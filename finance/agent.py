"""High-level finance research facade used by tools and CLI."""
from __future__ import annotations

from .backtest import backtest_moving_average_cross, format_backtest, parse_strategy
from .data import ProviderChain, export_history_csv
from .debate import debate_stocks
from .indicators import calculate_indicators, format_indicators
from .models import StockSnapshot, utc_now_iso
from .report import render_comparison, render_daily_brief, render_stock_report
from .symbols import extract_symbols, normalize_symbol


class FinanceResearchAgent:
    def __init__(self, provider: ProviderChain | None = None):
        self.provider = provider or ProviderChain()

    def snapshot(self, symbol: str, period: str = "1y", news_limit: int = 5) -> StockSnapshot:
        normalized = normalize_symbol(symbol)
        quote = self.provider.get_quote(normalized)
        history = self.provider.get_history(normalized, period, "1d")
        financials = self.provider.get_financials(normalized)
        news = self.provider.get_news(normalized, news_limit)

        if financials.market_cap is None and quote.market_cap is not None:
            financials.market_cap = quote.market_cap
        if financials.pe_ratio is None and quote.pe_ratio is not None:
            financials.pe_ratio = quote.pe_ratio
        if financials.eps is None and quote.eps is not None:
            financials.eps = quote.eps

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
        snapshot = self.snapshot(symbol, "3mo", 3)
        quote = snapshot.quote
        return "\n".join([
            f"标的: {snapshot.symbol} {quote.name}".strip(),
            f"价格: {quote.price} {quote.currency}",
            f"涨跌: {quote.change} ({quote.change_percent}%)",
            f"成交量: {quote.volume}",
            f"数据源: {quote.source}",
            f"时间: {quote.as_of}",
            f"实时/准实时: {'是' if quote.is_realtime else '否'}",
            *[f"备注: {note}" for note in quote.notes],
        ])

    def get_price_history(self, symbol: str, period: str = "1y", format: str = "summary") -> str:
        normalized = normalize_symbol(symbol)
        history = self.provider.get_history(normalized, period, "1d")
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
        normalized = normalize_symbol(symbol)
        news = self.provider.get_news(normalized, limit)
        if not news:
            return f"{normalized}: 暂无新闻数据。"
        lines = [f"{normalized} 新闻:"]
        for item in news:
            lines.append(f"- {item.title} ({item.publisher}, {item.published_at})")
            if item.link:
                lines.append(f"  {item.link}")
        return "\n".join(lines)

    def calculate_indicators(self, symbol: str, period: str = "1y") -> str:
        normalized = normalize_symbol(symbol)
        history = self.provider.get_history(normalized, period, "1d")
        return format_indicators(calculate_indicators(history))

    def generate_report(self, symbol: str, period: str = "1y") -> str:
        return render_stock_report(self.snapshot(symbol, period, 5))

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
        history = self.provider.get_history(normalize_symbol(symbol), period, "1d")
        result = backtest_moving_average_cross(history, config)
        return format_backtest(result)

    def daily_brief(self, symbols: list[str] | str, period: str = "3mo") -> str:
        symbol_list = _coerce_symbols(symbols)
        snapshots = [self.snapshot(symbol, period, 2) for symbol in symbol_list]
        return render_daily_brief(snapshots)

    def route_task(self, task: str) -> str:
        symbols = extract_symbols(task)
        if not symbols:
            symbols = ["AAPL"]
        lowered = task.lower()
        period = _extract_period(task)
        if any(word in task for word in ("回测", "策略")) or "backtest" in lowered:
            return self.backtest_strategy(symbols[0], task, period or "2y")
        if any(word in task for word in ("简报", "自选股")) or "brief" in lowered:
            return self.daily_brief(symbols, period or "3mo")
        if any(word in task for word in ("比较", "对比")) or "compare" in lowered:
            return self.compare_stocks(symbols, period or "1y")
        if any(word in task for word in ("辩论", "选股", "debate")):
            return self.debate_stocks(symbols, period or "1y")
        return self.generate_report(symbols[0], period or "1y")


def _coerce_symbols(symbols: list[str] | str) -> list[str]:
    if isinstance(symbols, str):
        extracted = extract_symbols(symbols)
        if extracted:
            return extracted
        raw = [part.strip() for part in symbols.replace("，", ",").split(",")]
        return [normalize_symbol(part) for part in raw if part]
    return [normalize_symbol(symbol) for symbol in symbols if symbol]


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
