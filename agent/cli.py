"""命令行入口。

用法：
  python -m agent.cli --selfcheck          # Day1：自检骨架是否装好
  python -m agent.cli "创建 hello.py 并运行"  # Day5 起：真正跑任务（v1 在 Day6）
"""
from __future__ import annotations
import argparse
import json
import re
import sys
from time import perf_counter

from tools.base import build_default_registry
from agent.input import InteractiveInput, clean_user_input
from agent.prompts import SYSTEM_PROMPT
from agent.ui import render_help, render_prompt, render_trace, render_trace_summary, render_welcome


FINANCE_TEXT_HINTS = (
    "股票", "股价", "行情", "走势", "财报", "估值", "回测", "选股", "辩论",
    "自选股", "标的", "上市", "港股", "美股", "概念股", "基本面", "技术面",
    "市盈率", "成交量", "财务", "均线", "智谱", "贵州茅台",
)

FINANCE_WORD_HINTS = (
    "quote", "stock", "ticker", "price", "listed", "ipo", "nasdaq", "nyse", "hkex",
    "spacex", "minimax", "spcx", "nvda", "amd", "aapl", "tsla", "msft",
    "pe", "eps", "roe", "rsi", "macd", "ma20", "ma60",
)


def build_system_prompt() -> str:
    try:
        from skills.loader import load_skills, skills_catalog

        skills = load_skills()
        if not skills:
            return SYSTEM_PROMPT
        return SYSTEM_PROMPT + "\n\n可用 Skills：\n" + skills_catalog(skills)
    except Exception as exc:  # noqa: BLE001
        return SYSTEM_PROMPT + f"\n\n[Skill 加载失败：{exc}]"


def selfcheck() -> int:
    print("== finance-agent 自检 ==")
    ok = True
    try:
        reg = build_default_registry()
        print(f"[ok] 工具注册表加载成功，当前内置工具数：{len(reg)}")
        print(f"     工具：{', '.join(reg.names())}")
    except Exception as e:  # noqa
        print(f"[FAIL] 工具注册表：{e}"); ok = False

    try:
        from backend.fake_backend import FakeBackend
        FakeBackend().chat([{"role": "user", "content": "hi"}], tools=[])
        print("[ok] FakeBackend 可用（未配 DEEPSEEK_API_KEY 时的离线占位后端）")
    except Exception as e:  # noqa
        print(f"[FAIL] FakeBackend：{e}"); ok = False

    try:
        from agent.loop import AgentLoop  # noqa
        print("[ok] 主循环模块可导入")
    except Exception as e:  # noqa
        print(f"[FAIL] 主循环：{e}"); ok = False

    print("== 自检", "通过 ✅" if ok else "未通过 ❌", "==")
    print("\n可继续运行：python -m agent.cli /help 或 python -m agent.cli")
    return 0 if ok else 1


def welcome() -> int:
    print(render_welcome())
    return 0


def build_agent(observer=None):
    from agent.loop import AgentLoop

    reg = build_default_registry()
    try:
        from backend.client import DeepSeekBackend
        backend = DeepSeekBackend()
    except Exception as e:  # noqa: BLE001
        from backend.fake_backend import FakeBackend
        print(f"[提示] 未启用真后端（{e}），回退 FakeBackend。配置 DEEPSEEK_API_KEY 后即用真模型。")
        backend = FakeBackend()
    return AgentLoop(backend, reg, build_system_prompt(), observer=observer)


