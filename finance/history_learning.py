"""Historical pattern learning for forecast calibration and skill updates."""
from __future__ import annotations

import json
import math
from dataclasses import dataclass, field
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any

from .indicators import calculate_indicators
from .models import Candle


LEARNING_DIR = Path(".finance_agent")
LEARNING_PATH = LEARNING_DIR / "history_learning.jsonl"
SKILL_PATH = Path("skills") / "finance-history-learning" / "SKILL.md"


@dataclass
class FeatureStats:
    feature: str
    bucket: str
    count: int
    win_rate: float
    avg_forward_return_pct: float


@dataclass
class LearnedRule:
    symbol: str
    horizon_days: int
    sample_count: int
    current_features: dict[str, str]
    matched_stats: list[FeatureStats]
    predicted_direction: str
    confidence: float
    expected_return_pct: float
    learned_at: str
    notes: list[str] = field(default_factory=list)


def learn_from_history(
    symbol: str,
    candles: list[Candle],
    *,
    horizon_days: int = 20,
    min_samples: int = 8,
) -> LearnedRule:
    clean = [candle for candle in candles if candle.close is not None]
    rows = _feature_rows(clean, horizon_days)
    current_features = _current_features(clean)
    matched: list[FeatureStats] = []
    for feature, bucket in current_features.items():
        returns = [
            row["forward_return_pct"]
            for row in rows
            if row.get(feature) == bucket and row.get("forward_return_pct") is not None
        ]
        if len(returns) >= min_samples:
            matched.append(_stats(feature, bucket, returns))

    if matched:
        expected = sum(item.avg_forward_return_pct * item.count for item in matched) / sum(item.count for item in matched)
        wins = sum(item.win_rate * item.count for item in matched) / sum(item.count for item in matched)
    else:
        forward_returns = [row["forward_return_pct"] for row in rows if row.get("forward_return_pct") is not None]
        expected = sum(forward_returns) / len(forward_returns) if forward_returns else 0.0
        wins = sum(1 for value in forward_returns if value > 0) / len(forward_returns) if forward_returns else 0.5

    if expected > 1:
        direction = "up"
    elif expected < -1:
        direction = "down"
    else:
        direction = "neutral"
    confidence = _confidence(expected, wins, len(rows), len(matched))
    notes = []
    if len(rows) < 30:
        notes.append("历史样本较少，置信度应下调。")
    if not matched:
        notes.append("当前特征没有足够历史匹配，使用全样本基准。")

    return LearnedRule(
        symbol=symbol,
        horizon_days=max(int(horizon_days), 1),
        sample_count=len(rows),
        current_features=current_features,
        matched_stats=matched,
        predicted_direction=direction,
        confidence=confidence,
        expected_return_pct=expected,
        learned_at=_iso_now(),
        notes=notes,
    )


def save_learning(rule: LearnedRule, path: Path | None = None) -> Path:
    path = path or LEARNING_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "symbol": rule.symbol,
        "horizon_days": rule.horizon_days,
        "sample_count": rule.sample_count,
        "current_features": rule.current_features,
        "matched_stats": [item.__dict__ for item in rule.matched_stats],
        "predicted_direction": rule.predicted_direction,
        "confidence": rule.confidence,
        "expected_return_pct": rule.expected_return_pct,
        "learned_at": rule.learned_at,
        "notes": rule.notes,
    }
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n")
    return path


def load_learning(path: Path | None = None) -> list[dict[str, Any]]:
    path = path or LEARNING_PATH
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return rows


def render_learning(rule: LearnedRule) -> str:
    lines = [
        f"# 历史学习预测：{rule.symbol}",
        "",
        f"- 学习时间: {rule.learned_at}",
        f"- 预测周期: {rule.horizon_days} 天",
        f"- 历史样本: {rule.sample_count}",
        f"- 当前方向: {rule.predicted_direction}",
        f"- 置信度: {rule.confidence:.2f}",
        f"- 期望收益: {rule.expected_return_pct:.2f}%",
        "",
        "## 当前特征",
    ]
    for feature, bucket in rule.current_features.items():
        lines.append(f"- {feature}: {bucket}")
    lines.extend(["", "## 匹配历史表现"])
    if rule.matched_stats:
        lines.append("| 特征 | 桶 | 样本 | 胜率 | 未来收益均值 |")
        lines.append("|---|---|---:|---:|---:|")
        for item in rule.matched_stats:
            lines.append(
                f"| {item.feature} | {item.bucket} | {item.count} | "
                f"{item.win_rate * 100:.1f}% | {item.avg_forward_return_pct:.2f}% |"
            )
    else:
        lines.append("- 当前特征匹配样本不足，使用全样本基准。")
    if rule.notes:
        lines.extend(["", "## 注意"])
        lines.extend(f"- {note}" for note in rule.notes)
    lines.append("")
    lines.append("说明：这是历史模式学习结果，不构成投资建议；必须用未来真实价格继续评分。")
    return "\n".join(lines)


def update_history_learning_skill(rule: LearnedRule, path: Path | None = None) -> Path:
    path = path or SKILL_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    content = _skill_content(rule)
    path.write_text(content, encoding="utf-8")
    return path


