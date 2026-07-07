"""Ticker normalization helpers."""
from __future__ import annotations

import re

CHINESE_SYMBOLS = {
    "苹果": "AAPL",
    "英伟达": "NVDA",
    "辉达": "NVDA",
    "微软": "MSFT",
    "特斯拉": "TSLA",
    "亚马逊": "AMZN",
    "谷歌": "GOOGL",
    "谷歌a": "GOOGL",
    "谷歌c": "GOOG",
    "amd": "AMD",
    "超威": "AMD",
    "贵州茅台": "600519.SS",
    "茅台": "600519.SS",
    "平安银行": "000001.SZ",
    "招商银行": "600036.SS",
    "腾讯": "0700.HK",
    "阿里巴巴": "BABA",
    "美团": "3690.HK",
    "智谱": "02513.HK",
    "智谱ai": "02513.HK",
    "智谱清言": "02513.HK",
    "knowledge atlas": "02513.HK",
    "spacex": "SPCX",
    "space x": "SPCX",
}


def normalize_symbol(symbol: str) -> str:
    raw = symbol.strip()
    if not raw:
        return raw
    lowered = raw.lower()
    if lowered in CHINESE_SYMBOLS:
        return CHINESE_SYMBOLS[lowered]

    normalized = raw.upper().replace("。", ".")
    hk_match = re.fullmatch(r"(\d{1,5})\.HK", normalized)
    if hk_match:
        code = hk_match.group(1)
        return f"{code.zfill(4)}.HK" if len(code) <= 4 else f"{code}.HK"
    if re.fullmatch(r"\d{6}", normalized):
        if normalized.startswith(("6", "9")):
            return f"{normalized}.SS"
        return f"{normalized}.SZ"
    if re.fullmatch(r"\d{1,5}", normalized):
        return f"{normalized.zfill(4)}.HK"
    return normalized


def is_a_share(symbol: str) -> bool:
    normalized = normalize_symbol(symbol)
    return bool(re.fullmatch(r"\d{6}\.(SS|SZ|SH|BJ)", normalized))


def to_tushare_symbol(symbol: str) -> str:
    normalized = normalize_symbol(symbol)
    if normalized.endswith(".SS"):
        return normalized[:-3] + ".SH"
    return normalized


def to_akshare_symbol(symbol: str) -> str:
    normalized = normalize_symbol(symbol)
    return normalized.split(".", 1)[0]


def to_yahoo_symbol(symbol: str) -> str:
    """Return the Yahoo Finance query symbol for a normalized ticker.

    HK tickers are usually displayed with 4 digits, while some Chinese
    finance sites display newly listed names with a leading zero as 5 digits
    (for example Snowball 02513). Yahoo expects 2513.HK for that case.
    """
    normalized = normalize_symbol(symbol)
    if normalized.endswith(".HK"):
        code = normalized[:-3]
        if code.isdigit():
            yahoo_code = (code.lstrip("0") or "0").zfill(4)
            return f"{yahoo_code}.HK"
    return normalized


def extract_symbols(text: str) -> list[str]:
    found: list[str] = []
    lowered = text.lower()
    for name, symbol in sorted(CHINESE_SYMBOLS.items(), key=lambda item: len(item[0]), reverse=True):
        if name in lowered:
            found.append(symbol)

    for match in re.finditer(r"(?:xueqiu\.com/S/|雪球[:：]?\s*)(\d{4,5})", text, flags=re.IGNORECASE):
        found.append(normalize_symbol(match.group(1)))

    text_without_urls = re.sub(r"https?://\S+", " ", text)
    pattern = re.compile(r"\b[A-Za-z]{1,6}(?:\.[A-Za-z]{1,4})?\b|\b\d{4,6}(?:\.[A-Za-z]{1,4})?\b")
    ignored = {
        "MA", "MACD", "RSI", "PE", "EPS", "ROE", "ETF", "API", "MVP", "CSV",
        "HTTP", "HTTPS", "URL", "WWW", "COM", "AI", "AGENT", "DAY", "BUY", "SELL",
        "IPO",
    }
    for match in pattern.finditer(text_without_urls):
        token = match.group(0)
        if token.upper() in ignored:
            continue
        normalized = normalize_symbol(token)
        if normalized and normalized not in ignored:
            found.append(normalized)

    unique: list[str] = []
    for symbol in found:
        if symbol not in unique:
            unique.append(symbol)
    return unique
