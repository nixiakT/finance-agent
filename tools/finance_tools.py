"""Finance tools for stock research."""
from __future__ import annotations

from .base import Tool
from finance.agent import FinanceResearchAgent


_agent = FinanceResearchAgent()


def _route_task(task: str) -> str:
    return _agent.route_task(task)


def _get_quote(symbol: str) -> str:
    return _agent.get_quote(symbol)


def _resolve_symbol(query: str, limit: int = 8) -> str:
    return _agent.resolve_symbol(query, limit)


def _get_price_history(symbol: str, period: str = "1y", format: str = "summary") -> str:
    return _agent.get_price_history(symbol, period, format)


def _get_financials(symbol: str) -> str:
    return _agent.get_financials(symbol)


def _get_news(symbol: str, limit: int = 5) -> str:
    return _agent.get_news(symbol, limit)


def _calculate_indicators(symbol: str, period: str = "1y") -> str:
    return _agent.calculate_indicators(symbol, period)


def _generate_report(symbol: str, period: str = "1y") -> str:
    return _agent.generate_report(symbol, period)


def _compare_stocks(symbols: list[str] | str, period: str = "1y") -> str:
    return _agent.compare_stocks(symbols, period)


def _debate_stocks(symbols: list[str] | str, period: str = "1y") -> str:
    return _agent.debate_stocks(symbols, period)


def _backtest_strategy(
    symbol: str,
    strategy: str = "",
    period: str = "2y",
    fast_window: int | None = None,
    slow_window: int | None = None,
    initial_cash: float = 100_000,
) -> str:
    return _agent.backtest_strategy(symbol, strategy, period, fast_window, slow_window, initial_cash)


def _daily_brief(symbols: list[str] | str, period: str = "3mo") -> str:
    return _agent.daily_brief(symbols, period)


finance_route_task_tool = Tool(
    name="finance_route_task",
    description="根据自然语言金融任务自动选择报告、对比、辩论、回测或自选股简报。",
    parameters={
        "type": "object",
        "properties": {"task": {"type": "string", "description": "用户的完整金融研究任务"}},
        "required": ["task"],
    },
    run=_route_task,
)

finance_get_quote_tool = Tool(
    name="finance_get_quote",
    description="获取股票实时/准实时行情；返回价格、涨跌、成交量、数据源和时间。",
    parameters={
        "type": "object",
        "properties": {"symbol": {"type": "string", "description": "股票代码，如 AAPL、NVDA、600519 或 贵州茅台"}},
        "required": ["symbol"],
    },
    run=_get_quote,
)

finance_resolve_symbol_tool = Tool(
    name="finance_resolve_symbol",
    description="把公司名、简称、中文名、英文名或 ticker 解析为可交易股票代码，覆盖 A 股、港股和美股候选。",
    parameters={
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "公司名、简称、中文名、英文名或 ticker"},
            "limit": {"type": "integer", "description": "候选数量，默认 8"},
        },
        "required": ["query"],
    },
    run=_resolve_symbol,
)

finance_get_price_history_tool = Tool(
    name="finance_get_price_history",
    description="获取股票历史价格并返回摘要或 CSV。",
    parameters={
        "type": "object",
        "properties": {
            "symbol": {"type": "string"},
            "period": {"type": "string", "description": "时间范围，如 3mo、1y、2y"},
            "format": {"type": "string", "description": "summary 或 csv"},
        },
        "required": ["symbol"],
    },
    run=_get_price_history,
)

finance_get_financials_tool = Tool(
    name="finance_get_financials",
    description="获取股票基本面和估值摘要。",
    parameters={"type": "object", "properties": {"symbol": {"type": "string"}}, "required": ["symbol"]},
    run=_get_financials,
)

finance_get_news_tool = Tool(
    name="finance_get_news",
    description="获取股票相关新闻摘要和链接。",
    parameters={
        "type": "object",
        "properties": {"symbol": {"type": "string"}, "limit": {"type": "integer"}},
        "required": ["symbol"],
    },
    run=_get_news,
)

finance_calculate_indicators_tool = Tool(
    name="finance_calculate_indicators",
    description="计算 MA5/MA20/MA60、RSI、MACD、波动率和收益率等技术指标。",
    parameters={
        "type": "object",
        "properties": {"symbol": {"type": "string"}, "period": {"type": "string"}},
        "required": ["symbol"],
    },
    run=_calculate_indicators,
)

finance_generate_report_tool = Tool(
    name="finance_generate_report",
    description="生成结构化股票研究报告，包含价格、基本面、技术面、新闻、风险和结论。",
    parameters={
        "type": "object",
        "properties": {"symbol": {"type": "string"}, "period": {"type": "string"}},
        "required": ["symbol"],
    },
    run=_generate_report,
)

finance_compare_stocks_tool = Tool(
    name="finance_compare_stocks",
    description="比较多只股票的估值、基本面、技术指标和风险。",
    parameters={
        "type": "object",
        "properties": {
            "symbols": {
                "oneOf": [
                    {"type": "array", "items": {"type": "string"}},
                    {"type": "string"},
                ]
            },
            "period": {"type": "string"},
        },
        "required": ["symbols"],
    },
    run=_compare_stocks,
)

finance_debate_stocks_tool = Tool(
    name="finance_debate_stocks",
    description="让多头、空头、价值、宏观、风险和裁判 Agent 对股票池进行辩论选股。",
    parameters={
        "type": "object",
        "properties": {
            "symbols": {
                "oneOf": [
                    {"type": "array", "items": {"type": "string"}},
                    {"type": "string"},
                ]
            },
            "period": {"type": "string"},
        },
        "required": ["symbols"],
    },
    run=_debate_stocks,
)

finance_backtest_strategy_tool = Tool(
    name="finance_backtest_strategy",
    description="回测移动均线类策略，支持从自然语言策略描述中提取窗口参数。",
    parameters={
        "type": "object",
        "properties": {
            "symbol": {"type": "string"},
            "strategy": {"type": "string"},
            "period": {"type": "string"},
            "fast_window": {"type": "integer"},
            "slow_window": {"type": "integer"},
            "initial_cash": {"type": "number"},
        },
        "required": ["symbol"],
    },
    run=_backtest_strategy,
)

finance_daily_brief_tool = Tool(
    name="finance_daily_brief",
    description="为自选股生成每日简报。",
    parameters={
        "type": "object",
        "properties": {
            "symbols": {
                "oneOf": [
                    {"type": "array", "items": {"type": "string"}},
                    {"type": "string"},
                ]
            },
            "period": {"type": "string"},
        },
        "required": ["symbols"],
    },
    run=_daily_brief,
)


finance_tools = [
    finance_route_task_tool,
    finance_resolve_symbol_tool,
    finance_get_quote_tool,
    finance_get_price_history_tool,
    finance_get_financials_tool,
    finance_get_news_tool,
    finance_calculate_indicators_tool,
    finance_generate_report_tool,
    finance_compare_stocks_tool,
    finance_debate_stocks_tool,
    finance_backtest_strategy_tool,
    finance_daily_brief_tool,
]
