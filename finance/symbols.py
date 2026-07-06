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
}


def normalize_symbol(symbol: str) -> str:
    raw = symbol.strip()
    if not raw:
        return raw
    lowered = raw.lower()
    if lowered in CHINESE_SYMBOLS:
        return CHINESE_SYMBOLS[lowered]

    normalized = raw.upper().replace("。", ".")
    if re.fullmatch(r"\d{6}", normalized):
        if normalized.startswith(("6", "9")):
            return f"{normalized}.SS"
        return f"{normalized}.SZ"
    if re.fullmatch(r"\d{4,5}", normalized):
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


def extract_symbols(text: str) -> list[str]:
    found: list[str] = []
    lowered = text.lower()
    for name, symbol in CHINESE_SYMBOLS.items():
        if name in lowered:
            found.append(symbol)

    pattern = re.compile(r"\b[A-Za-z]{1,6}(?:\.[A-Za-z]{1,4})?\b|\b\d{4,6}(?:\.[A-Za-z]{1,4})?\b")
    ignored = {
        "MA", "MACD", "RSI", "PE", "EPS", "ROE", "ETF", "API", "MVP", "CSV",
        "HTTP", "URL", "AI", "AGENT", "DAY", "BUY", "SELL",
    }
    for match in pattern.finditer(text):
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