def _feature_rows(candles: list[Candle], horizon_days: int) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    closes = [float(candle.close) for candle in candles if candle.close is not None]
    for idx in range(60, max(len(closes) - horizon_days, 60)):
        current = closes[: idx + 1]
        now = current[-1]
        future = closes[idx + horizon_days]
        features = _features_from_closes(current)
        features["forward_return_pct"] = (future - now) / now * 100 if now else None
        rows.append(features)
    return rows


def _current_features(candles: list[Candle]) -> dict[str, str]:
    closes = [float(candle.close) for candle in candles if candle.close is not None]
    return _features_from_closes(closes)


def _features_from_closes(closes: list[float]) -> dict[str, str]:
    if len(closes) < 60:
        return {"data": "insufficient"}
    start = date(2000, 1, 1)
    indicators = calculate_indicators([
        Candle(date=(start + timedelta(days=index)).isoformat(), open=None, high=None, low=None, close=close)
        for index, close in enumerate(closes)
    ])
    price = closes[-1]
    ma20 = indicators.get("ma20")
    ma60 = indicators.get("ma60")
    ret_20 = _return_pct(closes, 20)
    ret_60 = _return_pct(closes, 60)
    vol = indicators.get("annualized_volatility_pct")
    rsi = indicators.get("rsi14")
    return {
        "trend_20d": _bucket(ret_20, (-8, -2, 2, 8), ("strong_down", "down", "flat", "up", "strong_up")),
        "trend_60d": _bucket(ret_60, (-15, -5, 5, 15), ("strong_down", "down", "flat", "up", "strong_up")),
        "price_vs_ma20": "above" if ma20 is not None and price >= ma20 else "below",
        "price_vs_ma60": "above" if ma60 is not None and price >= ma60 else "below",
        "volatility": _bucket(vol, (20, 40, 60), ("low", "normal", "high", "extreme")),
        "rsi": _bucket(rsi, (30, 45, 55, 70), ("oversold", "weak", "neutral", "strong", "overbought")),
    }


def _return_pct(closes: list[float], window: int) -> float | None:
    if len(closes) <= window:
        return None
    base = closes[-window - 1]
    if base == 0:
        return None
    return (closes[-1] - base) / base * 100


def _bucket(value: Any, cuts: tuple[float, ...], labels: tuple[str, ...]) -> str:
    if value is None:
        return "unknown"
    try:
        number = float(value)
    except (TypeError, ValueError):
        return "unknown"
    if math.isnan(number):
        return "unknown"
    for cut, label in zip(cuts, labels, strict=False):
        if number < cut:
            return label
    return labels[-1]


def _stats(feature: str, bucket: str, returns: list[float]) -> FeatureStats:
    wins = sum(1 for value in returns if value > 0)
    return FeatureStats(
        feature=feature,
        bucket=bucket,
        count=len(returns),
        win_rate=wins / len(returns),
        avg_forward_return_pct=sum(returns) / len(returns),
    )


def _confidence(expected_return: float, win_rate: float, sample_count: int, matched_count: int) -> float:
    edge = min(abs(expected_return) / 8.0, 1.0)
    win_edge = abs(win_rate - 0.5) * 2
    sample = min(sample_count / 180.0, 1.0)
    matched = min(matched_count / 4.0, 1.0)
    return min(max(0.25 + 0.30 * edge + 0.20 * win_edge + 0.15 * sample + 0.10 * matched, 0.0), 0.95)


def _skill_content(rule: LearnedRule) -> str:
    stats = "\n".join(
        f"- `{item.feature}={item.bucket}`: n={item.count}, win={item.win_rate * 100:.1f}%, "
        f"avg_forward={item.avg_forward_return_pct:.2f}%"
        for item in rule.matched_stats[:8]
    ) or "- 当前没有足够匹配特征；先用全样本基准，不要高置信预测。"
    features = "\n".join(f"- `{key}`: `{value}`" for key, value in rule.current_features.items())
    notes = "\n".join(f"- {note}" for note in rule.notes) or "- 每次预测后必须写入 prediction ledger，并在到期后评分。"
    return f"""---
name: finance-history-learning
description: 当用户要求根据历史行情学习预测规则、用历史数据校准股票方向/仓位、或把预测经验沉淀为 Skill 时使用。
---

# Finance History Learning

## 适用场景

用于从历史 K 线中学习可解释的方向预测规则，并把结果用于后续股票研究、纸面组合和预测评分。

## 最新学习结果

- 标的: `{rule.symbol}`
- 学习时间: `{rule.learned_at}`
- 预测周期: `{rule.horizon_days}` 天
- 历史样本: `{rule.sample_count}`
- 当前方向: `{rule.predicted_direction}`
- 置信度: `{rule.confidence:.2f}`
- 期望收益: `{rule.expected_return_pct:.2f}%`

## 当前特征

{features}

## 历史匹配表现

{stats}

## 使用规则

1. 先核验行情来源和时间，不能用 `SAMPLE_FALLBACK` 当真实学习数据。
2. 预测必须输出方向、周期、置信度、历史样本数和主要匹配特征。
3. 只把学习结果作为研究假设；不得承诺收益或输出确定性买卖指令。
4. 给出预测后调用 `prediction_record` 或 `/predict record` 保存 baseline。
5. 到期后调用 `prediction_evaluate` 和 `prediction_learn` 做事后评分。
6. 若样本数低于 60 或匹配特征不足，置信度不得高于 0.5。

## 注意

{notes}
"""


def _iso_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
