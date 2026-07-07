"""命令行入口。

用法：
  python -m agent.cli --selfcheck          # Day1：自检骨架是否装好
  python -m agent.cli "创建 hello.py 并运行"  # Day5 起：真正跑任务（v1 在 Day6）
"""
from __future__ import annotations
import argparse
import sys

from tools.base import build_default_registry
from agent.input import InteractiveInput, clean_user_input
from agent.prompts import SYSTEM_PROMPT
from agent.ui import render_help, render_prompt, render_trace, render_welcome


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


def make_observer(enabled):
    def observe(event, payload):
        if not enabled():
            return
        if event == "model_start":
            print(render_trace("model", f"turn {payload.get('turn')}"))
        elif event == "model_end":
            calls = payload.get("tool_calls") or []
            if calls:
                print(render_trace("model selected tools", ", ".join(calls)))
            elif payload.get("content_preview"):
                print(render_trace("model answered", payload["content_preview"]))
        elif event == "tool_start":
            print(render_trace("tool", f"{payload.get('name')} {payload.get('arguments')}"))
        elif event == "tool_end":
            print(render_trace("tool result", f"{payload.get('name')} -> {payload.get('preview')}"))
        elif event == "tool_error":
            print(render_trace("tool error", f"{payload.get('name')} -> {payload.get('error')}"))
        elif event == "context_compacted":
            print(render_trace("context compacted", f"{payload.get('messages')} messages retained"))
    return observe


def interactive() -> int:
    from agent.commands import CommandRouter
    from agent.loop import AgentSession

    print(render_welcome())
    print()
    think_enabled = False
    agent = build_agent(observer=make_observer(lambda: think_enabled))
    session = AgentSession(agent)
    router = CommandRouter(
        agent.registry,
        trace=lambda event, detail: print(render_trace(event, detail)) if think_enabled else None,
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
        if task.startswith("/"):
            result = router.handle(task, think_enabled=think_enabled)
            if result.handled:
                if result.think is not None:
                    think_enabled = result.think
                if result.clear:
                    session.reset()
                if result.selfcheck:
                    selfcheck()
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
        print(session.ask(task))


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
        result = CommandRouter(reg).handle(task)
        if result.handled:
            if result.selfcheck:
                return selfcheck()
            if result.output:
                print(result.output)
            if result.exit:
                print("bye.")
            return 0

    # 真正跑任务：优先用 DeepSeek API；没配 key 时回退到 FakeBackend（离线打通管道）
    agent = build_agent()
    print(agent.run(task))
    return 0


if __name__ == "__main__":
    sys.exit(main())
