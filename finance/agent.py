"""High-level finance research facade used by tools and CLI."""
from __future__ import annotations

import re

from .backtest import backtest_moving_average_cross, format_backtest, parse_strategy
from .data import ProviderChain, export_history_csv
from .debate import debate_stocks
from .indicators import calculate_indicators, format_indicators
from .models import Financials, NewsItem, Quote, StockSnapshot, utc_now_iso
from .paper_portfolio import (
    construct_portfolio,
    load_account,
    mark_to_market,
    rebalance_portfolio,
    render_account,
    render_recommendation,
)
from .quality import render_quality_screen
from .report import render_comparison, render_daily_brief, render_stock_report
from .resolver import resolve_symbol, resolve_symbol_text
from .symbols import extract_symbols, normalize_symbol
from .web import web_search


class FinanceResearchAgent:
    def __init__(self, provider: ProviderChain | None = None):
        self.provider = provider or ProviderChain()

    def snapshot(self, symbol: str, period: str = "1y", news_limit: int = 5) -> StockSnapshot:
        normalized = _resolve_symbol(symbol)
        errors: list[str] = []
        try:
            quote = self.provider.get_quote(normalized)
        except Exception as exc:
            quote = Quote(
                symbol=normalized,
                source="UNAVAILABLE",
                as_of=utc_now_iso(),
                is_realtime=False,
                notes=[f"行情获取失败: {_compact_error(exc)}"],
            )
            errors.append(f"行情获取失败: {_compact_error(exc)}")

        try:
            history = self.provider.get_history(normalized, period, "1d")
        except Exception as exc:
            history = []
            errors.append(f"历史价格获取失败: {_compact_error(exc)}")

        try:
            financials = self.provider.get_financials(normalized)
        except Exception as exc:
            financials = Financials(
                symbol=normalized,
                source="UNAVAILABLE",
                as_of=utc_now_iso(),
                notes=[f"基本面获取失败: {_compact_error(exc)}"],
            )
            errors.append(f"基本面获取失败: {_compact_error(exc)}")

        try:
            news = self.provider.get_news(normalized, news_limit) if news_limit > 0 else []
        except Exception as exc:
            news = [
                NewsItem(
                    title=f"新闻获取失败: {_compact_error(exc)}",
                    source="UNAVAILABLE",
                    published_at=utc_now_iso(),
                )
            ]
            errors.append(f"新闻获取失败: {_compact_error(exc)}")

        if financials.market_cap is None and quote.market_cap is not None:
            financials.market_cap = quote.market_cap
        if financials.pe_ratio is None and quote.pe_ratio is not None:
            financials.pe_ratio = quote.pe_ratio
        if financials.eps is None and quote.eps is not None:
            financials.eps = quote.eps
        if errors:
            _extend_unique(quote.notes, errors)

        indicators = calculate_indicators(history)
        return StockSnapshot(
            symbol=normalized,
            quote=quote,
            history=history,
            financials=financials,
            news=news,
            indicators=indicators,
            fetched_at=utc_now_iso(),
        )

    def get_quote(self, symbol: str) -> str:
        normalized = _resolve_symbol(symbol)
        quote = self.provider.get_quote(normalized)
        return "\n".join([
            f"标的: {normalized} {quote.name}".strip(),
            f"价格: {quote.price} {quote.currency}",
            f"涨跌: {quote.change} ({quote.change_percent}%)",
            f"成交量: {quote.volume}",
            f"数据源: {quote.source}",
            f"时间: {quote.as_of}",
            f"实时/准实时: {'是' if quote.is_realtime else '否'}",
            *[f"备注: {note}" for note in quote.notes],
        ])

    def get_price_history(self, symbol: str, period: str = "1y", format: str = "summary") -> str:
        normalized = _resolve_symbol(symbol)
        try:
            history = self.provider.get_history(normalized, period, "1d")
        except Exception as exc:
            return f"{normalized}: 历史价格获取失败: {_compact_error(exc)}"
        if format == "csv":
            return export_history_csv(history)
        indicators = calculate_indicators(history)
        return "\n".join([
            f"标的: {normalized}",
            f"数据点: {len(history)}",
            f"起止: {history[0].date if history else '无'} 到 {history[-1].date if history else '无'}",
            format_indicators(indicators),
        ])

    def get_financials(self, symbol: str) -> str:
        snapshot = self.snapshot(symbol, "3mo", 0)
        return render_stock_report(snapshot).split("## 新闻事件")[0].strip()

    def get_news(self, symbol: str, limit: int = 5) -> str:
        normalized = _resolve_symbol(symbol)
        try:
            news = self.provider.get_news(normalized, limit)
        except Exception as exc:
            error = _compact_error(exc)
            if "empty result" in error:
                return f"{normalized}: 未找到与该标的强相关的新闻；新闻接口可能返回了噪声或被过滤。"
            return f"{normalized}: 新闻获取失败: {error}"
        if not news:
            return f"{normalized}: 暂无新闻数据。"
        lines = [f"{normalized} 新闻:"]
        for item in news:
            lines.append(f"- {item.title} ({item.publisher}, {item.published_at})")
            if item.link:
                lines.append(f"  {item.link}")
        return "\n".join(lines)

    def calculate_indicators(self, symbol: str, period: str = "1y") -> str:
        normalized = _resolve_symbol(symbol)
        try:
            history = self.provider.get_history(normalized, period, "1d")
        except Exception as exc:
            return f"{normalized}: 技术指标计算失败，历史价格获取失败: {_compact_error(exc)}"
        return format_indicators(calculate_indicators(history))

    def generate_report(self, symbol: str, period: str = "1y") -> str:
        return render_stock_report(self.snapshot(symbol, period, 5))

    def quality_screen(self, symbol: str, period: str = "1y") -> str:
        return render_quality_screen(self.snapshot(symbol, period, 5))

    def compare_stocks(self, symbols: list[str] | str, period: str = "1y") -> str:
        symbol_list = _coerce_symbols(symbols)
        snapshots = [self.snapshot(symbol, period, 3) for symbol in symbol_list]
        return render_comparison(snapshots)

    def debate_stocks(self, symbols: list[str] | str, period: str = "1y") -> str:
        symbol_list = _coerce_symbols(symbols)
        snapshots = [self.snapshot(symbol, period, 3) for symbol in symbol_list]
        return debate_stocks(snapshots)

    def backtest_strategy(
        self,
        symbol: str,
        strategy: str | None = None,
        period: str = "2y",
        fast_window: int | None = None,
        slow_window: int | None = None,
        initial_cash: float = 100_000.0,
    ) -> str:
        config = parse_strategy(
            strategy,
            fast_window=fast_window,
            slow_window=slow_window,
            initial_cash=initial_cash,
        )
        try:
            history = self.provider.get_history(normalize_symbol(symbol), period, "1d")
        except Exception as exc:
            return f"{normalize_symbol(symbol)}: 回测失败，历史价格获取失败: {_compact_error(exc)}"
        result = backtest_moving_average_cross(history, config)
        return format_backtest(result)

    def daily_brief(self, symbols: list[str] | str, period: str = "3mo") -> str:
        symbol_list = _coerce_symbols(symbols)
        snapshots = [self.snapshot(symbol, period, 2) for symbol in symbol_list]
        return render_daily_brief(snapshots)

    def build_paper_portfolio(
        self,
        symbols: list[str] | str,
        initial_cash: float = 1_000_000.0,
        period: str = "1y",
        max_positions: int = 5,
        name: str = "default",
    ) -> str:
        symbol_list = _coerce_symbols(symbols)
        snapshots = [self.snapshot(symbol, period, 3) for symbol in symbol_list]
        account, scores = construct_portfolio(
            snapshots,
            initial_cash=initial_cash,
            max_positions=max_positions,
            name=name,
        )
        return render_recommendation(account, scores)

    def rebalance_paper_portfolio(
        self,
        symbols: list[str] | str,
        period: str = "1y",
        max_positions: int = 5,
        name: str = "default",
    ) -> str:
        symbol_list = _coerce_symbols(symbols)
        snapshots = [self.snapshot(symbol, period, 3) for symbol in symbol_list]
        account, scores = rebalance_portfolio(
            snapshots,
            name=name,
            max_positions=max_positions,
        )
        return render_recommendation(account, scores)

    def mark_paper_portfolio(self, name: str = "default") -> str:
        account = mark_to_market(get_quote=self.provider.get_quote, name=name)
        return render_account(account)

    def show_paper_portfolio(self, name: str = "default") -> str:
        return render_account(load_account(name))

    def route_task(self, task: str) -> str:
        symbols = extract_symbols(task)
        if not symbols and _looks_like_stock_task(task):
            symbols = [_resolve_symbol(_extract_name_query(task))]
        if not symbols:
            symbols = ["AAPL"]
        lowered = task.lower()
        period = _extract_period(task)
        if _is_portfolio_task(task):
            return self.build_paper_portfolio(symbols, _extract_cash(task) or 1_000_000.0, period or "1y")
        if _is_market_update_task(task):
            return self.market_update_task(task, symbols[0])
        if any(word in task for word in ("标的", "代码", "上市", "是不是上市", "已经上市")):
            return self.verify_symbol_task(task, symbols[0])
        if any(word in task for word in ("回测", "策略")) or "backtest" in lowered:
            return self.backtest_strategy(symbols[0], task, period or "2y")
        if any(word in task for word in ("简报", "自选股")) or "brief" in lowered:
            return self.daily_brief(symbols, period or "3mo")
        if any(word in task for word in ("质量门禁", "去劣", "初筛", "checklist", "quality")):
            return self.quality_screen(symbols[0], period or "1y")
        if any(word in task for word in ("比较", "对比")) or "compare" in lowered:
            return self.compare_stocks(symbols, period or "1y")
        if any(word in task for word in ("辩论", "选股", "debate")):
            return self.debate_stocks(symbols, period or "1y")
        return self.generate_report(symbols[0], period or "1y")

    def verify_symbol_task(self, task: str, symbol: str) -> str:
        normalized = _resolve_symbol(symbol)
        query = _verification_query(task, normalized)
        parts = [
            "# 标的核验",
            "",
            f"- 识别标的: {normalized}",
            "",
            "## 公开网页搜索",
            web_search(query, 5),
            "",
            "## 行情核验",
            self.get_quote(normalized),
            "",
            "说明：网页搜索用于确认上市状态、代码和公开页面；行情数据仍以返回的数据源、时间和备注为准。",
        ]
        return "\n".join(parts)

    def market_update_task(self, task: str, symbol: str) -> str:
        """Return a source-first market update for today's/latest status questions."""
        normalized = _resolve_symbol(symbol)
        query = _verification_query(task, normalized)
        parts = [
            "# 今日市场核验",
            "",
            f"- 识别标的: {normalized}",
            "",
            "## 上市状态与代码核验",
            web_search(query, 5),
            "",
            "## 公开网页核验",
            web_search(f"{task} {normalized} latest news stock", 5),
            "",
            "## 行情快照",
            self.get_quote(normalized),
            "",
            "## 近期技术面",
            self.calculate_indicators(normalized, "3mo"),
            "",
            "## 新闻摘要",
            self.get_news(normalized, 5),
            "",
            "## 边界",
            "- 以上只做研究核验，不构成买卖建议。",
            "- 若网页搜索入口失败，请优先使用返回的公开财经页面链接或 /fetch URL 交叉验证。",
        ]
        return "\n".join(parts)

    def resolve_symbol(self, query: str, limit: int = 8) -> str:
        return resolve_symbol_text(query, limit)


