"""Market data providers.

The provider chain tries real data sources first and falls back to clearly
marked sample data when the network/API is unavailable.
"""
from __future__ import annotations

import csv
import math
import os
from datetime import datetime, timedelta
from io import StringIO
from typing import Any, Protocol

import httpx

from config import load_local_env
from .models import Candle, Financials, NewsItem, Quote, utc_now_iso
from .symbols import is_a_share, normalize_symbol, to_akshare_symbol, to_tushare_symbol


class MarketDataProvider(Protocol):
    name: str

    def get_quote(self, symbol: str) -> Quote:
        ...

    def get_history(self, symbol: str, period: str = "1y", interval: str = "1d") -> list[Candle]:
        ...

    def get_financials(self, symbol: str) -> Financials:
        ...

    def get_news(self, symbol: str, limit: int = 5) -> list[NewsItem]:
        ...


class ProviderError(RuntimeError):
    pass


class AlphaVantageProvider:
    name = "Alpha Vantage"

    def __init__(self, api_key: str | None = None, timeout: float = 20.0):
        self.api_key = api_key or os.environ.get("ALPHAVANTAGE_API_KEY", "")
        self.client = httpx.Client(timeout=timeout, follow_redirects=True)

    def available(self) -> bool:
        return bool(self.api_key)

    def _get(self, params: dict[str, str]) -> dict[str, Any]:
        if not self.api_key:
            raise ProviderError("missing ALPHAVANTAGE_API_KEY")
        params = dict(params)
        params["apikey"] = self.api_key
        response = self.client.get("https://www.alphavantage.co/query", params=params)
        response.raise_for_status()
        data = response.json()
        if "Error Message" in data:
            raise ProviderError(data["Error Message"])
        if "Note" in data or "Information" in data:
            raise ProviderError(data.get("Note") or data.get("Information") or "rate limited")
        return data

    def get_quote(self, symbol: str) -> Quote:
        normalized = normalize_symbol(symbol)
        data = self._get({"function": "GLOBAL_QUOTE", "symbol": normalized})
        raw = data.get("Global Quote") or {}
        if not raw:
            raise ProviderError("empty Alpha Vantage quote")
        price = _to_float(raw.get("05. price"))
        previous = _to_float(raw.get("08. previous close"))
        change = _to_float(raw.get("09. change"))
        change_percent = _percent_to_float(raw.get("10. change percent"))
        return Quote(
            symbol=normalized,
            price=price,
            previous_close=previous,
            change=change,
            change_percent=change_percent,
            volume=_to_int(raw.get("06. volume")),
            source=self.name,
            as_of=raw.get("07. latest trading day") or utc_now_iso(),
            is_realtime=True,
        )

    def get_history(self, symbol: str, period: str = "1y", interval: str = "1d") -> list[Candle]:
        normalized = normalize_symbol(symbol)
        output_size = "full" if period in {"2y", "5y", "max"} else "compact"
        data = self._get({
            "function": "TIME_SERIES_DAILY_ADJUSTED",
            "symbol": normalized,
            "outputsize": output_size,
        })
        series = data.get("Time Series (Daily)") or {}
        candles = [
            Candle(
                date=date,
                open=_to_float(row.get("1. open")),
                high=_to_float(row.get("2. high")),
                low=_to_float(row.get("3. low")),
                close=_to_float(row.get("5. adjusted close") or row.get("4. close")),
                volume=_to_int(row.get("6. volume")),
            )
            for date, row in series.items()
        ]
        candles.sort(key=lambda c: c.date)
        return _trim_period(candles, period)

    def get_financials(self, symbol: str) -> Financials:
        normalized = normalize_symbol(symbol)
        data = self._get({"function": "OVERVIEW", "symbol": normalized})
        if not data or "Symbol" not in data:
            raise ProviderError("empty Alpha Vantage overview")
        return Financials(
            symbol=normalized,
            source=self.name,
            as_of=utc_now_iso(),
            market_cap=_to_float(data.get("MarketCapitalization")),
            pe_ratio=_to_float(data.get("PERatio")),
            forward_pe=_to_float(data.get("ForwardPE")),
            eps=_to_float(data.get("EPS")),
            revenue=_to_float(data.get("RevenueTTM")),
            gross_profit=_to_float(data.get("GrossProfitTTM")),
            net_income=_to_float(data.get("NetIncomeTTM")),
            debt_to_equity=_to_float(data.get("DebtToEquityRatio")),
            return_on_equity=_to_float(data.get("ReturnOnEquityTTM")),
            profit_margin=_to_float(data.get("ProfitMargin")),
        )

    def get_news(self, symbol: str, limit: int = 5) -> list[NewsItem]:
        normalized = normalize_symbol(symbol)
        data = self._get({"function": "NEWS_SENTIMENT", "tickers": normalized, "limit": str(limit)})
        items = []
        for row in (data.get("feed") or [])[:limit]:
            items.append(NewsItem(
                title=row.get("title", ""),
                publisher=row.get("source", ""),
                link=row.get("url", ""),
                published_at=row.get("time_published", ""),
                summary=row.get("summary", ""),
                source=self.name,
            ))
        return items


