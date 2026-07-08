"""Paper portfolio account for measurable stock-selection experiments."""
from __future__ import annotations

import json
import math
from dataclasses import dataclass, field, replace
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Callable

from .models import Quote, StockSnapshot


PORTFOLIO_DIR = Path(".finance_agent")
DEFAULT_ACCOUNT = "default"


@dataclass
class Holding:
    symbol: str
    shares: float
    avg_cost: float
    last_price: float
    market_value: float
    weight: float
    thesis: str = ""


@dataclass
class PortfolioAccount:
    name: str
    initial_cash: float
    cash: float
    holdings: list[Holding] = field(default_factory=list)
    transactions: list[dict[str, Any]] = field(default_factory=list)
    history: list[dict[str, Any]] = field(default_factory=list)
    created_at: str = ""
    updated_at: str = ""


@dataclass
class CandidateScore:
    symbol: str
    score: float
    target_weight: float
    price: float | None
    source: str
    thesis: str
    warnings: list[str] = field(default_factory=list)


def account_path(name: str = DEFAULT_ACCOUNT, base_dir: Path | None = None) -> Path:
    clean = "".join(ch for ch in (name or DEFAULT_ACCOUNT) if ch.isalnum() or ch in {"-", "_"}) or DEFAULT_ACCOUNT
    return (base_dir or PORTFOLIO_DIR) / f"portfolio_{clean}.json"


def create_account(
    *,
    initial_cash: float = 1_000_000.0,
    name: str = DEFAULT_ACCOUNT,
    overwrite: bool = False,
    base_dir: Path | None = None,
) -> PortfolioAccount:
    path = account_path(name, base_dir)
    if path.exists() and not overwrite:
        return load_account(name, base_dir)
    now = _iso_now()
    account = PortfolioAccount(
        name=name,
        initial_cash=max(float(initial_cash), 0.0),
        cash=max(float(initial_cash), 0.0),
        created_at=now,
        updated_at=now,
    )
    save_account(account, base_dir)
    return account


def load_account(name: str = DEFAULT_ACCOUNT, base_dir: Path | None = None) -> PortfolioAccount:
    path = account_path(name, base_dir)
    if not path.exists():
        return create_account(name=name, base_dir=base_dir)
    data = json.loads(path.read_text(encoding="utf-8"))
    holdings = [Holding(**row) for row in data.get("holdings", [])]
    return PortfolioAccount(
        name=str(data.get("name") or name),
        initial_cash=float(data.get("initial_cash") or 0),
        cash=float(data.get("cash") or 0),
        holdings=holdings,
        transactions=list(data.get("transactions", [])),
        history=list(data.get("history", [])),
        created_at=str(data.get("created_at") or ""),
        updated_at=str(data.get("updated_at") or ""),
    )


