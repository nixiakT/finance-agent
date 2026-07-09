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
    ("╭────────── 招财进宝符 ───────────╮", "red"),
    ("│    ◌    ✦     ◌     ✦    ◌      │", "gold"),
    ("│          /\\_______/\\            │", "white"),
    ("│      ___(  ◠   ◠  )___          │", "white"),
    ("│    .'    \\   ᴗ   /    `.        │", "white"),
    ("│   /   ╭─╮\\_____/╭─╮   \\         │", "gold"),
    ("│  |    │ │  ___  │ │    |        │", "white"),
    ("│  |    │ │ (___) │ │    |        │", "white"),
    ("│   \\   ╰─╯\\___/╰─╯   /           │", "white"),
    ("│    `-.    /   \\    .-'          │", "gold"),
    ("│       (  o ) ( o  )             │", "white"),
    ("│      ◢████████████◣             │", "red"),
    ("│     ═══╧════════╧═══            │", "red"),
    ("╰─────────────────────────────────╯", "gold"),
    ("model", "muted"),
    ("{model_row}", "muted"),
    ("research only", "gold"),
    ("facts · inference · risk", "muted"),
    ("no auto trading", "red"),
]

PANEL_ROWS = [
    ("Available Tools", ""),
    ("finance", "quote, history, financials, news"),
    ("analysis", "indicators, report, compare"),
    ("agents", "debate, risk, value, macro"),
    ("strategy", "backtest, brief, trace2skill"),
    ("web", "search, fetch, source check"),
    ("wechat", "status, send, report outbox"),
    ("memory", "preference, correction, evolve"),
    ("prediction", "ledger, scorecard, review"),
    ("portfolio", "paper account, allocation, PnL"),
    ("learning", "history patterns, skill update"),
    ("schedule", "wechat brief, due runner"),
    ("", ""),
    ("Market Sources", ""),
    ("quotes", "Yahoo Finance, Alpha Vantage"),
    ("A-share", "Tushare, AKShare"),
    ("fallback", "sample data is clearly marked"),
    ("", ""),
    ("Commands", ""),
    ("/help", "menu and examples"),
    ("/status", "model, sources, tools"),
    ("/think on", "expand execution trace"),
    ("/quality AAPL", "research quality gate"),
]


HELP = """
finance-agent 功能菜单

基础命令：
  /help
    显示当前功能菜单。
  /think on | /think compact | /think off
    切换高层执行轨迹。默认 compact 折叠成一行摘要；on 展开详情；off 完全隐藏。
    这里只展示可审计的执行摘要，不展示隐藏推理链。
  /trace
    展开上一轮任务的详细 thinking 轨迹。
  /lang zh | /lang en
    切换 CLI 交互语言。也可以设置 FINANCE_AGENT_LANG=zh 或 en。
  /selfcheck 或 --selfcheck
    运行工具注册、后端和主循环自检。
  /status
    显示模型、base URL、工具数、数据源、thinking 状态和 License。
  /proxy status | /proxy test | /proxy set http://127.0.0.1:7897 | /proxy off
    查看、测试、临时设置或关闭网页/行情查询代理。
  /wechat status | /wechat send <内容> | /wechat send-md <markdown>
    查看微信连接状态，或把报告/简报发送到微信连接器。未配置 webhook 时写入本地 outbox。
  /memory list | /memory add <内容>
    查看或新增金融研究偏好、纠错、数据源经验和风险规则。
  /evolve <复盘/纠错/成功轨迹>
    把金融研究经验沉淀为本地 memory，并更新 finance-research-evolution Skill。
  /predict record AAPL up 30 0.65 <理由> | /predict list | /predict eval [all] | /predict learn [save]
    记录方向预测、查看预测账本、到期评分，并按历史命中率生成复盘；加 save 会写入金融记忆。
  /portfolio init 1000000 AAPL MSFT NVDA | /portfolio review GOOGL AVGO | /portfolio mark | /portfolio sell AAPL all | /portfolio trades | /portfolio rebalance AAPL MSFT NVDA
    创建 100 万纸面投资账户；之后可每日估值、诊断弱持仓/替换候选、模拟卖出、查看交易流水和再平衡。
  /learn-history AAPL 2y 20
    从历史 K 线学习可解释预测规则，写入预测账本，并更新 finance-history-learning Skill。
  /schedule list | /schedule brief AAPL,MSFT,NVDA [interval_minutes] | /schedule portfolio [name] [interval_minutes] | /schedule run
    创建微信定时简报或组合每日估值任务，或执行到期任务。适合配合 cron 定时调用。
  /mcp
    显示已透明并入主循环的 MCP 工具。
  /security
    显示权限分层、危险命令拦截和不可信内容隔离策略。
  /clear
    清空当前会话上下文。
  /compact
    用模型生成交接摘要压缩当前会话历史，保留最近上下文。
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
  /resolve minimax
    解析公司名、简称、中文名、英文名或 ticker，返回 A 股/港股/美股候选代码。
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
  /export-report AAPL 3mo reports/aapl.md
    生成结构化股票研究报告并保存为 Markdown 文件。
  /quality AAPL 1y
    运行研究质量门禁和去劣初筛，输出信息丰富度、数据缺口、快速否决/重审信号和下一步核验。
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
  /mcp
    查看 MCP 工具，例如 mcp__echo。
  /security
    查看安全层策略。
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
  /resolve minimax
  /search 智谱 02513 股票
  /fetch https://stock.finance.sina.com.cn/hkstock/quotes/02513.html

Trace2Skill 自进化：
  可把成功任务轨迹沉淀成新的 skills/<name>/SKILL.md。

Finance Memory 自进化：
  /memory add 以后分析港股先核验展示代码和 Yahoo 查询代码差异
  /evolve SpaceX 查询必须先解析 SPCX，再核验行情和新闻，不能用旧知识判断未上市

预测评分闭环：
  /predict record AAPL up 30 0.65 服务收入和回购支撑
  /predict eval all
  /predict learn save

微信定时推送：
  /schedule brief AAPL,MSFT,NVDA 1440
  /schedule run

研究质量门禁：
  - 信息丰富度 A/B/C
  - 数据完整性和来源风险
  - 快速否决/重审信号
  - 下一步核验清单

数据源：
  Alpha Vantage、Tushare、AKShare、Yahoo Finance、SAMPLE_FALLBACK。
  若数据源限流或缺失，报告会标注来源、时间和降级情况。

边界：
  本系统只做研究辅助，不做自动交易，不承诺收益，不输出确定性买卖指令。
""".strip()