class YahooFinanceProvider:
    name = "Yahoo Finance public endpoints"

    def __init__(self, timeout: float = 20.0):
        self.client = httpx.Client(
            timeout=timeout,
            follow_redirects=True,
            headers={
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Safari/537.36",
                "Accept": "application/json,text/plain,*/*",
            },
        )

    def _chart(self, symbol: str, period: str, interval: str) -> dict[str, Any]:
        normalized = normalize_symbol(symbol)
        response = self.client.get(
            f"https://query1.finance.yahoo.com/v8/finance/chart/{normalized}",
            params={"range": period, "interval": interval, "includePrePost": "false"},
        )
        response.raise_for_status()
        data = response.json()
        chart = data.get("chart", {})
        if chart.get("error"):
            raise ProviderError(str(chart["error"]))
        result = (chart.get("result") or [None])[0]
        if not result:
            raise ProviderError("empty Yahoo chart")
        return result

    def get_quote(self, symbol: str) -> Quote:
        normalized = normalize_symbol(symbol)
        result = self._chart(normalized, "1d", "1m")
        meta = result.get("meta", {})
        timestamp = result.get("timestamp") or []
        quote_rows = ((result.get("indicators") or {}).get("quote") or [{}])[0]
        closes = [c for c in quote_rows.get("close", []) if c is not None]
        volumes = [v for v in quote_rows.get("volume", []) if v is not None]
        price = _to_float(meta.get("regularMarketPrice"))
        if price is None and closes:
            price = _to_float(closes[-1])
        previous = _to_float(meta.get("previousClose") or meta.get("chartPreviousClose"))
        change = price - previous if price is not None and previous not in (None, 0) else None
        change_percent = change / previous * 100 if change is not None and previous else None
        as_of = utc_now_iso()
        is_realtime = True
        if timestamp:
            as_of_dt = datetime.utcfromtimestamp(timestamp[-1]).replace(microsecond=0)
            as_of = as_of_dt.isoformat() + "Z"
            is_realtime = datetime.utcnow() - as_of_dt <= timedelta(hours=36)
        notes = ["Yahoo public endpoints may be delayed or rate limited."]
        if not is_realtime:
            notes.append("Latest Yahoo timestamp is older than 36 hours; treat it as delayed historical data.")
        return Quote(
            symbol=normalized,
            name=meta.get("longName") or meta.get("shortName") or "",
            currency=meta.get("currency", ""),
            price=price,
            previous_close=previous,
            change=change,
            change_percent=change_percent,
            volume=_to_int(meta.get("regularMarketVolume")) or (sum(_to_int(v) or 0 for v in volumes) if volumes else None),
            source=self.name,
            as_of=as_of,
            is_realtime=is_realtime,
            notes=notes,
        )

    def get_history(self, symbol: str, period: str = "1y", interval: str = "1d") -> list[Candle]:
        normalized = normalize_symbol(symbol)
        result = self._chart(normalized, period, interval)
        timestamps = result.get("timestamp") or []
        quote_rows = ((result.get("indicators") or {}).get("quote") or [{}])[0]
        candles: list[Candle] = []
        for index, ts in enumerate(timestamps):
            candles.append(Candle(
                date=datetime.utcfromtimestamp(ts).date().isoformat(),
                open=_list_float(quote_rows.get("open"), index),
                high=_list_float(quote_rows.get("high"), index),
                low=_list_float(quote_rows.get("low"), index),
                close=_list_float(quote_rows.get("close"), index),
                volume=_list_int(quote_rows.get("volume"), index),
            ))
        return [c for c in candles if c.close is not None]

    def get_financials(self, symbol: str) -> Financials:
        normalized = normalize_symbol(symbol)
        modules = "summaryDetail,defaultKeyStatistics,financialData"
        response = self.client.get(
            f"https://query2.finance.yahoo.com/v10/finance/quoteSummary/{normalized}",
            params={"modules": modules},
        )
        response.raise_for_status()
        data = response.json()
        result = (((data.get("quoteSummary") or {}).get("result") or [None])[0]) or {}
        if not result:
            raise ProviderError("empty Yahoo quote summary")
        summary = result.get("summaryDetail") or {}
        stats = result.get("defaultKeyStatistics") or {}
        financial = result.get("financialData") or {}
        return Financials(
            symbol=normalized,
            source=self.name,
            as_of=utc_now_iso(),
            market_cap=_raw(summary.get("marketCap") or stats.get("enterpriseValue")),
            pe_ratio=_raw(summary.get("trailingPE")),
            forward_pe=_raw(summary.get("forwardPE")),
            eps=_raw(stats.get("trailingEps")),
            revenue=_raw(financial.get("totalRevenue")),
            gross_profit=_raw(financial.get("grossProfits")),
            net_income=_raw(financial.get("netIncomeToCommon")),
            free_cash_flow=_raw(financial.get("freeCashflow")),
            debt_to_equity=_raw(financial.get("debtToEquity")),
            return_on_equity=_raw(financial.get("returnOnEquity")),
            profit_margin=_raw(summary.get("profitMargins")),
            notes=["Yahoo quote summary fields may be incomplete for some markets."],
        )

    def get_news(self, symbol: str, limit: int = 5) -> list[NewsItem]:
        normalized = normalize_symbol(symbol)
        response = self.client.get(
            "https://query2.finance.yahoo.com/v1/finance/search",
            params={"q": normalized, "quotesCount": "1", "newsCount": str(limit)},
        )
        response.raise_for_status()
        data = response.json()
        items: list[NewsItem] = []
        for row in (data.get("news") or [])[:limit]:
            published = row.get("providerPublishTime")
            items.append(NewsItem(
                title=row.get("title", ""),
                publisher=row.get("publisher", ""),
                link=row.get("link", ""),
                published_at=(
                    datetime.utcfromtimestamp(published).replace(microsecond=0).isoformat() + "Z"
                    if published else ""
                ),
                summary=row.get("summary", ""),
                source=self.name,
            ))
        return items