def _coerce_symbols(symbols: list[str] | str) -> list[str]:
    if isinstance(symbols, str):
        extracted = extract_symbols(symbols)
        if extracted:
            return extracted
        raw = [part.strip() for part in symbols.replace("，", ",").split(",")]
        return [_resolve_symbol(part) for part in raw if part]
    return [_resolve_symbol(symbol) for symbol in symbols if symbol]


def _extract_period(task: str) -> str:
    lowered = task.lower()
    if any(token in task for token in ("三个月", "3个月", "近三月", "最近三月")) or "3mo" in lowered:
        return "3mo"
    if any(token in task for token in ("一个月", "1个月", "近一月", "最近一月")) or "1mo" in lowered:
        return "1mo"
    if any(token in task for token in ("半年", "六个月", "6个月")) or "6mo" in lowered:
        return "6mo"
    if any(token in task for token in ("两年", "2年", "过去两年")) or "2y" in lowered:
        return "2y"
    if any(token in task for token in ("五年", "5年", "过去五年")) or "5y" in lowered:
        return "5y"
    return ""


def _extract_cash(task: str) -> float | None:
    match = re.search(r"(\d+(?:\.\d+)?)\s*(万|w|W)", task)
    if match:
        return float(match.group(1)) * 10_000
    match = re.search(r"(\d+(?:\.\d+)?)\s*(百万|million)", task, flags=re.IGNORECASE)
    if match:
        return float(match.group(1)) * 1_000_000
    match = re.search(r"(\d+(?:\.\d+)?)\s*(?:元|cash|资金)", task, flags=re.IGNORECASE)
    if match:
        return float(match.group(1))
    if "一百万" in task:
        return 1_000_000.0
    return None