HELP_EN = """
finance-agent command menu

Basics:
  /help
    Show this menu.
  /lang zh | /lang en
    Switch CLI language for the current process.
  /think on | /think compact | /think off
    Toggle visible high-level execution trace. compact folds details into one summary line; on expands details; off hides it.
  /trace
    Expand the detailed thinking trace from the last task.
  /status
    Show model, base URL, proxy, tool count, data sources, thinking state and License.
  /proxy status | /proxy test | /proxy set http://127.0.0.1:7897 | /proxy off
    Inspect, test or set the HTTP proxy used by market/web lookup calls.
  /wechat status | /wechat send <message> | /wechat send-md <markdown>
    Inspect the WeChat connector or send reports. Without a webhook it writes to a local outbox.
  /memory list | /memory add <note>
    Inspect or add finance preferences, corrections, source notes and risk rules.
  /evolve <review/correction/trace>
    Save finance learning to memory and update the finance-research-evolution Skill.
  /predict record AAPL up 30 0.65 <thesis> | /predict list | /predict eval [all] | /predict learn [save]
    Record directional forecasts and score them later against realized prices.
  /portfolio init 1000000 AAPL MSFT NVDA | /portfolio review GOOGL AVGO | /portfolio mark | /portfolio sell AAPL all | /portfolio trades | /portfolio rebalance AAPL MSFT NVDA
    Create a paper account, diagnose weak holdings/replacements, mark daily, simulate sells, inspect trades, and rebalance. It never sends real orders.
  /learn-history AAPL 2y 20
    Learn explainable forecast rules from historical candles, record the forecast, and update finance-history-learning Skill.
  /schedule list | /schedule brief AAPL,MSFT,NVDA [interval_minutes] | /schedule portfolio [name] [interval_minutes] | /schedule run
    Schedule WeChat briefs or portfolio marks and execute due jobs, usually from cron.
  /mcp
    Show MCP tools merged into the agent loop.
  /security
    Show permission and prompt-injection safety policy.
  /clear
    Clear session context.
  /compact
    Summarize older conversation history with the model and keep recent context.
  /exit
    Exit interactive mode.

Research commands:
  /resolve spacex
    Resolve company name or ticker across US/HK/A-share markets.
  /quote SPCX
    Get quote snapshot.
  /history AAPL 1y
    Price history and indicator summary.
  /financials AAPL
    Fundamentals and valuation summary.
  /news AAPL 5
    Related news.
  /report AAPL 1y
    Structured stock research report.
  /export-report AAPL 3mo reports/aapl.md
    Generate a structured stock research report and save it as a Markdown file.
  /quality AAPL 1y
    Research quality gate: information grade, data gaps, red flags and next checks.
  /compare NVDA AMD 1y
    Compare stocks.
  /debate NVDA AMD 1y
    Multi-agent stock debate.
  /backtest TSLA 20 60 2y
    Backtest MA crossover strategy.
  /brief AAPL MSFT NVDA
    Watchlist brief.
  /search SpaceX SPCX IPO
    Public web verification.
  /fetch https://example.com
    Fetch a URL and summarize it.
  /wechat send-md # AAPL brief
    Send a report to the configured connector or local outbox.
  /predict record SPCX down 30 0.55 valuation reset risk
    Save a measurable forecast for future scoring.

Boundary:
  Research only. No auto trading, no return promises, no deterministic buy/sell instructions.
""".strip()