class TushareProvider:
    name = "Tushare Pro"

    def __init__(self, token: str | None = None):
        self.token = token or os.environ.get("TUSHARE_TOKEN", "")
        self._pro = None

    def available(self) -> bool:
        return bool(self.token)

    def _client(self) -> Any:
        if not self.token:
            raise ProviderError("missing TUSHARE_TOKEN")
        if self._pro is None:
            try:
                import tushare as ts  # type: ignore
            except ImportError as exc:
                raise ProviderError("tushare package is not installed") from exc
            ts.set_token(self.token)
            self._pro = ts.pro_api(self.token)
        return self._pro

    def _require_a_share(self, symbol: str) -> tuple[str, str]:
        normalized = normalize_symbol(symbol)
        if not is_a_share(normalized):
            raise ProviderError("TushareProvider supports A-share symbols only")
        return normalized, to_tushare_symbol(normalized)

    def get_quote(self, symbol: str) -> Quote:
        normalized, ts_code = self._require_a_share(symbol)
        pro = self._client()
        start_date, end_date = _date_window("1mo")
        daily = pro.daily(ts_code=ts_code, start_date=start_date, end_date=end_date)
        if daily is None or daily.empty:
            raise ProviderError("empty Tushare daily quote")
        daily = daily.sort_values("trade_date")
        latest = daily.iloc[-1]
        previous = daily.iloc[-2] if len(daily) > 1 else None
        basics = self._daily_basic(pro, ts_code)
        name = self._stock_name(pro, ts_code)
        price = _to_float(latest.get("close"))
        previous_close = _to_float(previous.get("close")) if previous is not None else _to_float(latest.get("pre_close"))
        change = price - previous_close if price is not None and previous_close not in (None, 0) else _to_float(latest.get("change"))
        change_percent = (
            change / previous_close * 100
            if change is not None and previous_close
            else _to_float(latest.get("pct_chg"))
        )
        trade_date = str(latest.get("trade_date", ""))
        return Quote(
            symbol=normalized,
            name=name,
            currency="CNY",
            price=price,
            previous_close=previous_close,
            change=change,
            change_percent=change_percent,
            volume=_to_int(latest.get("vol")),
            market_cap=_to_float(basics.get("total_mv")) * 10_000 if basics.get("total_mv") is not None else None,
            pe_ratio=_to_float(basics.get("pe_ttm") or basics.get("pe")),
            source=self.name,
            as_of=_format_trade_date(trade_date),
            is_realtime=False,
            notes=["Tushare daily data is end-of-day data, not tick-level realtime data."],
        )

    def get_history(self, symbol: str, period: str = "1y", interval: str = "1d") -> list[Candle]:
        normalized, ts_code = self._require_a_share(symbol)
        pro = self._client()
        start_date, end_date = _date_window(period)
        data = pro.daily(ts_code=ts_code, start_date=start_date, end_date=end_date)
        if data is None or data.empty:
            raise ProviderError("empty Tushare history")
        data = data.sort_values("trade_date")
        candles: list[Candle] = []
        for _, row in data.iterrows():
            candles.append(Candle(
                date=_format_trade_date(str(row.get("trade_date", ""))),
                open=_to_float(row.get("open")),
                high=_to_float(row.get("high")),
                low=_to_float(row.get("low")),
                close=_to_float(row.get("close")),
                volume=_to_int(row.get("vol")),
            ))
        return candles

    def get_financials(self, symbol: str) -> Financials:
        normalized, ts_code = self._require_a_share(symbol)
        pro = self._client()
        basics = self._daily_basic(pro, ts_code)
        income = self._latest_report(pro, "income", ts_code)
        cashflow = self._latest_report(pro, "cashflow", ts_code)
        fina_indicator = self._latest_report(pro, "fina_indicator", ts_code)
        revenue = _to_float(income.get("total_revenue") or income.get("revenue"))
        net_income = _to_float(income.get("n_income_attr_p") or income.get("net_profit"))
        return Financials(
            symbol=normalized,
            source=self.name,
            as_of=utc_now_iso(),
            market_cap=_to_float(basics.get("total_mv")) * 10_000 if basics.get("total_mv") is not None else None,
            pe_ratio=_to_float(basics.get("pe_ttm") or basics.get("pe")),
            eps=_to_float(fina_indicator.get("eps")),
            revenue=revenue,
            gross_profit=_to_float(income.get("grossprofit")),
            net_income=net_income,
            free_cash_flow=_to_float(cashflow.get("free_cashflow") or cashflow.get("n_cashflow_act")),
            debt_to_equity=_to_float(fina_indicator.get("debt_to_assets")),
            return_on_equity=_to_float(fina_indicator.get("roe")),
            profit_margin=(net_income / revenue if net_income is not None and revenue else None),
            notes=["Tushare fundamentals depend on token permission and reporting availability."],
        )

    def get_news(self, symbol: str, limit: int = 5) -> list[NewsItem]:
        raise ProviderError("Tushare news is not enabled in this provider")

    def _daily_basic(self, pro: Any, ts_code: str) -> dict[str, Any]:
        try:
            start_date, end_date = _date_window("1mo")
            data = pro.daily_basic(ts_code=ts_code, start_date=start_date, end_date=end_date)
            if data is not None and not data.empty:
                return data.sort_values("trade_date").iloc[-1].to_dict()
        except Exception:
            return {}
        return {}

    def _stock_name(self, pro: Any, ts_code: str) -> str:
        try:
            data = pro.stock_basic(fields="ts_code,name")
            if data is not None and not data.empty:
                row = data.loc[data["ts_code"].astype(str) == ts_code]
                if not row.empty:
                    return str(row.iloc[0].get("name", ""))
        except Exception:
            return ""
        return ""

    def _latest_report(self, pro: Any, method: str, ts_code: str) -> dict[str, Any]:
        try:
            fn = getattr(pro, method)
            data = fn(ts_code=ts_code)
            if data is not None and not data.empty:
                sort_column = "end_date" if "end_date" in data.columns else data.columns[0]
                return data.sort_values(sort_column).iloc[-1].to_dict()
        except Exception:
            return {}
        return {}