class TracePrinter:
    """Visible execution trace for the CLI, not hidden model reasoning."""

    def __init__(self, mode):
        self.mode = mode
        self._model_started: dict[int, float] = {}
        self._tool_started: dict[str, float] = {}
        self._command_tool_started: tuple[str, float] | None = None
        self._current_lines: list[str] = []
        self._current_tools: list[str] = []
        self._current_started: float | None = None
        self._last_lines: list[str] = []

    def observe(self, event, payload):
        if self._mode() == "off":
            return
        if event == "model_start":
            turn = int(payload.get("turn") or 0)
            self._model_started[turn] = perf_counter()
            self._emit(render_trace("model turn", str(turn)))
        elif event == "model_end":
            turn = int(payload.get("turn") or 0)
            elapsed = _elapsed(self._model_started.pop(turn, None))
            calls = payload.get("tool_calls") or []
            if calls:
                self._emit(render_trace("selected tools", ", ".join(calls), elapsed=elapsed))
            elif payload.get("content_preview"):
                self._emit(render_trace("model answer", payload["content_preview"], elapsed=elapsed))
        elif event == "tool_start":
            name = str(payload.get("name") or "unknown")
            self._tool_started[name] = perf_counter()
            self._emit(render_trace(f"tool {name}", _json_preview(payload.get("arguments", {}))), tool=name)
        elif event == "tool_end":
            name = str(payload.get("name") or "unknown")
            elapsed = _elapsed(self._tool_started.pop(name, None))
            self._emit(render_trace(f"tool result {name}", str(payload.get("preview") or ""), elapsed=elapsed), tool=name)
        elif event == "tool_error":
            name = str(payload.get("name") or "unknown")
            elapsed = _elapsed(self._tool_started.pop(name, None))
            self._emit(render_trace(f"tool error {name}", str(payload.get("error") or ""), elapsed=elapsed), tool=name)
        elif event == "context_compacted":
            self._emit(render_trace("context compacted", f"{payload.get('messages')} messages retained"))

    def command(self, event: str, detail: str) -> None:
        if self._mode() == "off":
            return
        name, rest = _split_trace_detail(detail)
        if event == "tool":
            self._command_tool_started = (name, perf_counter())
            self._emit(render_trace(f"tool {name}", rest), tool=name)
            return
        if event == "tool result":
            elapsed = None
            if self._command_tool_started and self._command_tool_started[0] == name:
                elapsed = _elapsed(self._command_tool_started[1])
                self._command_tool_started = None
            self._emit(render_trace(f"tool result {name}", rest, elapsed=elapsed), tool=name)
            return
        self._emit(render_trace(event, detail))

    def flush(self) -> None:
        if not self._current_lines:
            return
        elapsed = _elapsed(self._current_started)
        self._last_lines = list(self._current_lines)
        if self._mode() == "compact":
            print(render_trace_summary(len(self._current_lines), self._current_tools, elapsed=elapsed))
        self._current_lines = []
        self._current_tools = []
        self._current_started = None

    def render_details(self) -> str:
        if not self._last_lines:
            return "暂无可展开的 thinking 轨迹。"
        return "\n".join(self._last_lines)

    def _emit(self, line: str, tool: str | None = None) -> None:
        if self._current_started is None:
            self._current_started = perf_counter()
        self._current_lines.append(line)
        if tool and tool not in self._current_tools:
            self._current_tools.append(tool)
        if self._mode() == "on":
            print(line)

    def _mode(self) -> str:
        value = self.mode()
        if value is True:
            return "on"
        if value is False or value is None:
            return "off"
        normalized = str(value).lower()
        return normalized if normalized in {"on", "compact", "off"} else "compact"


def make_observer(enabled):
    printer = TracePrinter(enabled)

    def observe(event, payload):
        printer.observe(event, payload)

    return observe


