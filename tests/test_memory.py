from __future__ import annotations

from agent.memory import KVMemory, Memory
from tools.base import build_default_registry
from tools.memory_tools import remember_tool


def test_memory_persists_across_instances(tmp_path) -> None:  # noqa: ANN001
    path = tmp_path / "MEMORY.md"

    Memory(path).write("本项目时间戳一律用 UTC")
    recalled = Memory(path).recall()

    assert "本项目时间戳一律用 UTC" in recalled
    assert recalled.startswith("# 项目记忆")


def test_memory_sanitizes_secrets(tmp_path) -> None:  # noqa: ANN001
    path = tmp_path / "MEMORY.md"

    Memory(path).write("api_key=abcdefghijklmnop 以后用 UTC")

    recalled = Memory(path).recall()
    assert "abcdefghijklmnop" not in recalled
    assert "[REDACTED_SECRET]" in recalled


def test_kv_memory_updates_and_forgets(tmp_path) -> None:  # noqa: ANN001
    path = tmp_path / "memory.json"
    memory = KVMemory(path)

    memory.remember("pm", "npm")
    memory.remember("pm", "pnpm")
    assert KVMemory(path).data == {"pm": "pnpm"}

    memory.forget("pm")
    assert KVMemory(path).data == {}


def test_remember_tool_writes_project_memory(tmp_path, monkeypatch) -> None:  # noqa: ANN001
    monkeypatch.chdir(tmp_path)

    output = remember_tool.run(note="包管理器用 pnpm，不要用 npm")

    assert "已记住" in output
    assert "pnpm" in (tmp_path / "MEMORY.md").read_text(encoding="utf-8")


def test_memory_tools_are_registered() -> None:
    registry = build_default_registry()

    assert registry.get("remember") is not None
    assert registry.get("memory_set") is not None
    assert registry.get("memory_forget") is not None
