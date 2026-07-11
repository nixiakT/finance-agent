"""Compact, terminal-width-aware CLI presentation helpers."""
from __future__ import annotations

import os
import shutil
import sys
import unicodedata
from datetime import datetime

from agent.command_catalog import specs_by_category
from config import load_local_env


def render_welcome(width: int | None = None) -> str:
    """Render a short launch panel that fits the current terminal."""
    frame_width = _terminal_width(width)
    inner = frame_width - 2
    load_local_env()
    model = os.environ.get("DEEPSEEK_MODEL", "not configured")
    rows = [
        _frame_title(" Finance Agent · stock research ", inner),
        _frame_line(f"ฅ^•ﻌ•^ฅ  model {model}", inner),
        _frame_line("data  Yahoo · AKShare · optional Alpha Vantage/Tushare", inner),
        _frame_line("boundary  research only · facts / inference / risk · no auto trading", inner),
        _frame_line("", inner),
    ]
    if current_lang() == "en":
        rows.extend([
            _frame_line("Try   Analyze AAPL over the last 3 months", inner),
            _frame_line("Help  /help    Status  /status    Trace  /think on", inner),
        ])
    else:
        rows.extend([
            _frame_line("试试  分析一下 AAPL 最近三个月走势", inner),
            _frame_line("帮助  /help    状态  /status    轨迹  /think on", inner),
        ])
    rows.append(_color("╰" + "─" * inner + "╯", "gold"))
    return "\n".join(rows)


