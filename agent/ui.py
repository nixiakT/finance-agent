"""CLI presentation helpers."""
from __future__ import annotations

import os
import sys
import unicodedata
from datetime import datetime
from pathlib import Path

from config import load_local_env


WIDTH = 82


LOGO = [
    "┌────────── 招财进宝 ──────────┐",
    "│        /\\_/\\      HK US CN   │",
    "│       (  o.o )    MA RSI PE  │",
    "│        >  ^  <    DATA NEWS  │",
    "│      /|   金   |\\            │",
    "│     /_|___融___|_\\           │",
    "│        /   |   \\             │",
    "│       /____|____\\            │",
    "├────────── Research ──────────┤",
    "│ model                        │",
    "{model_row}",
    "│                              │",
    "│ mode                         │",
    "│ research only                │",
    "│ no auto trading              │",
    "│ facts · inference · risk     │",
    "└──────────────────────────────┘",
]

PANEL_ROWS = [
    ("Available Tools", ""),
    ("finance", "quote, history, financials, news"),
    ("analysis", "indicators, report, compare"),
    ("agents", "debate, risk, value, macro"),
    ("strategy", "backtest, brief, trace2skill"),
    ("web", "search, fetch, source check"),
    ("", ""),
    ("Market Sources", ""),
    ("quotes", "Yahoo Finance, Alpha Vantage"),
    ("A-share", "Tushare, AKShare"),
    ("fallback", "sample data is clearly marked"),
    ("", ""),
    ("Commands", ""),
    ("/help", "menu and examples"),
    ("/think on", "show high-level tool trace"),
    ("/search 智谱 02513", "verify listing pages"),
    ("/quote AAPL", "fast market snapshot"),
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
    title = " Finance Agent v0.3.0 · stock research workspace "
    lines.append(_color(_top_border(title), "gold"))
    logo = _logo_rows()
    body_rows = max(len(logo), len(PANEL_ROWS))
    for index in range(body_rows):
        left = logo[index] if index < len(logo) else ""
        label, value = PANEL_ROWS[index] if index < len(PANEL_ROWS) else ("", "")
        lines.append(_panel_line(left, _right_cell(label, value)))
    lines.append(_panel_line("", ""))
    lines.append(_panel_line(_muted(str(Path.cwd())), _right_cell("Session", _session_id())))
    lines.append(_panel_line(_muted("research only · no auto trading"), _right_cell("Boundary", "facts, inference, risk")))
    lines.append(_panel_line("", ""))
    lines.append(_panel_line(_accent("Ask") + "  分析一下 AAPL 最近三个月走势", _accent("/help") + " commands  " + _muted("↑/↓ history")))
    lines.append(_color("╰" + "─" * WIDTH + "╯", "gold"))
    lines.append("")
    lines.append(_accent("Welcome to Finance Agent.") + " Type your message or /help for commands.")
    lines.append(_muted("Tip: 数据优先标注来源和时间；SAMPLE_FALLBACK 只用于演示。"))
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


def _top_border(title: str) -> str:
    title_width = _display_width(title)
    inner_width = WIDTH
    remaining = max(inner_width - title_width, 0)
    left = remaining // 2
    right = remaining - left
    return "╭" + "─" * left + title + "─" * right + "╮"


def _panel_line(left: str, right: str) -> str:
    left_width = 35
    right_width = WIDTH - left_width - 2
    left_text = _truncate_display(left, left_width)
    right_text = _truncate_display(right, right_width)
    left_text = _pad_display(left_text, left_width)
    right_text = _pad_display(right_text, right_width)
    return (
        _color("│", "gold")
        + " "
        + _color(left_text, "gold")
        + " "
        + right_text
        + _color("│", "gold")
    )


def _right_cell(label: str, value: str) -> str:
    if not label and not value:
        return ""
    if value:
        return _accent(label + ": ") + value
    return _accent(label)


def _accent(text: str) -> str:
    return _color(text, "cyan")


def _muted(text: str) -> str:
    return _color(text, "muted")


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


def _pad_display(text: str, width: int) -> str:
    return text + " " * max(width - _display_width(text), 0)


def _truncate_display(text: str, width: int) -> str:
    clean_width = _display_width(_strip_ansi(text))
    if clean_width <= width:
        return text
    visible = ""
    used = 0
    for char in _strip_ansi(text):
        char_width = 2 if unicodedata.east_asian_width(char) in {"F", "W"} else 1
        if used + char_width > max(width - 1, 0):
            break
        visible += char
        used += char_width
    return visible + "…"


def _session_id() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def _logo_rows() -> list[str]:
    load_local_env()
    model = os.environ.get("DEEPSEEK_MODEL", "model not configured")
    rows = []
    for row in LOGO:
        if row == "{model_row}":
            rows.append(_logo_box_row(model))
        else:
            rows.append(row)
    return rows


def _logo_box_row(text: str) -> str:
    content_width = 30
    content = _truncate_display(text, content_width - 2)
    content = _pad_display(content, content_width - 2)
    return "│ " + content + " │"