class AKShareProvider:
    name = "AKShare"

    def __init__(self):
        self._ak = None

    def _client(self) -> Any:
        if self._ak is None:
            try:
                import akshare as ak  # type: ignore
            except ImportError as exc:
                raise ProviderError("akshare package is not installed") from exc
            self._ak = ak
        return self._ak

    def _require_a_share(self, symbol: str) -> tuple[str, str]:
        normalized = normalize_symbol(symbol)
        if not is_a_share(normalized):
            raise ProviderError("AKShareProvider supports A-share symbols only")
        return normalized, to_akshare_symbol(normalized)

    def get_quote(self, symbol: str) -> Quote:
        normalized, code = self._require_a_share(symbol)
        ak = self._client()
        data = ak.stock_zh_a_spot_em()
        if data is None or data.empty:
            raise ProviderError("empty AKShare spot data")
        row = data.loc[data["代码"].astype(str) == code]
        if row.empty:
            raise ProviderError(f"{code} not found in AKShare spot data")
        item = row.iloc[0].to_dict()
        return Quote(
            symbol=normalized,
            name=str(item.get("名称", "")),
            currency="CNY",
            price=_to_float(item.get("最新价")),
            previous_close=None,
            change=_to_float(item.get("涨跌额")),
            change_percent=_to_float(item.get("涨跌幅")),
            volume=_to_int(item.get("成交量")),
            market_cap=_to_float(item.get("总市值")),
            pe_ratio=_to_float(item.get("市盈率-动态") or item.get("市盈率")),
            source=self.name,
            as_of=utc_now_iso(),
            is_realtime=True,
            notes=["AKShare realtime fields depend on upstream Eastmoney availability and may be delayed."],
        )

    def get_history(self, symbol: str, period: str = "1y", interval: str = "1d") -> list[Candle]:
        normalized, code = self._require_a_share(symbol)
        ak = self._client()
        start_date, end_date = _date_window(period)
        data = ak.stock_zh_a_hist(
            symbol=code,
            period="daily",
            start_date=start_date,
            end_date=end_date,
            adjust="qfq",
        )
        if data is None or data.empty:
            raise ProviderError("empty AKShare history")
        candles: list[Candle] = []
        for _, row in data.iterrows():
            candles.append(Candle(
                date=str(row.get("日期", "")),
                open=_to_float(row.get("开盘")),
                high=_to_float(row.get("最高")),
                low=_to_float(row.get("最低")),
                close=_to_float(row.get("收盘")),
                volume=_to_int(row.get("成交量")),
            ))
        return candles

    def get_financials(self, symbol: str) -> Financials:
        normalized, code = self._require_a_share(symbol)
        quote = self.get_quote(normalized)
        notes = ["AKShare financial provider currently uses spot valuation fields; detailed statements are future work."]
        return Financials(
            symbol=normalized,
            source=self.name,
            as_of=utc_now_iso(),
            market_cap=quote.market_cap,
            pe_ratio=quote.pe_ratio,
            notes=notes,
        )

    def get_news(self, symbol: str, limit: int = 5) -> list[NewsItem]:
        normalized, code = self._require_a_share(symbol)
        ak = self._client()
        if not hasattr(ak, "stock_news_em"):
            raise ProviderError("AKShare stock_news_em is unavailable")
        data = ak.stock_news_em(symbol=code)
        if data is None or data.empty:
            raise ProviderError("empty AKShare news")
        items: list[NewsItem] = []
        for _, row in data.head(limit).iterrows():
            items.append(NewsItem(
                title=str(row.get("新闻标题") or row.get("标题") or ""),
                publisher=str(row.get("文章来源") or row.get("来源") or "Eastmoney"),
                link=str(row.get("新闻链接") or row.get("链接") or ""),
                published_at=str(row.get("发布时间") or row.get("时间") or ""),
                source=self.name,
            ))
        return items


