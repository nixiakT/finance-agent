"""Research quality gates inspired by value-investing workflows."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .models import Financials, Quote, StockSnapshot


@dataclass
class QualityGate:
    information_grade: str
    information_reason: str
    passed: list[str]
    warnings: list[str]
    veto_signals: list[str]
    next_checks: list[str]


def evaluate_quality_gate(snapshot: StockSnapshot) -> QualityGate:
    quote = snapshot.quote
    financials = snapshot.financials
    passed: list[str] = []
    warnings: list[str] = []
    veto_signals: list[str] = []
    next_checks: list[str] = []

    if quote.price is not None and quote.as_of:
        passed.append("行情价格和时间戳可用。")
    else:
        warnings.append("缺少可用行情价格或行情时间戳。")

    if quote.is_realtime:
        passed.append("行情时间处于实时/准实时窗口。")
    else:
        warnings.append("行情不是实时/准实时，需确认是否延迟或停牌。")

    if len(snapshot.history) >= 60:
        passed.append(f"历史价格样本充足（{len(snapshot.history)} 个数据点）。")
    elif snapshot.history:
        warnings.append(f"历史价格样本偏少（{len(snapshot.history)} 个数据点）。")
    else:
        warnings.append("缺少历史价格，技术面和回测不可用。")

    real_financial_fields = _financial_field_count(financials)
    if _low_confidence_source(financials.source):
        warnings.append("基本面数据源不可用或为样例 fallback。")
    elif real_financial_fields >= 5:
        passed.append(f"基本面字段较完整（{real_financial_fields} 个关键字段）。")
    elif real_financial_fields > 0:
        warnings.append(f"基本面字段不足（{real_financial_fields} 个关键字段）。")
    else:
        warnings.append("缺少关键基本面字段。")

    if snapshot.news:
        passed.append(f"已有相关新闻/事件 {len(snapshot.news)} 条。")
    else:
        warnings.append("缺少相关新闻或公告核验。")

    pe = financials.pe_ratio or quote.pe_ratio
    if financials.free_cash_flow is not None and financials.free_cash_flow < 0:
        veto_signals.append("自由现金流为负，需要解释资本开支、营运资本或融资依赖。")
    if financials.debt_to_equity is not None and financials.debt_to_equity > 150:
        veto_signals.append("杠杆水平偏高，需要核验利息覆盖和再融资风险。")
    if pe is not None and pe > 80:
        veto_signals.append("估值倍数很高，安全边际可能不足。")
    if _low_confidence_source(quote.source) or _low_confidence_source(financials.source):
        veto_signals.append("核心数据置信度不足，不能进入高置信度结论。")

    if financials.free_cash_flow is None:
        next_checks.append("补充最近年度/季度自由现金流，并核验是否长期为正。")
    if financials.return_on_equity is None:
        next_checks.append("补充 ROE 和过去 3-5 年趋势，判断资本效率。")
    if financials.debt_to_equity is None:
        next_checks.append("补充负债、现金和利息覆盖，检查资产负债表韧性。")
    if not snapshot.news:
        next_checks.append("用公开公告、财报或财经新闻源交叉验证近期事件。")
    if not next_checks:
        next_checks.append("继续核验管理层、竞争格局、行业周期和估值情景。")

    grade, reason = _information_grade(quote, financials, snapshot, real_financial_fields)
    return QualityGate(
        information_grade=grade,
        information_reason=reason,
        passed=passed,
        warnings=warnings,
        veto_signals=veto_signals,
        next_checks=next_checks,
    )


def render_quality_gate(snapshot: StockSnapshot) -> str:
    gate = evaluate_quality_gate(snapshot)
    lines = [
        f"- 信息丰富度: {gate.information_grade}（{gate.information_reason}）",
        "- 已通过检查:",
    ]
    lines.extend(f"  - {item}" for item in (gate.passed or ["暂无明确通过项。"]))
    lines.append("- 需要注意:")
    lines.extend(f"  - {item}" for item in (gate.warnings or ["暂无明显数据缺口。"]))
    lines.append("- 快速否决/重审信号:")
    lines.extend(f"  - {item}" for item in (gate.veto_signals or ["未触发硬性否决信号；仍需做商业模式和管理层验证。"]))
    lines.append("- 下一步核验:")
    lines.extend(f"  - {item}" for item in gate.next_checks)
    return "\n".join(lines)


def render_quality_screen(snapshot: StockSnapshot) -> str:
    gate = evaluate_quality_gate(snapshot)
    financials = snapshot.financials
    quote = snapshot.quote
    checks = [
        ("行情可信", "通过" if quote.price is not None and quote.as_of else "待补充", "价格和时间戳"),
        ("历史样本", "通过" if len(snapshot.history) >= 60 else "待补充", f"{len(snapshot.history)} 个数据点"),
        ("ROE", _pass_or_gap(financials.return_on_equity, 0.08), _format_pct(financials.return_on_equity)),
        ("自由现金流", _pass_positive(financials.free_cash_flow), _format_number(financials.free_cash_flow)),
        ("利润率", _pass_or_gap(financials.profit_margin, 0.05), _format_pct(financials.profit_margin)),
        ("杠杆", _pass_debt(financials.debt_to_equity), _format_number(financials.debt_to_equity)),
        ("新闻/公告", "通过" if snapshot.news else "待补充", f"{len(snapshot.news)} 条"),
    ]
    lines = [
        f"# 研究质量初筛：{snapshot.symbol}",
        "",
        f"- 抓取时间: {snapshot.fetched_at}",
        f"- 信息丰富度: {gate.information_grade}（{gate.information_reason}）",
        "",
        "| 检查项 | 结果 | 证据 |",
        "|---|---|---|",
    ]
    lines.extend(f"| {label} | {result} | {evidence} |" for label, result, evidence in checks)
    lines.extend([
        "",
        "## 快速否决/重审信号",
        *(f"- {item}" for item in (gate.veto_signals or ["未触发硬性否决信号；但通过初筛不等于值得买。"])),
        "",
        "## 数据缺口",
        *(f"- {item}" for item in (gate.warnings or ["暂无明显数据缺口。"])),
        "",
        "## 下一步",
        *(f"- {item}" for item in gate.next_checks),
        "",
        "边界：这是去劣和质量门禁，不是买入/卖出建议。",
    ])
    return "\n".join(lines)


def _information_grade(
    quote: Quote,
    financials: Financials,
    snapshot: StockSnapshot,
    financial_field_count: int,
) -> tuple[str, str]:
    if _low_confidence_source(quote.source) or _low_confidence_source(financials.source):
        return "C", "核心行情或基本面不可用/样例化，只能做低置信度整理"
    if quote.price is not None and len(snapshot.history) >= 120 and financial_field_count >= 5 and snapshot.news:
        return "A", "行情、历史、基本面和新闻均较完整"
    if quote.price is not None and len(snapshot.history) >= 40 and financial_field_count >= 2:
        return "B", "关键数据可用，但仍有字段或事件核验缺口"
    return "C", "数据窗口不足，需要补充一手来源"


def _financial_field_count(financials: Financials) -> int:
    fields: list[Any] = [
        financials.market_cap,
        financials.pe_ratio,
        financials.forward_pe,
        financials.eps,
        financials.revenue,
        financials.gross_profit,
        financials.net_income,
        financials.free_cash_flow,
        financials.debt_to_equity,
        financials.return_on_equity,
        financials.profit_margin,
    ]
    return sum(value is not None for value in fields)


def _low_confidence_source(source: str) -> bool:
    return source in {"", "UNAVAILABLE", "SAMPLE_FALLBACK"}


def _pass_or_gap(value: float | None, threshold: float) -> str:
    if value is None:
        return "待补充"
    return "通过" if value >= threshold else "重审"


def _pass_positive(value: float | None) -> str:
    if value is None:
        return "待补充"
    return "通过" if value > 0 else "重审"


def _pass_debt(value: float | None) -> str:
    if value is None:
        return "待补充"
    return "通过" if value <= 150 else "重审"


def _format_pct(value: float | None) -> str:
    if value is None:
        return "缺失"
    number = value * 100 if abs(value) <= 2 else value
    return f"{number:.2f}%"


def _format_number(value: float | None) -> str:
    if value is None:
        return "缺失"
    if abs(value) >= 1_000_000_000:
        return f"{value / 1_000_000_000:.2f}B"
    if abs(value) >= 1_000_000:
        return f"{value / 1_000_000:.2f}M"
    return f"{value:,.2f}"