def _is_market_update_task(task: str) -> bool:
    return any(token in task for token in ("今天", "今日", "当天", "现在", "最新", "情况", "怎么了", "股价", "行情"))


def _is_portfolio_task(task: str) -> bool:
    lowered = task.lower()
    return any(token in task for token in ("100万", "一百万", "模拟组合", "纸面组合", "自己投资", "买多少", "仓位", "建仓")) or any(
        token in lowered for token in ("paper portfolio", "portfolio", "allocate", "allocation")
    )


def _resolve_symbol(symbol: str) -> str:
    try:
        return resolve_symbol(symbol).symbol
    except Exception:
        return normalize_symbol(symbol)


def _looks_like_stock_task(task: str) -> bool:
    lowered = task.lower()
    return any(token in task for token in ("股价", "股票", "行情", "走势", "今天", "今日", "最新", "上市")) or any(
        token in lowered for token in ("stock", "quote", "price", "ticker")
    )


def _extract_name_query(task: str) -> str:
    cleaned = task
    for token in ("股价", "股票", "行情", "走势", "今天", "今日", "最新", "怎么样", "如何", "看看", "看一下", "查一下", "上市"):
        cleaned = cleaned.replace(token, " ")
    return " ".join(cleaned.split()) or task


def _compact_error(exc: Exception, limit: int = 220) -> str:
    text = " ".join(str(exc).split())
    text = text.replace("For more information check:", "详情:")
    if len(text) <= limit:
        return text
    return text[:limit] + "..."


def _verification_query(task: str, symbol: str) -> str:
    terms: list[str] = []
    if "智谱" in task:
        terms.append("智谱")
    if "spacex" in task.lower():
        terms.append("SpaceX")
    terms.append(symbol)
    if symbol.endswith(".HK"):
        code = symbol[:-3]
        terms.append(code)
        stripped = code.lstrip("0")
        if stripped and stripped != code:
            terms.append(stripped)
    terms.append("股票")
    if re.search(r"[A-Za-z]", task + symbol):
        terms.extend(["stock", "ticker", "IPO", "Nasdaq"])
    unique: list[str] = []
    for term in terms:
        if term and term not in unique:
            unique.append(term)
    return " ".join(unique)


def _extend_unique(target: list[str], values: list[str]) -> None:
    for value in values:
        if value not in target:
            target.append(value)