class SampleDataProvider:
    name = "SAMPLE_FALLBACK"

    def get_quote(self, symbol: str) -> Quote:
        normalized = normalize_symbol(symbol)
        profile = _SAMPLE_PROFILES.get(normalized, _generic_profile(normalized))
        history = self.get_history(normalized, "1y", "1d")
        last = history[-1].close if history else profile["price"]
        prev = history[-2].close if len(history) > 1 else profile["price"] * 0.99
        change = last - prev if last is not None and prev is not None else None
        change_percent = change / prev * 100 if change is not None and prev else None
        return Quote(
            symbol=normalized,
            name=profile["name"],
            currency=profile["currency"],
            price=last,
            previous_close=prev,
            change=change,
            change_percent=change_percent,
            volume=profile["volume"],
            market_cap=profile["market_cap"],
            pe_ratio=profile["pe_ratio"],
            eps=profile["eps"],
            source=self.name,
            as_of=utc_now_iso(),
            is_realtime=False,
            notes=["样例 fallback 数据，仅用于离线演示；请勿当作真实行情。"],
        )

    def get_history(self, symbol: str, period: str = "1y", interval: str = "1d") -> list[Candle]:
        normalized = normalize_symbol(symbol)
        profile = _SAMPLE_PROFILES.get(normalized, _generic_profile(normalized))
        days = _period_to_days(period)
        base_price = profile["price"]
        trend = profile["trend"]
        volatility = profile["volatility"]
        candles: list[Candle] = []
        start = datetime.utcnow().date() - timedelta(days=days * 7 // 5 + 10)
        trading_day = 0
        current = start
        while len(candles) < days:
            current += timedelta(days=1)
            if current.weekday() >= 5:
                continue
            progress = trading_day / max(days - 1, 1)
            seasonal = math.sin(trading_day / 9.0) * volatility + math.cos(trading_day / 23.0) * volatility * 0.6
            close = base_price * (1 + trend * (progress - 1) + seasonal)
            open_price = close * (1 - math.sin(trading_day / 5.0) * volatility * 0.25)
            high = max(open_price, close) * (1 + volatility * 0.4)
            low = min(open_price, close) * (1 - volatility * 0.4)
            candles.append(Candle(
                date=current.isoformat(),
                open=round(open_price, 2),
                high=round(high, 2),
                low=round(low, 2),
                close=round(close, 2),
                volume=int(profile["volume"] * (0.7 + 0.3 * (1 + math.sin(trading_day / 11.0)))),
            ))
            trading_day += 1
        return candles

    def get_financials(self, symbol: str) -> Financials:
        normalized = normalize_symbol(symbol)
        profile = _SAMPLE_PROFILES.get(normalized, _generic_profile(normalized))
        return Financials(
            symbol=normalized,
            source=self.name,
            as_of=utc_now_iso(),
            market_cap=profile["market_cap"],
            pe_ratio=profile["pe_ratio"],
            forward_pe=profile["forward_pe"],
            eps=profile["eps"],
            revenue=profile["revenue"],
            gross_profit=profile["gross_profit"],
            net_income=profile["net_income"],
            free_cash_flow=profile["free_cash_flow"],
            debt_to_equity=profile["debt_to_equity"],
            return_on_equity=profile["return_on_equity"],
            profit_margin=profile["profit_margin"],
            notes=["样例 fallback 数据，仅用于离线演示；请接入真实数据源后再做研究。"],
        )

    def get_news(self, symbol: str, limit: int = 5) -> list[NewsItem]:
        normalized = normalize_symbol(symbol)
        profile = _SAMPLE_PROFILES.get(normalized, _generic_profile(normalized))
        rows = [
            f"{profile['name']} 发布最新经营数据，市场关注收入增长和利润率变化",
            f"分析师讨论 {profile['name']} 的估值水平与行业竞争格局",
            f"宏观利率和风险偏好变化可能影响 {profile['name']} 的估值倍数",
        ]
        return [
            NewsItem(
                title=row,
                publisher="Sample News",
                published_at=utc_now_iso(),
                source=self.name,
                summary="样例新闻，仅用于离线演示。",
            )
            for row in rows[:limit]
        ]


class ProviderChain:
    def __init__(self, providers: list[MarketDataProvider] | None = None):
        load_local_env()
        default: list[MarketDataProvider] = []
        alpha = AlphaVantageProvider()
        tushare = TushareProvider()
        if alpha.available():
            default.append(alpha)
        if tushare.available():
            default.append(tushare)
        default.extend([AKShareProvider(), YahooFinanceProvider(), SampleDataProvider()])
        self.providers = providers or default

    def get_quote(self, symbol: str) -> Quote:
        return self._first("get_quote", symbol)

    def get_history(self, symbol: str, period: str = "1y", interval: str = "1d") -> list[Candle]:
        return self._first("get_history", symbol, period, interval)

    def get_financials(self, symbol: str) -> Financials:
        return self._first("get_financials", symbol)

    def get_news(self, symbol: str, limit: int = 5) -> list[NewsItem]:
        return self._first("get_news", symbol, limit)

    def _first(self, method: str, *args: Any) -> Any:
        errors: list[str] = []
        for provider in self.providers:
            try:
                result = getattr(provider, method)(*args)
                if result:
                    return result
                errors.append(f"{provider.name}: empty result")
            except Exception as exc:  # noqa: BLE001 - convert provider failures to notes/fallback
                errors.append(f"{provider.name}: {exc}")
        raise ProviderError("; ".join(errors))


def export_history_csv(candles: list[Candle]) -> str:
    buffer = StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["date", "open", "high", "low", "close", "volume"])
    for candle in candles:
        writer.writerow([candle.date, candle.open, candle.high, candle.low, candle.close, candle.volume])
    return buffer.getvalue()