def save_account(account: PortfolioAccount, base_dir: Path | None = None) -> Path:
    path = account_path(account.name, base_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "name": account.name,
        "initial_cash": account.initial_cash,
        "cash": account.cash,
        "holdings": [holding.__dict__ for holding in account.holdings],
        "transactions": account.transactions[-1000:],
        "history": account.history[-500:],
        "created_at": account.created_at,
        "updated_at": account.updated_at,
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def score_candidates(snapshots: list[StockSnapshot]) -> list[CandidateScore]:
    scored = [_score_snapshot(snapshot) for snapshot in snapshots]
    return sorted(scored, key=lambda item: item.score, reverse=True)


def construct_portfolio(
    snapshots: list[StockSnapshot],
    *,
    initial_cash: float = 1_000_000.0,
    max_positions: int = 5,
    max_weight: float = 0.30,
    min_score: float = 35.0,
    cash_reserve: float = 0.10,
    name: str = DEFAULT_ACCOUNT,
    overwrite: bool = True,
    base_dir: Path | None = None,
) -> tuple[PortfolioAccount, list[CandidateScore]]:
    scores = score_candidates(snapshots)
    account = create_account(initial_cash=initial_cash, name=name, overwrite=overwrite, base_dir=base_dir)
    selected = [
        score for score in scores
        if score.score >= min_score and score.price is not None and score.price > 0
    ][:max(max_positions, 1)]

    investable = account.initial_cash * (1 - _clamp(cash_reserve, 0.0, 0.8))
    weights = _target_weights(selected, max_weight)
    holdings: list[Holding] = []
    used_cash = 0.0
    transactions: list[dict[str, Any]] = []
    for score, weight in zip(selected, weights, strict=False):
        assert score.price is not None
        market_value = investable * weight
        shares = math.floor(market_value / score.price)
        if shares <= 0:
            continue
        actual_value = shares * score.price
        used_cash += actual_value
        holdings.append(Holding(
            symbol=score.symbol,
            shares=float(shares),
            avg_cost=float(score.price),
            last_price=float(score.price),
            market_value=float(actual_value),
            weight=0.0,
            thesis=score.thesis,
        ))
        transactions.append(_transaction(
            action="BUY",
            symbol=score.symbol,
            shares=float(shares),
            price=float(score.price),
            reason=f"initial build: {score.thesis}",
        ))

    account.cash = account.initial_cash - used_cash
    account.holdings = _normalize_holding_weights(holdings, account.cash)
    account.transactions = transactions
    account.updated_at = _iso_now()
    account.history.append(_history_row(account, event="construct", notes="initial paper portfolio"))
    save_account(account, base_dir)
    return account, scores


def rebalance_portfolio(
    snapshots: list[StockSnapshot],
    *,
    name: str = DEFAULT_ACCOUNT,
    max_positions: int = 5,
    max_weight: float = 0.30,
    min_score: float = 35.0,
    cash_reserve: float = 0.10,
    base_dir: Path | None = None,
) -> tuple[PortfolioAccount, list[CandidateScore]]:
    account = load_account(name, base_dir)
    latest_prices = {
        snapshot.symbol: snapshot.quote.price
        for snapshot in snapshots
        if snapshot.quote.price is not None and snapshot.quote.price > 0
    }
    for holding in account.holdings:
        latest_price = latest_prices.get(holding.symbol)
        if latest_price is not None:
            holding.last_price = float(latest_price)
            holding.market_value = holding.shares * float(latest_price)
    account.holdings = _normalize_holding_weights(account.holdings, account.cash)
    old_holdings = {holding.symbol: replace(holding) for holding in account.holdings}
    total = portfolio_value(account)
    scores = score_candidates(snapshots)
    selected = [
        score for score in scores
        if score.score >= min_score and score.price is not None and score.price > 0
    ][:max(max_positions, 1)]
    investable = total * (1 - _clamp(cash_reserve, 0.0, 0.8))
    weights = _target_weights(selected, max_weight)
    holdings: list[Holding] = []
    used_cash = 0.0
    for score, weight in zip(selected, weights, strict=False):
        assert score.price is not None
        market_value = investable * weight
        shares = math.floor(market_value / score.price)
        if shares <= 0:
            continue
        actual_value = shares * score.price
        used_cash += actual_value
        holdings.append(Holding(
            symbol=score.symbol,
            shares=float(shares),
            avg_cost=_rebalance_avg_cost(old_holdings.get(score.symbol), float(shares), float(score.price)),
            last_price=float(score.price),
            market_value=float(actual_value),
            weight=0.0,
            thesis=score.thesis,
        ))
    _record_rebalance_transactions(account, old_holdings, holdings)
    account.cash = total - used_cash
    account.holdings = _normalize_holding_weights(holdings, account.cash)
    account.updated_at = _iso_now()
    account.history.append(_history_row(account, event="rebalance", notes="paper portfolio rebalance"))
    save_account(account, base_dir)
    return account, scores


def mark_to_market(
    *,
    get_quote: Callable[[str], Quote],
    name: str = DEFAULT_ACCOUNT,
    base_dir: Path | None = None,
    notes: str = "",
) -> PortfolioAccount:
    account = load_account(name, base_dir)
    prices: dict[str, float] = {}
    for holding in account.holdings:
        quote = get_quote(holding.symbol)
        if quote.price is not None and quote.price > 0:
            prices[holding.symbol] = float(quote.price)
            holding.last_price = float(quote.price)
            holding.market_value = holding.shares * float(quote.price)
    account.holdings = _normalize_holding_weights(account.holdings, account.cash)
    account.updated_at = _iso_now()
    account.history.append(_history_row(account, event="mark", notes=notes or "mark to market", prices=prices))
    save_account(account, base_dir)
    return account


def sell_holding(
    symbol: str,
    *,
    shares: float | str = "all",
    price: float | None = None,
    reason: str = "manual sell",
    name: str = DEFAULT_ACCOUNT,
    base_dir: Path | None = None,
) -> PortfolioAccount:
    account = load_account(name, base_dir)
    target = symbol.upper()
    sell_all = str(shares).lower() == "all"
    requested_shares: float | None = None
    if not sell_all:
        try:
            requested_shares = float(shares)
        except (TypeError, ValueError):
            account.history.append(_history_row(account, event="sell_failed", notes=f"invalid shares: {shares}"))
            save_account(account, base_dir)
            return account
        if requested_shares <= 0:
            account.history.append(_history_row(account, event="sell_failed", notes=f"invalid shares: {shares}"))
            save_account(account, base_dir)
            return account
    remaining: list[Holding] = []
    sold = False
    for holding in account.holdings:
        if holding.symbol.upper() != target:
            remaining.append(holding)
            continue
        sell_shares = holding.shares if sell_all else min(requested_shares or 0.0, holding.shares)
        if sell_shares <= 0:
            remaining.append(holding)
            continue
        sell_price = float(price if price is not None and price > 0 else holding.last_price)
        if sell_price <= 0:
            remaining.append(holding)
            continue
        proceeds = sell_shares * sell_price
        realized = (sell_price - holding.avg_cost) * sell_shares
        account.cash += proceeds
        account.transactions.append(_transaction(
            action="SELL",
            symbol=holding.symbol,
            shares=float(sell_shares),
            price=sell_price,
            reason=reason,
            realized_pnl=realized,
        ))
        sold = True
        left = holding.shares - sell_shares
        if left > 0:
            holding.shares = left
            holding.last_price = sell_price
            holding.market_value = left * sell_price
            remaining.append(holding)
    if not sold:
        account.history.append(_history_row(account, event="sell_failed", notes=f"{target} not held"))
    else:
        account.holdings = _normalize_holding_weights(remaining, account.cash)
        account.updated_at = _iso_now()
        account.history.append(_history_row(account, event="sell", notes=reason))
    save_account(account, base_dir)
    return account


def portfolio_value(account: PortfolioAccount, prices: dict[str, float] | None = None) -> float:
    prices = prices or {}
    holding_value = 0.0
    for holding in account.holdings:
        price = prices.get(holding.symbol, holding.last_price)
        holding_value += holding.shares * price
    return account.cash + holding_value


def render_transactions(account: PortfolioAccount, limit: int = 30) -> str:
    if not account.transactions:
        return "交易流水：暂无。"
    lines = ["# 纸面交易流水", ""]
    lines.append("| 时间 | 动作 | 标的 | 股数 | 价格 | 金额 | 实现盈亏 | 理由 |")
    lines.append("|---|---|---|---:|---:|---:|---:|---|")
    for item in account.transactions[-max(limit, 1):]:
        lines.append(
            f"| {item.get('as_of', '')} | {item.get('action', '')} | {item.get('symbol', '')} | "
            f"{float(item.get('shares') or 0):,.0f} | {_money(item.get('price'))} | "
            f"{_money(item.get('amount'))} | {_money(item.get('realized_pnl'))} | "
            f"{str(item.get('reason') or '')[:90]} |"
        )
    return "\n".join(lines)


def render_account(account: PortfolioAccount) -> str:
    total = portfolio_value(account)
    pnl = total - account.initial_cash
    pnl_pct = (pnl / account.initial_cash * 100) if account.initial_cash else 0.0
    lines = [
        f"# 模拟投资账户：{account.name}",
        "",
        f"- 初始资金: {_money(account.initial_cash)}",
        f"- 当前净值: {_money(total)}",
        f"- 现金: {_money(account.cash)}",
        f"- 累计收益: {_money(pnl)} ({pnl_pct:.2f}%)",
        f"- 更新时间: {account.updated_at or '未知'}",
        "",
        "## 持仓",
    ]
    if not account.holdings:
        lines.append("- 暂无持仓。")
    else:
        lines.append("| 标的 | 股数 | 成本 | 最新价 | 市值 | 权重 | 理由 |")
        lines.append("|---|---:|---:|---:|---:|---:|---|")
        for holding in account.holdings:
            lines.append(
                f"| {holding.symbol} | {holding.shares:,.0f} | {_money(holding.avg_cost)} | "
                f"{_money(holding.last_price)} | {_money(holding.market_value)} | {holding.weight * 100:.2f}% | "
                f"{holding.thesis[:80]} |"
            )
    lines.extend([
        "",
        "## 交易统计",
        f"- 交易笔数: {len(account.transactions)}",
        f"- 已实现盈亏: {_money(_realized_pnl(account))}",
        "",
        "## 最近记录",
    ])
    for row in account.history[-5:]:
        lines.append(
            f"- {row.get('as_of')} {row.get('event')}: "
            f"净值 {_money(row.get('total_value'))}, 收益 {float(row.get('return_pct') or 0):.2f}%"
        )
    lines.append("")
    lines.append("说明：这是纸面组合，用于验证研究和选股框架，不会执行真实交易。")
    return "\n".join(lines)


def render_recommendation(account: PortfolioAccount, scores: list[CandidateScore]) -> str:
    lines = [render_account(account), "", "## 候选评分"]
    lines.append("| 排名 | 标的 | 分数 | 目标权重 | 价格 | 数据源 | 关键理由 | 风险提示 |")
    lines.append("|---:|---|---:|---:|---:|---|---|---|")
    for index, score in enumerate(scores, start=1):
        lines.append(
            f"| {index} | {score.symbol} | {score.score:.1f} | {score.target_weight * 100:.1f}% | "
            f"{_money(score.price)} | {score.source or '未知'} | {score.thesis} | "
            f"{'; '.join(score.warnings) or '无'} |"
        )
    lines.extend([
        "",
        "## 风控规则",
        "- 单只股票目标权重受上限约束，默认不超过 30%。",
        "- 默认保留现金，避免满仓和数据误差导致的过度集中。",
        "- SAMPLE_FALLBACK 或 UNAVAILABLE 数据会显著降权；真实投资前必须核验数据源。",
        "- 输出是模拟组合和研究实验，不构成投资建议，也不连接真实交易账户。",
    ])
    return "\n".join(lines)


def _score_snapshot(snapshot: StockSnapshot) -> CandidateScore:
    q = snapshot.quote
    f = snapshot.financials
    i = snapshot.indicators
    score = 50.0
    thesis: list[str] = []
    warnings: list[str] = []

    ret_3m = _num(i.get("return_3m_pct"))
    ret_1y = _num(i.get("return_1y_pct"))
    vol = _num(i.get("annualized_volatility_pct"))
    pe = _num(f.pe_ratio or q.pe_ratio)
    roe = _ratio_pct(f.return_on_equity)
    margin = _ratio_pct(f.profit_margin)

    if ret_3m is not None:
        delta = _clamp(ret_3m / 2.0, -12.0, 12.0)
        score += delta
        thesis.append(f"3月收益{ret_3m:.1f}%")
    if ret_1y is not None:
        delta = _clamp(ret_1y / 6.0, -8.0, 8.0)
        score += delta
        thesis.append(f"1年收益{ret_1y:.1f}%")
    if vol is not None:
        if vol < 25:
            score += 6
            thesis.append("波动率较低")
        elif vol > 55:
            score -= 12
            warnings.append(f"年化波动率偏高 {vol:.1f}%")
    if pe is not None:
        if 0 < pe < 25:
            score += 8
            thesis.append(f"PE {pe:.1f} 不高")
        elif pe > 60:
            score -= 12
            warnings.append(f"PE 偏高 {pe:.1f}")
    if f.free_cash_flow is not None:
        if f.free_cash_flow > 0:
            score += 8
            thesis.append("自由现金流为正")
        else:
            score -= 10
            warnings.append("自由现金流为负")
    if margin is not None:
        if margin > 20:
            score += 6
            thesis.append(f"利润率{margin:.1f}%")
        elif margin < 5:
            score -= 5
            warnings.append(f"利润率偏低 {margin:.1f}%")
    if roe is not None:
        if roe > 15:
            score += 6
            thesis.append(f"ROE {roe:.1f}%")
        elif roe < 5:
            score -= 5
            warnings.append(f"ROE 偏低 {roe:.1f}%")

    if q.source in {"SAMPLE_FALLBACK", "UNAVAILABLE", ""}:
        score -= 35
        warnings.append(f"行情数据源低置信: {q.source or '未知'}")
    if f.source in {"SAMPLE_FALLBACK", "UNAVAILABLE", ""}:
        score -= 25
        warnings.append(f"基本面数据源低置信: {f.source or '未知'}")
    if q.price is None or q.price <= 0:
        score -= 50
        warnings.append("缺少有效价格，不能建仓")

    score = _clamp(score, 0.0, 100.0)
    return CandidateScore(
        symbol=snapshot.symbol,
        score=score,
        target_weight=0.0,
        price=q.price,
        source=f"{q.source}/{f.source}",
        thesis="；".join(thesis[:5]) or "正面证据不足",
        warnings=warnings,
    )


def _target_weights(scores: list[CandidateScore], max_weight: float) -> list[float]:
    if not scores:
        return []
    raw = [max(score.score - 30.0, 1.0) for score in scores]
    total = sum(raw)
    weights = [min(value / total, max_weight) for value in raw]
    remaining = 1.0 - sum(weights)
    uncapped = [idx for idx, weight in enumerate(weights) if weight < max_weight]
    while remaining > 0.0001 and uncapped:
        add = remaining / len(uncapped)
        next_uncapped = []
        for idx in uncapped:
            room = max_weight - weights[idx]
            actual = min(add, room)
            weights[idx] += actual
            remaining -= actual
            if weights[idx] < max_weight - 0.0001:
                next_uncapped.append(idx)
        if len(next_uncapped) == len(uncapped):
            break
        uncapped = next_uncapped
    for score, weight in zip(scores, weights, strict=False):
        score.target_weight = weight
    return weights


def _normalize_holding_weights(holdings: list[Holding], cash: float) -> list[Holding]:
    total = cash + sum(holding.market_value for holding in holdings)
    if total <= 0:
        return holdings
    for holding in holdings:
        holding.weight = holding.market_value / total
    return holdings


def _record_rebalance_transactions(
    account: PortfolioAccount,
    old_holdings: dict[str, Holding],
    new_holdings: list[Holding],
) -> None:
    new_by_symbol = {holding.symbol: holding for holding in new_holdings}
    for symbol, old in old_holdings.items():
        new = new_by_symbol.get(symbol)
        new_shares = new.shares if new else 0.0
        if old.shares > new_shares:
            sold = old.shares - new_shares
            price = new.last_price if new else old.last_price
            account.transactions.append(_transaction(
                action="SELL",
                symbol=symbol,
                shares=sold,
                price=price,
                reason="rebalance reduce/exit",
                realized_pnl=(price - old.avg_cost) * sold,
            ))
    for new in new_holdings:
        old = old_holdings.get(new.symbol)
        old_shares = old.shares if old else 0.0
        if new.shares > old_shares:
            bought = new.shares - old_shares
            account.transactions.append(_transaction(
                action="BUY",
                symbol=new.symbol,
                shares=bought,
                price=new.last_price,
                reason=f"rebalance add: {new.thesis}",
            ))


def _rebalance_avg_cost(old: Holding | None, new_shares: float, trade_price: float) -> float:
    if old is None or old.shares <= 0 or new_shares <= 0:
        return trade_price
    if new_shares <= old.shares:
        return old.avg_cost
    bought = new_shares - old.shares
    return ((old.avg_cost * old.shares) + (trade_price * bought)) / new_shares


def _transaction(
    *,
    action: str,
    symbol: str,
    shares: float,
    price: float,
    reason: str,
    realized_pnl: float = 0.0,
) -> dict[str, Any]:
    return {
        "as_of": _iso_now(),
        "action": action,
        "symbol": symbol,
        "shares": shares,
        "price": price,
        "amount": shares * price,
        "realized_pnl": realized_pnl,
        "reason": reason,
    }


def _realized_pnl(account: PortfolioAccount) -> float:
    return sum(float(item.get("realized_pnl") or 0) for item in account.transactions)


def _history_row(
    account: PortfolioAccount,
    *,
    event: str,
    notes: str = "",
    prices: dict[str, float] | None = None,
) -> dict[str, Any]:
    total = portfolio_value(account)
    ret = (total - account.initial_cash) / account.initial_cash * 100 if account.initial_cash else 0.0
    return {
        "as_of": _iso_now(),
        "event": event,
        "total_value": total,
        "cash": account.cash,
        "return_pct": ret,
        "positions": [
            {
                "symbol": holding.symbol,
                "shares": holding.shares,
                "price": holding.last_price,
                "market_value": holding.market_value,
                "weight": holding.weight,
            }
            for holding in account.holdings
        ],
        "prices": prices or {},
        "notes": notes,
    }


def _num(value: Any) -> float | None:
    if value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if math.isnan(number):
        return None
    return number


def _ratio_pct(value: Any) -> float | None:
    number = _num(value)
    if number is None:
        return None
    if abs(number) <= 2:
        return number * 100
    return number


def _clamp(value: float, low: float, high: float) -> float:
    return min(max(value, low), high)


def _money(value: Any) -> str:
    if value is None:
        return "NA"
    try:
        return f"{float(value):,.2f}"
    except (TypeError, ValueError):
        return str(value)


def _iso_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
