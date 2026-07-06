"""命令行入口。

用法：
  python -m agent.cli --selfcheck          # Day1：自检骨架是否装好
  python -m agent.cli "创建 hello.py 并运行"  # Day5 起：真正跑任务（v1 在 Day6）
"""
from __future__ import annotations
import argparse
import sys

from tools.base import build_default_registry
from agent.prompts import SYSTEM_PROMPT
from agent.ui import render_help, render_prompt, render_welcome


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
    print("== mini-OpenClaw 自检 ==")
    ok = True
    try:
        reg = build_default_registry()
        print(f"[ok] 工具注册表加载成功，当前内置工具数：{len(reg)}（Day5 起会变多）")
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
        print("[ok] 主循环模块可导入（Day5 实现 run 逻辑）")
    except Exception as e:  # noqa
        print(f"[FAIL] 主循环：{e}"); ok = False

    print("== 自检", "通过 ✅" if ok else "未通过 ❌", "==")
    print("\n下一步：按 dayNN 的 lab-guide 填 # TODO 标记。")
    return 0 if ok else 1


def welcome() -> int:
    print(render_welcome())
    return 0


def build_agent():
    from agent.loop import AgentLoop

    reg = build_default_registry()
    try:
        from backend.client import DeepSeekBackend
        backend = DeepSeekBackend()
    except Exception as e:  # noqa: BLE001
        from backend.fake_backend import FakeBackend
        print(f"[提示] 未启用真后端（{e}），回退 FakeBackend。配置 DEEPSEEK_API_KEY 后即用真模型。")
        backend = FakeBackend()
    return AgentLoop(backend, reg, build_system_prompt())


def interactive() -> int:
    from agent.loop import AgentSession

    print(render_welcome())
    print()
    agent = build_agent()
    session = AgentSession(agent)
    while True:
        try:
            user_input = input(render_prompt())
        except (EOFError, KeyboardInterrupt):
            print("\nbye.")
            return 0
        task = user_input.strip()
        if not task:
            continue
        command = task.lower()
        if command in {"/exit", "/quit", "exit", "quit"}:
            print("bye.")
            return 0
        if command in {"/help", "help"}:
            print(render_help())
            continue
        if command in {"/clear", "clear"}:
            session.reset()
            print("已清空当前会话上下文。")
            continue
        if command in {"/selfcheck", "selfcheck"}:
            selfcheck()
            continue
        print(session.ask(task))


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="mini-openclaw")
    p.add_argument("task", nargs="?", help="要让 agent 完成的任务（自然语言）")
    p.add_argument("--selfcheck", action="store_true", help="只做骨架自检")
    args = p.parse_args(argv)

    if args.selfcheck:
        return selfcheck()
    if not args.task:
        return interactive()
    if args.task.strip().lower() in {"/help", "help"}:
        print(render_help())
        return 0

    # 真正跑任务：优先用 DeepSeek API；没配 key 时回退到 FakeBackend（离线打通管道）
    agent = build_agent()
    print(agent.run(args.task))
    return 0


if __name__ == "__main__":
    sys.exit(main())