def _raw(value: Any) -> float | None:
    if isinstance(value, dict):
        value = value.get("raw")
    return _to_float(value)


def _to_float(value: Any) -> float | None:
    if value in (None, "", "None", "N/A", "-"):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _to_int(value: Any) -> int | None:
    if value in (None, "", "None", "N/A", "-"):
        return None
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


def _percent_to_float(value: Any) -> float | None:
    if isinstance(value, str):
        value = value.replace("%", "")
    return _to_float(value)


def _list_float(values: list[Any] | None, index: int) -> float | None:
    if not values or index >= len(values):
        return None
    return _to_float(values[index])


def _list_int(values: list[Any] | None, index: int) -> int | None:
    if not values or index >= len(values):
        return None
    return _to_int(values[index])


def _period_to_days(period: str) -> int:
    normalized = period.lower().strip()
    table = {"1mo": 22, "3mo": 66, "6mo": 126, "1y": 252, "2y": 504, "5y": 1260}
    if normalized in table:
        return table[normalized]
    if normalized.endswith("d") and normalized[:-1].isdigit():
        return max(int(normalized[:-1]), 5)
    return 252


def _trim_period(candles: list[Candle], period: str) -> list[Candle]:
    days = _period_to_days(period)
    return candles[-days:]


def _date_window(period: str) -> tuple[str, str]:
    end = datetime.utcnow().date()
    start = end - timedelta(days=_period_to_days(period) * 7 // 5 + 10)
    return start.strftime("%Y%m%d"), end.strftime("%Y%m%d")


def _format_trade_date(value: str) -> str:
    text = value.strip()
    if len(text) == 8 and text.isdigit():
        return f"{text[:4]}-{text[4:6]}-{text[6:]}"
    return text


def _generic_profile(symbol: str) -> dict[str, Any]:
    return {
        "name": symbol,
        "currency": "USD",
        "price": 100.0,
        "volume": 10_000_000,
        "market_cap": 50_000_000_000,
        "pe_ratio": 22.0,
        "forward_pe": 20.0,
        "eps": 4.5,
        "revenue": 20_000_000_000,
        "gross_profit": 9_000_000_000,
        "net_income": 4_000_000_000,
        "free_cash_flow": 3_500_000_000,
        "debt_to_equity": 80.0,
        "return_on_equity": 0.18,
        "profit_margin": 0.2,
        "trend": 0.08,
        "volatility": 0.025,
    }


_SAMPLE_PROFILES: dict[str, dict[str, Any]] = {
    "AAPL": {
        **_generic_profile("AAPL"),
        "name": "Apple Inc.",
        "price": 210.0,
        "market_cap": 3_200_000_000_000,
        "pe_ratio": 31.0,
        "forward_pe": 28.0,
        "eps": 6.7,
        "revenue": 390_000_000_000,
        "gross_profit": 180_000_000_000,
        "net_income": 100_000_000_000,
        "free_cash_flow": 95_000_000_000,
        "debt_to_equity": 150.0,
        "return_on_equity": 1.2,
        "profit_margin": 0.25,
        "trend": 0.10,
        "volatility": 0.018,
    },
    "NVDA": {
        **_generic_profile("NVDA"),
        "name": "NVIDIA Corporation",
        "price": 145.0,
        "market_cap": 3_500_000_000_000,
        "pe_ratio": 45.0,
        "forward_pe": 35.0,
        "eps": 3.2,
        "revenue": 130_000_000_000,
        "gross_profit": 95_000_000_000,
        "net_income": 70_000_000_000,
        "free_cash_flow": 60_000_000_000,
        "debt_to_equity": 25.0,
        "return_on_equity": 0.85,
        "profit_margin": 0.54,
        "trend": 0.32,
        "volatility": 0.035,
    },
    "AMD": {
        **_generic_profile("AMD"),
        "name": "Advanced Micro Devices, Inc.",
        "price": 165.0,
        "market_cap": 270_000_000_000,
        "pe_ratio": 48.0,
        "forward_pe": 29.0,
        "eps": 3.4,
        "revenue": 28_000_000_000,
        "gross_profit": 14_000_000_000,
        "net_income": 4_200_000_000,
        "free_cash_flow": 3_000_000_000,
        "debt_to_equity": 7.0,
        "return_on_equity": 0.08,
        "profit_margin": 0.15,
        "trend": 0.18,
        "volatility": 0.04,
    },
    "TSLA": {
        **_generic_profile("TSLA"),
        "name": "Tesla, Inc.",
        "price": 260.0,
        "market_cap": 830_000_000_000,
        "pe_ratio": 70.0,
        "forward_pe": 55.0,
        "eps": 3.7,
        "revenue": 100_000_000_000,
        "gross_profit": 18_000_000_000,
        "net_income": 12_000_000_000,
        "free_cash_flow": 4_500_000_000,
        "debt_to_equity": 15.0,
        "return_on_equity": 0.18,
        "profit_margin": 0.12,
        "trend": 0.02,
        "volatility": 0.045,
    },
    "MSFT": {
        **_generic_profile("MSFT"),
        "name": "Microsoft Corporation",
        "price": 480.0,
        "market_cap": 3_600_000_000_000,
        "pe_ratio": 36.0,
        "forward_pe": 31.0,
        "eps": 13.2,
        "revenue": 260_000_000_000,
        "gross_profit": 180_000_000_000,
        "net_income": 95_000_000_000,
        "free_cash_flow": 75_000_000_000,
        "debt_to_equity": 35.0,
        "return_on_equity": 0.35,
        "profit_margin": 0.36,
        "trend": 0.15,
        "volatility": 0.02,
    },
    "600519.SS": {
        **_generic_profile("600519.SS"),
        "name": "Kweichow Moutai Co., Ltd.",
        "currency": "CNY",
        "price": 1500.0,
        "market_cap": 1_900_000_000_000,
        "pe_ratio": 23.0,
        "forward_pe": 21.0,
        "eps": 65.0,
        "revenue": 170_000_000_000,
        "gross_profit": 155_000_000_000,
        "net_income": 85_000_000_000,
        "free_cash_flow": 75_000_000_000,
        "debt_to_equity": 10.0,
        "return_on_equity": 0.32,
        "profit_margin": 0.50,
        "trend": 0.04,
        "volatility": 0.018,
    },
}
