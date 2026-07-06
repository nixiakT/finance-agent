"""CLI presentation helpers."""
from __future__ import annotations

import os
import sys
import unicodedata


WIDTH = 76


CAT = [
    "        |\\      _,,,---,,_",
    "  招财  /,`.-'`'    -.  ;-;;,_",
    "       |,4-  ) )-,_. ,\\ (  `'-'",
    "      '---''(_/--'  `-'\\_)",
    "          lucky market cat",
]


HELP = """
finance-agent 功能菜单

基础命令：
  /help
    显示当前功能菜单。
  /think on | /think off
    开关高层执行轨迹。显示模型是否调用工具、工具名、参数和结果摘要。
  /selfcheck 或 --selfcheck
    运行工具注册、后端和主循环自检。
  /clear
    清空当前会话上下文。
  /exit
    退出交互会话。

交互编辑：
  ↑/↓ 历史记录，←/→ 移动光标，Backspace/Delete 删除。
  Ctrl+A/E 到行首/行尾，Ctrl+U/K 删除光标前/后的内容。

股票研究：
  分析一下 AAPL 最近三个月走势，并生成投资研究摘要
  分析一下 贵州茅台 的基本面和技术面

一键命令：
  /quote AAPL
    查询行情。
  /history AAPL 1y
    查看历史价格和技术指标摘要。
  /financials AAPL
    查看基本面和估值摘要。
  /news AAPL 5
    查看相关新闻。
  /indicators AAPL 1y
    计算技术指标。
  /report AAPL 1y
    生成结构化股票研究报告。
  /compare NVDA AMD 1y
    对比多只股票。
  /debate NVDA AMD 1y
    多智能体辩论选股。
  /backtest TSLA 20 60 2y
    回测 20/60 日均线策略。
  /brief AAPL MSFT NVDA
    生成自选股简报。
  /tools
    列出已注册工具。
  /sources
    查看当前数据源优先级。
  /search 智谱 02513 股票
    搜索公开网页，用于核验标的、上市状态、公告和新闻来源。
  /fetch https://xueqiu.com/S/02513
    抓取指定网页并显示标题、描述、HTTP 状态和摘要；遇到 WAF/JS 会标注。

行情与数据：
  - 实时/准实时行情：价格、涨跌幅、成交量、市值等
  - 历史价格：K 线摘要或 CSV
  - 基本面：PE、EPS、营收、利润、现金流、ROE、利润率
  - 新闻事件：相关新闻标题、来源、时间和链接

技术指标：
  - MA5 / MA20 / MA60
  - RSI14
  - MACD
  - 年化波动率
  - 近 1 月 / 3 月 / 1 年收益率

投资框架：
  - 巴菲特/芒格：护城河、现金流、安全边际
  - 段永平：好生意、用户价值、长期主义
  - 达利欧：宏观周期、利率、组合风险

多智能体辩论：
  用多智能体辩论 NVDA 和 AMD 哪个更值得继续研究
  角色包括 Bull、Bear、Value、Macro、Risk、Judge。

策略辅助：
  帮我回测 TSLA 的 20 日均线上穿 60 日均线策略
  当前支持移动均线交叉策略回测。

自选股简报：
  生成我的自选股每日简报：AAPL, MSFT, NVDA

网页核验：
  /search 智谱 02513 股票
  /fetch https://stock.finance.sina.com.cn/hkstock/quotes/02513.html

Trace2Skill 自进化：
  可把成功任务轨迹沉淀成新的 skills/<name>/SKILL.md。

数据源：
  Alpha Vantage、Tushare、AKShare、Yahoo Finance、SAMPLE_FALLBACK。
  若数据源限流或缺失，报告会标注来源、时间和降级情况。

边界：
  本系统只做研究辅助，不做自动交易，不承诺收益，不输出确定性买卖指令。
""".strip()


def render_welcome() -> str:
    lines: list[str] = []
    lines.append(_color("╭" + "─" * WIDTH + "╮", "gold"))
    lines.append(_box_line(""))
    lines.append(_box_line(_color("FINANCE AGENT", "green")))
    lines.append(_box_line(_color("stock research · debate · strategy lab", "muted")))
    lines.append(_box_line(""))
    for row in CAT:
        lines.append(_box_line(_color(row, "gold")))
    lines.append(_box_line(""))
    lines.append(_box_line(_color("行情 · 基本面 · 新闻 · 技术指标 · 多智能体辩论 · 策略回测", "cyan")))
    lines.append(_box_line("只做研究辅助，不做自动交易，不承诺收益"))
    lines.append(_box_line(""))
    lines.append(_box_line(_color("Ask  ", "green") + "  分析一下 AAPL 最近三个月走势"))
    lines.append(_box_line(_color("Help ", "cyan") + "  /help     " + _color("Exit ", "muted") + "  /exit     " + _color("History", "muted") + "  ↑/↓"))
    lines.append(_box_line(""))
    lines.append(_color("╰" + "─" * WIDTH + "╯", "gold"))
    return "\n".join(lines)


def render_help() -> str:
    return HELP


def render_prompt() -> str:
    if not sys.stdin.isatty():
        return ""
    return _color("finance-agent", "green") + _color(" > ", "muted")


def render_trace(event: str, detail: str = "") -> str:
    prefix = _color("thinking", "muted")
    if detail:
        return f"{prefix} · {event}: {detail}"
    return f"{prefix} · {event}"


def _box_line(text: str) -> str:
    visible = _strip_ansi(text)
    padding = max(WIDTH - _display_width(visible), 0)
    left = padding // 2
    right = padding - left
    return _color("│", "gold") + " " * left + text + " " * right + _color("│", "gold")


def _color(text: str, name: str) -> str:
    if not _should_color():
        return text
    colors = {
        "gold": "\033[38;5;220m",
        "green": "\033[38;5;82m",
        "cyan": "\033[38;5;80m",
        "muted": "\033[38;5;245m",
    }
    reset = "\033[0m"
    return f"{colors.get(name, '')}{text}{reset}"


def _should_color() -> bool:
    if os.environ.get("NO_COLOR"):
        return False
    if os.environ.get("FORCE_COLOR"):
        return True
    return sys.stdout.isatty()


def _strip_ansi(text: str) -> str:
    out = []
    i = 0
    while i < len(text):
        if text[i:i + 2] == "\033[":
            i += 2
            while i < len(text) and text[i] != "m":
                i += 1
            i += 1
            continue
        out.append(text[i])
        i += 1
    return "".join(out)


def _display_width(text: str) -> int:
    width = 0
    for char in text:
        width += 2 if unicodedata.east_asian_width(char) in {"F", "W"} else 1
    return width