def render_help(width: int | None = None) -> str:
    """Render concise help from the shared command catalog."""
    lang = current_lang()
    budget = _terminal_width(width)
    labels = {
        "session": ("会话与状态", "Session"),
        "research": ("股票研究", "Research"),
        "workflow": ("工作流", "Workflow"),
    }
    lines = ["finance-agent 功能菜单" if lang == "zh" else "finance-agent command menu", ""]
    usage_width = min(42, max(20, budget // 2))
    desc_width = max(budget - usage_width - 4, 12)
    for category, specs in specs_by_category().items():
        zh, en = labels.get(category, (category, category))
        lines.append(f"[{zh if lang == 'zh' else en}]")
        for spec in specs:
            description = spec.description_zh if lang == "zh" else spec.description_en
            if budget < 44:
                lines.append("  " + _truncate_display(spec.usage, max(budget - 2, 1)))
                lines.append("    " + _truncate_display(description, max(budget - 4, 1)))
            else:
                usage = _truncate_display(spec.usage, usage_width)
                description = _truncate_display(description, desc_width)
                lines.append(f"  {_pad_display(usage, usage_width)}  {description}".rstrip())
        lines.append("")
    lines.append(
        "输入 / 后可模糊补全；↑/↓ 查看历史；/trace 展开上一轮轨迹。"
        if lang == "zh"
        else "Type / for fuzzy completion; use ↑/↓ for history and /trace for the last trace."
    )
    return "\n".join(_truncate_display(line, budget) for line in lines)


def render_status_bar(
    *,
    mode: str,
    model: str,
    data_sources: int,
    skills: int,
    mcp: str,
    width: int | None = None,
) -> str:
    budget = _terminal_width(width)
    if budget < 32:
        fixed = f" {str(mode)[:1]} d{data_sources} s{skills} m{mcp} "
        model_width = max(budget - _display_width(fixed) - 1, 1)
        return _truncate_display(fixed + _truncate_display(str(model), model_width), budget)
    compact = budget < 64
    prefix = f" {mode} · "
    suffix = (
        f" · d{data_sources} · s{skills} · m{mcp} "
        if compact
        else f" · data {data_sources} · skills {skills} · mcp {mcp} "
    )
    model_width = max(budget - _display_width(prefix) - _display_width(suffix), 1)
    return _truncate_display(prefix + _truncate_display(str(model), model_width) + suffix, budget)


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
    elapsed_part = "" if elapsed is None else " " + _color("+" + _format_elapsed(elapsed), "gold")
    prefix = f"{_color('thinking', 'muted')} {_color(clock, 'muted')}{elapsed_part}"
    return f"{prefix} · {event}: {_trace_detail(detail)}" if detail else f"{prefix} · {event}"


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
    expand = " · /trace 展开" if current_lang() == "zh" else " · /trace to expand"
    return (
        f"{_color('thinking summary', 'muted')} · {steps} steps · "
        f"{tool_count} {tool_label}{elapsed_part}{tool_part}{expand}"
    )


def render_tool_card(
    name: str,
    state: str,
    detail: str = "",
    *,
    elapsed: float | None = None,
    width: int | None = None,
) -> str:
    """Render a bounded tool event; compact mode keeps it behind ``/trace``."""
    frame_width = _terminal_width(width)
    inner = frame_width - 2
    timing = f" · +{_format_elapsed(elapsed)}" if elapsed is not None else ""
    hint = "/trace 可重新展开上一轮工具轨迹" if current_lang() == "zh" else "/trace reopens the last tool trace"
    return "\n".join([
        _frame_title(f" tool {name} · {state}{timing} ", inner),
        _frame_line(_trace_detail(detail, max(inner - 2, 1)), inner),
        _frame_line(hint, inner),
        _color("╰" + "─" * inner + "╯", "gold"),
    ])


def current_lang() -> str:
    load_local_env()
    value = os.environ.get("FINANCE_AGENT_LANG", "zh").strip().lower()
    return "en" if value.startswith("en") else "zh"


def _terminal_width(width: int | None = None) -> int:
    detected = shutil.get_terminal_size((82, 24)).columns if width is None else int(width)
    return max(20, min(detected, 120))


def _frame_title(title: str, inner: int) -> str:
    label = _truncate_display(title, inner)
    remaining = max(inner - _display_width(label), 0)
    left = remaining // 2
    right = remaining - left
    return _color("╭" + "─" * left + label + "─" * right + "╮", "gold")


def _frame_line(text: str, inner: int) -> str:
    content_width = max(inner - 2, 0)
    content = _pad_display(_truncate_display(text, content_width), content_width)
    return _color("│", "gold") + " " + content + " " + _color("│", "gold")


def _color(text: str, name: str) -> str:
    if not _should_color():
        return text
    colors = {
        "gold": "\033[38;5;220m",
        "green": "\033[38;5;82m",
        "muted": "\033[38;5;245m",
    }
    return f"{colors.get(name, '')}{text}\033[0m"


def _should_color() -> bool:
    if os.environ.get("NO_COLOR"):
        return False
    if os.environ.get("FORCE_COLOR"):
        return True
    return sys.stdout.isatty()


def _strip_ansi(text: str) -> str:
    output: list[str] = []
    index = 0
    while index < len(text):
        if text[index:index + 2] == "\033[":
            index += 2
            while index < len(text) and text[index] != "m":
                index += 1
            index += 1
            continue
        output.append(text[index])
        index += 1
    return "".join(output)


def _display_width(text: str) -> int:
    return sum(2 if unicodedata.east_asian_width(char) in {"F", "W"} else 1 for char in _strip_ansi(text))


def _pad_display(text: str, width: int) -> str:
    return text + " " * max(width - _display_width(text), 0)


def _truncate_display(text: str, width: int) -> str:
    clean = _strip_ansi(text)
    if _display_width(clean) <= width:
        return text
    visible = ""
    used = 0
    for char in clean:
        char_width = 2 if unicodedata.east_asian_width(char) in {"F", "W"} else 1
        if used + char_width > max(width - 1, 0):
            break
        visible += char
        used += char_width
    return visible + "…"


def _format_elapsed(seconds: float) -> str:
    if seconds < 10:
        return f"{seconds:.2f}s"
    if seconds < 60:
        return f"{seconds:.1f}s"
    minutes = int(seconds // 60)
    return f"{minutes}m{seconds - minutes * 60:.0f}s"


def _trace_detail(detail: str, width: int = 220) -> str:
    return _truncate_display(" ".join(str(detail).split()), width)
