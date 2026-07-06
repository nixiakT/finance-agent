"""Deterministic multi-agent debate for stock selection research."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .models import StockSnapshot
from .report import _fmt_big, _fmt_number, _fmt_percent, _ratio_to_pct


@dataclass
class DebateRoleResult:
    role: str
    stance: str
    arguments: list[str]
    concerns: list[str]


def debate_stock(snapshot: StockSnapshot) -> str:
    roles = [
        _bull(snapshot),
        _bear(snapshot),
        _value(snapshot),
        _macro(snapshot),
        _risk(snapshot),
    ]
    return render_debate(snapshot, roles)


def debate_stocks(snapshots: list[StockSnapshot]) -> str:
    lines = ["# 多智能体辩论选股", ""]
    for snapshot in snapshots:
        lines.append(debate_stock(snapshot))
        lines.append("")
    lines.append("## 裁判横向结论")
    ranking = sorted(snapshots, key=_judge_score, reverse=True)
    for index, snapshot in enumerate(ranking, start=1):
        lines.append(f"{index}. {snapshot.symbol}: {_judge_summary(snapshot)}")
    lines.append("")
    lines.append("注意：排序只代表研究优先级，不代表买入建议。")
    return "\n".join(lines)


def render_debate(snapshot: StockSnapshot, roles: list[DebateRoleResult]) -> str:
    lines = [f"## {snapshot.symbol} 辩论", ""]
    for role in roles:
        lines.append(f"### {role.role}")
        lines.append(f"- 立场: {role.stance}")
        for arg in role.arguments:
            lines.append(f"- 支持理由: {arg}")
        for concern in role.concerns:
            lines.append(f"- 质疑点: {concern}")
        lines.append("")
    lines.append("### Judge Agent")
    lines.append(f"- 综合评分: {_judge_score(snapshot)}/10")
    lines.append(f"- 研究结论: {_judge_summary(snapshot)}")
    lines.append("- 下一步验证: 阅读最新财报/公告、拆解收入驱动、比较同业估值、做情景估值。")
    return "\n".join(lines).strip()


def _bull(snapshot: StockSnapshot) -> DebateRoleResult:
    q = snapshot.quote
    f = snapshot.financials
    i = snapshot.indicators
    args = []
    concerns = []
    if i.get("return_3m_pct") is not None and i["return_3m_pct"] > 0:
        args.append(f"近 3 月收益率为 {_fmt_percent(i['return_3m_pct'])}，价格动量偏正。")
    if f.profit_margin is not None and f.profit_margin > 0.15:
        args.append(f"利润率约 {_fmt_percent(_ratio_to_pct(f.profit_margin))}，盈利质量有跟踪价值。")
    if f.free_cash_flow is not None and f.free_cash_flow > 0:
        args.append(f"自由现金流为 {_fmt_big(f.free_cash_flow)}，支持长期价值讨论。")
    if not args:
        args.append("当前正面证据不足，多头需要更多业务和财务数据支持。")
    if q.source == "SAMPLE_FALLBACK" or f.source == "SAMPLE_FALLBACK":
        concerns.append("当前是样例数据，多头论证不能用于真实投资。")
    return DebateRoleResult("Bull Agent", "寻找上涨和继续跟踪理由", args, concerns)


def _bear(snapshot: StockSnapshot) -> DebateRoleResult:
    q = snapshot.quote
    f = snapshot.financials
    i = snapshot.indicators
    args = []
    concerns = []
    pe = f.pe_ratio or q.pe_ratio
    if pe is not None and pe > 40:
        args.append(f"PE 约 {_fmt_number(pe)}，估值对增长不及预期较敏感。")
    if i.get("annualized_volatility_pct") is not None and i["annualized_volatility_pct"] > 35:
        args.append(f"年化波动率约 {_fmt_percent(i['annualized_volatility_pct'])}，回撤风险需要重视。")
    if f.free_cash_flow is not None and f.free_cash_flow < 0:
        args.append("自由现金流为负，增长质量需要质疑。")
    if not args:
        args.append("未发现明显量化空头证据，但仍需查行业竞争和监管风险。")
    if snapshot.news:
        concerns.append("新闻事件需要逐条核验，避免只看标题做判断。")
    return DebateRoleResult("Bear Agent", "寻找风险和反例", args, concerns)


def _value(snapshot: StockSnapshot) -> DebateRoleResult:
    f = snapshot.financials
    args = []
    concerns = []
    if f.pe_ratio is not None:
        args.append(f"当前 PE: {_fmt_number(f.pe_ratio)}，需与增长、ROE、同业估值一起看。")
    if f.return_on_equity is not None:
        args.append(f"ROE: {_fmt_percent(_ratio_to_pct(f.return_on_equity))}，反映资本效率。")
    if f.free_cash_flow is not None:
        args.append(f"自由现金流: {_fmt_big(f.free_cash_flow)}。")
    if f.pe_ratio is None or f.return_on_equity is None:
        concerns.append("估值或 ROE 字段缺失，无法形成完整价值判断。")
    return DebateRoleResult("Value Agent", "评估估值、现金流和护城河线索", args or ["基本面数据不足。"], concerns)


def _macro(snapshot: StockSnapshot) -> DebateRoleResult:
    q = snapshot.quote
    i = snapshot.indicators
    args = [
        f"计价货币: {q.currency or '未知'}，需要结合利率、汇率和市场风险偏好。",
        f"近 1 年收益率: {_fmt_percent(i.get('return_1y_pct'))}，可作为周期位置的价格线索。",
    ]
    concerns = ["当前尚未接入利率、通胀和行业景气度数据，宏观判断只是框架提示。"]
    return DebateRoleResult("Macro Agent", "评估宏观周期和流动性影响", args, concerns)


def _risk(snapshot: StockSnapshot) -> DebateRoleResult:
    q = snapshot.quote
    f = snapshot.financials
    i = snapshot.indicators
    args = []
    concerns = []
    if i.get("annualized_volatility_pct") is not None:
        args.append(f"年化波动率: {_fmt_percent(i['annualized_volatility_pct'])}。")
    if f.debt_to_equity is not None:
        args.append(f"债务权益比: {_fmt_number(f.debt_to_equity)}。")
    if q.source == "SAMPLE_FALLBACK" or f.source == "SAMPLE_FALLBACK":
        concerns.append("样例数据风险最高，必须先替换为真实行情和财务数据。")
    if not snapshot.news:
        concerns.append("缺少新闻/公告，事件风险覆盖不足。")
    return DebateRoleResult("Risk Agent", "评估回撤、杠杆和数据风险", args or ["风险数据不足。"], concerns)


def _judge_score(snapshot: StockSnapshot) -> int:
    q = snapshot.quote
    f = snapshot.financials
    i = snapshot.indicators
    if q.source == "SAMPLE_FALLBACK" or f.source == "SAMPLE_FALLBACK":
        return 1
    score = 0
    pe = f.pe_ratio or q.pe_ratio
    if pe is not None and pe < 40:
        score += 2
    if f.free_cash_flow is not None and f.free_cash_flow > 0:
        score += 2
    if f.profit_margin is not None and f.profit_margin > 0.15:
        score += 2
    if i.get("return_3m_pct") is not None and i["return_3m_pct"] > 0:
        score += 1
    if i.get("annualized_volatility_pct") is not None and i["annualized_volatility_pct"] < 45:
        score += 1
    if snapshot.news:
        score += 1
    if q.is_realtime:
        score += 1
    return min(score, 10)


def _judge_summary(snapshot: StockSnapshot) -> str:
    score = _judge_score(snapshot)
    if snapshot.quote.source == "SAMPLE_FALLBACK" or snapshot.financials.source == "SAMPLE_FALLBACK":
        return "仅适合演示辩论流程；真实选股前必须替换数据源。"
    if score >= 7:
        return "值得进入深入研究池，但仍需财报、估值和竞争格局验证。"
    if score >= 4:
        return "可继续观察，当前多空证据较均衡。"
    return "暂不进入优先研究池，主要因为数据不足或风险信号偏多。"
