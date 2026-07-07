"""Interactive slash commands."""
from __future__ import annotations

import shlex
from dataclasses import dataclass
from typing import Callable

from finance.agent import FinanceResearchAgent
from finance.web import web_fetch, web_search
from tools.base import ToolRegistry


@dataclass
class CommandResult:
    handled: bool
    output: str = ""
    exit: bool = False
    clear: bool = False
    selfcheck: bool = False
    think: bool | None = None


class CommandRouter:
    def __init__(
        self,
        registry: ToolRegistry,
        finance_agent: FinanceResearchAgent | None = None,
        trace: Callable[[str, str], None] | None = None,
    ):
        self.registry = registry
        self.finance = finance_agent or FinanceResearchAgent()
        self.trace = trace

    def handle(self, raw: str, think_enabled: bool = False) -> CommandResult:
        text = raw.strip()
        if not text.startswith("/"):
            return CommandResult(False)
        try:
            parts = shlex.split(text)
        except ValueError as exc:
            return CommandResult(True, f"命令解析失败：{exc}")
        if not parts:
            return CommandResult(False)

        command = parts[0].lower()
        args = parts[1:]
        if command in {"/exit", "/quit"}:
            return CommandResult(True, exit=True)
        if command == "/clear":
            return CommandResult(True, clear=True, output="已清空当前会话上下文。")
        if command == "/selfcheck":
            return CommandResult(True, selfcheck=True)
        if command == "/think":
            return self._think(args, think_enabled)
        if command == "/tools":
            return CommandResult(True, self._tools())
        if command == "/sources":
            return CommandResult(True, self._sources())
        if command == "/search":
            try:
                return CommandResult(True, self._search(args))
            except ValueError as exc:
                return CommandResult(True, str(exc))
        if command == "/fetch":
            try:
                return CommandResult(True, self._fetch(args))
            except ValueError as exc:
                return CommandResult(True, str(exc))

        finance_commands = {
            "/quote": self._quote,
            "/history": self._history,
            "/financials": self._financials,
            "/news": self._news,
            "/indicators": self._indicators,
            "/report": self._report,
            "/compare": self._compare,
            "/debate": self._debate,
            "/backtest": self._backtest,
            "/brief": self._brief,
        }
        if command in finance_commands:
            try:
                return CommandResult(True, finance_commands[command](args))
            except ValueError as exc:
                return CommandResult(True, str(exc))
        return CommandResult(True, f"未知命令：{command}\n输入 /help 查看可用命令。")

    def _quote(self, args: list[str]) -> str:
        symbol = _require_arg(args, "/quote AAPL")
        self._trace_tool("finance_get_quote", {"symbol": symbol})
        return self._with_result_trace("finance_get_quote", self.finance.get_quote(symbol))

    def _history(self, args: list[str]) -> str:
        symbol = _require_arg(args, "/history AAPL [period]")
        period = args[1] if len(args) > 1 else "1y"
        self._trace_tool("finance_get_price_history", {"symbol": symbol, "period": period})
        return self._with_result_trace("finance_get_price_history", self.finance.get_price_history(symbol, period))

    def _financials(self, args: list[str]) -> str:
        symbol = _require_arg(args, "/financials AAPL")
        self._trace_tool("finance_get_financials", {"symbol": symbol})
        return self._with_result_trace("finance_get_financials", self.finance.get_financials(symbol))

    def _news(self, args: list[str]) -> str:
        symbol = _require_arg(args, "/news AAPL [limit]")
        limit = int(args[1]) if len(args) > 1 and args[1].isdigit() else 5
        self._trace_tool("finance_get_news", {"symbol": symbol, "limit": limit})
        return self._with_result_trace("finance_get_news", self.finance.get_news(symbol, limit))

    def _indicators(self, args: list[str]) -> str:
        symbol = _require_arg(args, "/indicators AAPL [period]")
        period = args[1] if len(args) > 1 else "1y"
        self._trace_tool("finance_calculate_indicators", {"symbol": symbol, "period": period})
        return self._with_result_trace("finance_calculate_indicators", self.finance.calculate_indicators(symbol, period))

    def _report(self, args: list[str]) -> str:
        symbol = _require_arg(args, "/report AAPL [period]")
        period = args[1] if len(args) > 1 else "1y"
        self._trace_tool("finance_generate_report", {"symbol": symbol, "period": period})
        return self._with_result_trace("finance_generate_report", self.finance.generate_report(symbol, period))

    def _compare(self, args: list[str]) -> str:
        symbols = _require_many(args, "/compare NVDA AMD [period]")
        period = _period_arg(args[-1])
        if period:
            symbols = args[:-1]
        else:
            period = "1y"
        self._trace_tool("finance_compare_stocks", {"symbols": symbols, "period": period})
        return self._with_result_trace("finance_compare_stocks", self.finance.compare_stocks(symbols, period))

    def _debate(self, args: list[str]) -> str:
        symbols = _require_many(args, "/debate NVDA AMD [period]")
        period = _period_arg(args[-1])
        if period:
            symbols = args[:-1]
        else:
            period = "1y"
        self._trace_tool("finance_debate_stocks", {"symbols": symbols, "period": period})
        return self._with_result_trace("finance_debate_stocks", self.finance.debate_stocks(symbols, period))

    def _backtest(self, args: list[str]) -> str:
        symbol = _require_arg(args, "/backtest TSLA 20 60 [period]")
        fast = int(args[1]) if len(args) > 1 and args[1].isdigit() else None
        slow = int(args[2]) if len(args) > 2 and args[2].isdigit() else None
        period = args[3] if len(args) > 3 else "2y"
        strategy = f"{fast or 20} 日均线上穿 {slow or 60} 日均线策略"
        self._trace_tool("finance_backtest_strategy", {
            "symbol": symbol,
            "strategy": strategy,
            "period": period,
        })
        return self._with_result_trace(
            "finance_backtest_strategy",
            self.finance.backtest_strategy(symbol, strategy, period, fast, slow),
        )

    def _brief(self, args: list[str]) -> str:
        symbols = _require_many(args, "/brief AAPL MSFT NVDA")
        self._trace_tool("finance_daily_brief", {"symbols": symbols})
        return self._with_result_trace("finance_daily_brief", self.finance.daily_brief(symbols))

    def _tools(self) -> str:
        names = self.registry.names()
        return "已注册工具：\n" + "\n".join(f"- {name}" for name in names)

    def _sources(self) -> str:
        diagnostics = self.finance.provider.diagnostics()
        lines = ["当前数据源状态："]
        for index, row in enumerate(diagnostics, start=1):
            detail = f" - {row['detail']}" if row.get("detail") else ""
            lines.append(f"{index}. {row['name']}: {row['status']}{detail}")
        return "\n".join(lines)

    def _search(self, args: list[str]) -> str:
        query = " ".join(args).strip()
        if not query:
            raise ValueError("用法：/search 智谱 02513 股票")
        self._trace_tool("web_search", {"query": query, "limit": 5})
        return self._with_result_trace("web_search", web_search(query, 5))

    def _fetch(self, args: list[str]) -> str:
        url = _require_arg(args, "/fetch https://xueqiu.com/S/02513")
        self._trace_tool("web_fetch", {"url": url})
        return self._with_result_trace("web_fetch", web_fetch(url))

    def _think(self, args: list[str], think_enabled: bool) -> CommandResult:
        if not args:
            state = "on" if think_enabled else "off"
            return CommandResult(True, f"thinking 当前状态：{state}")
        value = args[0].lower()
        if value in {"on", "true", "1"}:
            return CommandResult(True, "thinking 已开启：会显示高层执行轨迹和工具调用。", think=True)
        if value in {"off", "false", "0"}:
            return CommandResult(True, "thinking 已关闭。", think=False)
        return CommandResult(True, "用法：/think on 或 /think off")

    def _trace_tool(self, name: str, arguments: dict) -> None:
        if self.trace:
            self.trace("tool", f"{name} {arguments}")

    def _with_result_trace(self, name: str, output: str) -> str:
        if self.trace:
            self.trace("tool result", f"{name} -> {_preview(output)}")
        return output


def _require_arg(args: list[str], usage: str) -> str:
    if not args:
        raise ValueError(f"用法：{usage}")
    return args[0]


def _require_many(args: list[str], usage: str) -> list[str]:
    if not args:
        raise ValueError(f"用法：{usage}")
    return args


def _period_arg(value: str) -> str:
    normalized = value.lower()
    return normalized if normalized in {"1mo", "3mo", "6mo", "1y", "2y", "5y"} else ""


def _preview(text: str, limit: int = 180) -> str:
    clean = " ".join(str(text).split())
    if len(clean) <= limit:
        return clean
    return clean[:limit] + "..."