def render_welcome() -> str:
    lines: list[str] = []
    title = " Finance Agent v0.3.1 · stock research workspace "
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
    ask = "Analyze AAPL over the last 3 months" if current_lang() == "en" else "分析一下 AAPL 最近三个月走势"
    lines.append(_panel_line(_accent("Ask") + "  " + ask, _accent("/help") + " commands  " + _muted("↑/↓ history")))
    lines.append(_color("╰" + "─" * WIDTH + "╯", "gold"))
    lines.append("")
    if current_lang() == "en":
        lines.append(_accent("Welcome to Finance Agent.") + " Type your message or /help for commands.")
        lines.append(_muted("Tip: reports label source/time; SAMPLE_FALLBACK is demo-only."))
    else:
        lines.append(_accent("Welcome to Finance Agent.") + " Type your message or /help for commands.")
        lines.append(_muted("Tip: 数据优先标注来源和时间；SAMPLE_FALLBACK 只用于演示。"))
    return "\n".join(lines)


def render_help() -> str:
    return HELP_EN if current_lang() == "en" else HELP


def render_prompt() -> str:
    if not sys.stdin.isatty():
        return ""
    return _color("finance-agent", "green") + _color(" > ", "muted")


def render_trace(
    event: str,
    detail: str = "",
    *,
    elapsed: float | None = None,
    timestamp: str | None = None,
) -> str:
    clock = timestamp or datetime.now().strftime("%H:%M:%S")
    elapsed_part = ""
    if elapsed is not None:
        elapsed_part = " " + _color("+" + _format_elapsed(elapsed), "gold")
    prefix = f"{_color('thinking', 'muted')} {_muted(clock)}{elapsed_part}"
    if detail:
        return f"{prefix} · {event}: {_trace_detail(detail)}"
    return f"{prefix} · {event}"


def render_trace_summary(
    steps: int,
    tools: list[str],
    *,
    elapsed: float | None = None,
) -> str:
    elapsed_part = f" · {_format_elapsed(elapsed)}" if elapsed is not None else ""
    tool_count = len(tools)
    tool_label = "tool" if tool_count == 1 else "tools"
    tool_part = ", ".join(tools[:4])
    if len(tools) > 4:
        tool_part += f", +{len(tools) - 4}"
    if tool_part:
        tool_part = f" · {tool_part}"
    return f"{_color('thinking summary', 'muted')} · {steps} steps · {tool_count} {tool_label}{elapsed_part}{tool_part}"


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
        + left_text
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
        "red": "\033[38;5;203m",
        "white": "\033[38;5;255m",
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
    return text + " " * max(width - _display_width(_strip_ansi(text)), 0)


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


def current_lang() -> str:
    load_local_env()
    value = os.environ.get("FINANCE_AGENT_LANG", "zh").strip().lower()
    return "en" if value.startswith("en") else "zh"


def _format_elapsed(seconds: float) -> str:
    if seconds < 10:
        return f"{seconds:.2f}s"
    if seconds < 60:
        return f"{seconds:.1f}s"
    minutes = int(seconds // 60)
    remaining = seconds - minutes * 60
    return f"{minutes}m{remaining:.0f}s"


def _trace_detail(detail: str, width: int = 220) -> str:
    compact = " ".join(str(detail).split())
    return _truncate_display(compact, width)


def _logo_rows() -> list[str]:
    load_local_env()
    model = os.environ.get("DEEPSEEK_MODEL", "model not configured")
    rows = []
    for row, color in LOGO:
        if row == "{model_row}":
            rows.append(_color(_truncate_display(model, 35), color))
        else:
            rows.append(_color(row, color))
    return rows
