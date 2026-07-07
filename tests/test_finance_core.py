from __future__ import annotations

from datetime import date, timedelta

import pytest

from finance.agent import FinanceResearchAgent
from finance.backtest import StrategyConfig, backtest_moving_average_cross, parse_strategy
from finance.data import ProviderChain, ProviderError, SampleDataProvider
from finance.models import Candle, Financials, NewsItem, Quote
from finance.symbols import extract_symbols, normalize_symbol, to_yahoo_symbol


def test_symbol_normalization_handles_common_markets() -> None:
    assert normalize_symbol("智谱") == "02513.HK"
    assert normalize_symbol("2513.HK") == "2513.HK"
    assert normalize_symbol("02513") == "02513.HK"
    assert normalize_symbol("600519") == "600519.SS"
    assert to_yahoo_symbol("02513.HK") == "2513.HK"
    assert extract_symbols("比较 智谱 和 AAPL 最近走势")[:2] == ["02513.HK", "AAPL"]


def test_provider_chain_falls_through_to_next_provider() -> None:
    chain = ProviderChain(providers=[FailingProvider(), StaticProvider()])

    quote = chain.get_quote("AAPL")

    assert quote.symbol == "AAPL"
    assert quote.source == "STATIC"
    assert quote.price == 123.45


def test_provider_chain_can_report_custom_provider_diagnostics() -> None:
    chain = ProviderChain(providers=[StaticProvider()])

    assert chain.diagnostics() == [{"name": "STATIC", "status": "enabled", "detail": ""}]


def test_sample_fallback_can_be_disabled(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FINANCE_ALLOW_SAMPLE_FALLBACK", "0")

    chain = ProviderChain()

    assert all(not isinstance(provider, SampleDataProvider) for provider in chain.providers)
    fallback = [row for row in chain.diagnostics() if row["name"] == "SAMPLE_FALLBACK"][0]
    assert fallback["status"] == "disabled"


def test_route_task_selects_compare_and_backtest() -> None:
    agent = FinanceResearchAgent(provider=ProviderChain(providers=[StaticProvider()]))

    compare = agent.route_task("比较 AAPL 和 MSFT 的基本面")
    backtest = agent.route_task("帮我回测 AAPL 的 20 日均线上穿 60 日均线策略")

    assert "# 股票对比" in compare
    assert "# 策略回测结果" in backtest


def test_parse_strategy_and_backtest_return_metrics() -> None:
    config = parse_strategy("20 日均线上穿 60 日均线", initial_cash=50_000)
    candles = rising_candles(90)

    result = backtest_moving_average_cross(candles, config)

    assert config.fast_window == 20
    assert config.slow_window == 60
    assert result["strategy"] == "moving_average_cross"
    assert result["initial_cash"] == 50_000
    assert "total_return_pct" in result


class FailingProvider:
    name = "FAILING"

    def get_quote(self, symbol: str) -> Quote:
        raise ProviderError("quote failed")

    def get_history(self, symbol: str, period: str = "1y", interval: str = "1d") -> list[Candle]:
        raise ProviderError("history failed")

    def get_financials(self, symbol: str) -> Financials:
        raise ProviderError("financials failed")

    def get_news(self, symbol: str, limit: int = 5) -> list[NewsItem]:
        raise ProviderError("news failed")


class StaticProvider:
    name = "STATIC"

    def get_quote(self, symbol: str) -> Quote:
        return Quote(symbol=normalize_symbol(symbol), price=123.45, source=self.name, as_of="2026-01-01T00:00:00Z")

    def get_history(self, symbol: str, period: str = "1y", interval: str = "1d") -> list[Candle]:
        return rising_candles(120)

    def get_financials(self, symbol: str) -> Financials:
        return Financials(
            symbol=normalize_symbol(symbol),
            source=self.name,
            as_of="2026-01-01T00:00:00Z",
            market_cap=1_000_000_000,
            pe_ratio=20,
            eps=5,
            revenue=100_000_000,
            net_income=20_000_000,
            return_on_equity=0.18,
        )

    def get_news(self, symbol: str, limit: int = 5) -> list[NewsItem]:
        return [NewsItem(title="Static headline", publisher="STATIC", published_at="2026-01-01", source=self.name)]


def rising_candles(count: int) -> list[Candle]:
    start = date(2025, 1, 1)
    candles: list[Candle] = []
    for index in range(count):
        close = 100 + index
        candles.append(Candle(
            date=(start + timedelta(days=index)).isoformat(),
            open=close - 1,
            high=close + 1,
            low=close - 2,
            close=close,
            volume=1_000_000,
        ))
    return candles