def interactive() -> int:
    from agent.commands import CommandRouter
    from agent.loop import AgentSession
    from finance.agent import FinanceResearchAgent

    print(render_welcome())
    print()
    think_mode = "compact"
    trace = TracePrinter(lambda: think_mode)
    agent = build_agent(observer=trace.observe)
    session = AgentSession(agent)
    finance = FinanceResearchAgent()
    router = CommandRouter(
        agent.registry,
        finance_agent=finance,
        trace=trace.command,
    )
    input_reader = InteractiveInput(render_prompt())
    while True:
        try:
            user_input = input_reader.read()
        except (EOFError, KeyboardInterrupt):
            print("\nbye.")
            return 0
        task = clean_user_input(user_input)
        if not task:
            continue
        command = task.lower()
        if command in {"/help", "help"}:
            print(render_help())
            continue
        if command == "/trace":
            print(trace.render_details())
            continue
        if task.startswith("/"):
            result = router.handle(task, think_enabled=think_mode)
            if result.handled:
                if result.think is not None:
                    think_mode = result.think
                if result.clear:
                    session.reset()
                if result.compact:
                    print(session.compact())
                if result.selfcheck:
                    selfcheck()
                trace.flush()
                if result.output:
                    print(result.output)
                if result.exit:
                    print("bye.")
                    return 0
                continue
        if command in {"exit", "quit"}:
            print("bye.")
            return 0
        if command == "help":
            print(render_help())
            continue
        if _should_route_finance(task):
            trace.command("tool", f"finance_route_task {_json_preview({'task': task})}")
            output = finance.route_task(task)
            trace.command("tool result", f"finance_route_task -> {_preview(output)}")
            trace.flush()
            print(output)
            continue
        answer = session.ask(task)
        trace.flush()
        print(answer)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="mini-openclaw")
    p.add_argument("task", nargs="*", help="要让 agent 完成的任务（自然语言）")
    p.add_argument("--selfcheck", action="store_true", help="只做骨架自检")
    args = p.parse_args(argv)

    if args.selfcheck:
        return selfcheck()
    task = " ".join(args.task).strip()
    if not task:
        return interactive()
    if task.lower() in {"/help", "help"}:
        print(render_help())
        return 0
    if task.startswith("/"):
        from agent.commands import CommandRouter

        reg = build_default_registry()
        trace = TracePrinter(lambda: "compact")
        if task.lower() == "/trace":
            print(trace.render_details())
            return 0
        result = CommandRouter(reg, trace=trace.command).handle(task, think_enabled="compact")
        if result.handled:
            if result.selfcheck:
                return selfcheck()
            if result.compact:
                print("当前没有交互会话可压缩。请进入交互模式后使用 /compact。")
                return 0
            trace.flush()
            if result.output:
                print(result.output)
            if result.exit:
                print("bye.")
            return 0

    if _should_route_finance(task):
        trace = TracePrinter(lambda: "compact")
        from finance.agent import FinanceResearchAgent

        trace.command("tool", f"finance_route_task {_json_preview({'task': task})}")
        output = FinanceResearchAgent().route_task(task)
        trace.command("tool result", f"finance_route_task -> {_preview(output)}")
        trace.flush()
        print(output)
        return 0

    # 真正跑任务：优先用 DeepSeek API；没配 key 时回退到 FakeBackend（离线打通管道）
    trace = TracePrinter(lambda: "compact")
    agent = build_agent(observer=trace.observe)
    answer = agent.run(task)
    trace.flush()
    print(answer)
    return 0


def _json_preview(value) -> str:
    try:
        return json.dumps(value, ensure_ascii=False, default=str, separators=(",", ":"))
    except TypeError:
        return str(value)


def _elapsed(started_at: float | None) -> float | None:
    if started_at is None:
        return None
    return max(perf_counter() - started_at, 0.0)


def _split_trace_detail(detail: str) -> tuple[str, str]:
    text = str(detail).strip()
    if " -> " in text:
        name, rest = text.split(" -> ", 1)
        return name.strip() or "unknown", rest.strip()
    if not text:
        return "unknown", ""
    name, _, rest = text.partition(" ")
    return name.strip() or "unknown", rest.strip()


def _should_route_finance(task: str) -> bool:
    text = task.strip()
    if not text or text.startswith("/"):
        return False
    lowered = text.lower()
    compact = re.sub(r"\s+", "", lowered)
    if any(hint in compact for hint in FINANCE_TEXT_HINTS) or "a股" in compact:
        return True
    words = set(re.findall(r"[a-z0-9.]+", lowered))
    if words.intersection(FINANCE_WORD_HINTS):
        return True
    if re.search(r"\b[A-Z]{1,6}(?:\.[A-Z]{1,4})?\b", text) and any(
        token in text for token in ("分析", "比较", "看看", "查", "今天", "最近", "情况", "走势", "财报")
    ):
        return True
    if any(char.isdigit() for char in text) and any(token in text for token in ("分析", "比较", "看看", "查", "今天", "最近")):
        return True
    return False


def _preview(text: str, limit: int = 180) -> str:
    clean = " ".join(str(text).split())
    if len(clean) <= limit:
        return clean
    return clean[:limit] + "..."


if __name__ == "__main__":
    sys.exit(main())
