from __future__ import annotations

from typing import Any

import pytest

from agent.cli import main
from agent.commands import CommandRouter
from agent.context import maybe_compact, truncate_observation
from agent.loop import AgentLoop
from finance.data import ProviderError
from tools.base import Tool, ToolRegistry


def test_truncate_observation_marks_truncation() -> None:
    text = truncate_observation("x" * 20, max_chars=10)

    assert text.startswith("x" * 10)
    assert "已截断" in text


def test_maybe_compact_preserves_system_and_recent_messages() -> None:
    messages = [{"role": "system", "content": "system"}]
    messages.extend({"role": "user", "content": "x" * 1000} for _ in range(20))

    compacted = maybe_compact(messages, budget=100)

    assert compacted[0] == {"role": "system", "content": "system"}
    assert compacted[1]["role"] == "system"
    assert "compacted" in compacted[1]["content"]
    assert len(compacted) < len(messages)


def test_agent_loop_truncates_tool_results() -> None:
    registry = ToolRegistry()
    registry.register(Tool(
        name="long_tool",
        description="Return a long result",
        parameters={"type": "object", "properties": {}},
        run=lambda: "a" * 50,
    ))
    backend = ToolThenAnswerBackend()
    loop = AgentLoop(
        backend=backend,
        registry=registry,
        system_prompt="system",
        max_observation_chars=12,
    )

    answer = loop.run("run tool")

    assert answer.startswith("a" * 12)
    assert "已截断" in answer


def test_sources_command_reports_provider_status() -> None:
    class Provider:
        def diagnostics(self) -> list[dict[str, str]]:
            return [{"name": "TEST", "status": "enabled", "detail": "unit test"}]

    class Finance:
        provider = Provider()

    router = CommandRouter(ToolRegistry(), finance_agent=Finance())  # type: ignore[arg-type]

    output = router.handle("/sources").output

    assert "TEST: enabled - unit test" in output


def test_finance_command_surfaces_provider_error_without_traceback() -> None:
    class Finance:
        def get_quote(self, symbol: str) -> str:
            raise ProviderError("not found")

    router = CommandRouter(ToolRegistry(), finance_agent=Finance())  # type: ignore[arg-type]

    output = router.handle("/quote UNKNOWNXYZ").output

    assert "数据获取失败" in output
    assert "not found" in output


def test_main_handles_single_shot_slash_command(capsys: Any) -> None:
    assert main(["/tools"]) == 0

    output = capsys.readouterr().out

    assert "已注册工具" in output
    assert "finance_get_quote" in output


def test_main_handles_single_shot_slash_command_with_args(capsys: Any, monkeypatch: pytest.MonkeyPatch) -> None:
    import agent.commands as commands

    monkeypatch.setattr(commands, "web_search", lambda query, limit=5: f"搜索: {query}\nlimit={limit}")

    assert main(["/search", "智谱", "02513", "股票"]) == 0

    output = capsys.readouterr().out

    assert "搜索: 智谱 02513 股票" in output
    assert "02513" in output


class ToolThenAnswerBackend:
    def chat(self, messages: list[dict[str, Any]], tools: list[dict] | None = None) -> dict[str, Any]:
        if messages[-1].get("role") == "tool":
            return {"role": "assistant", "content": messages[-1]["content"], "tool_calls": []}
        return {"role": "assistant", "content": "", "tool_calls": [{"name": "long_tool", "arguments": {}}]}
