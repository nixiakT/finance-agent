from __future__ import annotations

import pytest

from agent.command_catalog import CompletionItem, command_completions, command_specs, completion_meta
from agent.custom_commands import load_custom_commands
from agent.dynamic_commands import DynamicSlashCommands
from agent.input import InteractiveInput
from agent.ui import _display_width, render_help, render_status_bar, render_tool_card, render_welcome


def test_command_catalog_drives_missing_completions() -> None:
    completions = command_completions()

    assert "/trace" in completions
    assert "/export-report AAPL 3mo reports/aapl.md" in completions
    assert "/think compact" in completions
    assert "/skills" in completions
    assert len({spec.name for spec in command_specs()}) == len(command_specs())


def test_interactive_input_uses_catalog_by_default(monkeypatch) -> None:  # noqa: ANN001
    monkeypatch.setattr(InteractiveInput, "_build_prompt_session", lambda self: None)
    monkeypatch.setattr(InteractiveInput, "_setup_readline_fallback", lambda self: None)

    reader = InteractiveInput("finance-agent > ")

    assert reader.commands == command_completions()


def test_welcome_adapts_to_small_and_large_terminals(monkeypatch) -> None:  # noqa: ANN001
    monkeypatch.setenv("NO_COLOR", "1")

    for width in (20, 60, 100):
        output = render_welcome(width=width)
        assert max(_display_width(line) for line in output.splitlines()) <= width
        assert "Finance Agent" in output


def test_help_is_catalog_backed_and_compact(monkeypatch) -> None:  # noqa: ANN001
    monkeypatch.setenv("FINANCE_AGENT_LANG", "zh")

    output = render_help()

    assert "/trace" in output
    assert "/export-report" in output
    assert "/skills" in output
    assert len(output.splitlines()) < 80

    narrow = render_help(width=20)
    assert max(_display_width(line) for line in narrow.splitlines()) <= 20


def test_status_bar_surfaces_runtime_capabilities() -> None:
    output = render_status_bar(
        mode="compact",
        model="deepseek-chat",
        data_sources=2,
        skills=4,
        mcp="1/2",
    )

    assert "compact" in output
    assert "deepseek-chat" in output
    assert "data 2" in output
    assert "skills 4" in output
    assert "mcp 1/2" in output

    narrow = render_status_bar(
        mode="compact",
        model="deepseek-reasoner-very-long-name",
        data_sources=2,
        skills=4,
        mcp="1/2",
        width=36,
    )
    assert "deep" in narrow
    assert "d2" in narrow and "s4" in narrow and "m1/2" in narrow
    assert _display_width(narrow) <= 36


def test_completion_menu_merges_builtin_custom_skill_and_mcp_prompt() -> None:
    extra = [
        CompletionItem("/review", "review the current stock", "custom"),
        CompletionItem("/finance-history-learning", "historical learning playbook", "skill"),
        CompletionItem("/mcp:research:daily", "daily research prompt", "mcp"),
    ]

    values = command_completions(extra)
    metadata = completion_meta(extra)

    assert "/help" in values
    assert "/review" in values
    assert "/finance-history-learning" in values
    assert "/mcp:research:daily" in values
    assert "custom" in metadata["/review"]
    assert "skill" in metadata["/finance-history-learning"]
    assert "mcp" in metadata["/mcp:research:daily"]


def test_custom_markdown_command_loads_and_substitutes_arguments(tmp_path) -> None:  # noqa: ANN001
    root = tmp_path / "commands"
    root.mkdir()
    (root / "review.md").write_text(
        "---\ndescription: Review a stock\nargument-hint: <ticker> <period>\n---\n"
        "Review $1 over $2. Full args: $ARGUMENTS. Literal: $$.",
        encoding="utf-8",
    )

    commands = load_custom_commands([root])

    assert [command.name for command in commands] == ["review"]
    assert commands[0].usage == "/review <ticker> <period>"
    assert commands[0].render(["AAPL", "3mo"]) == (
        "Review AAPL over 3mo. Full args: AAPL 3mo. Literal: $."
    )


def test_tool_card_is_bounded_and_points_to_trace(monkeypatch) -> None:  # noqa: ANN001
    monkeypatch.setenv("NO_COLOR", "1")

    output = render_tool_card(
        "finance_get_news",
        "done",
        "result " * 100,
        elapsed=0.123,
        width=60,
    )

    assert "finance_get_news" in output
    assert "done" in output
    assert "/trace" in output
    assert max(_display_width(line) for line in output.splitlines()) <= 60


def test_dynamic_slash_expands_custom_skill_and_mcp_prompt(tmp_path) -> None:  # noqa: ANN001
    command_root = tmp_path / "commands"
    command_root.mkdir()
    (command_root / "review.md").write_text(
        "---\ndescription: Review stock\n---\nReview $1 carefully.",
        encoding="utf-8",
    )
    skill_root = tmp_path / "skills"
    skill_path = skill_root / "risk" / "SKILL.md"
    skill_path.parent.mkdir(parents=True)
    skill_path.write_text(
        "---\nname: risk-check\ndescription: Check risks\n---\n\nList disconfirming evidence.",
        encoding="utf-8",
    )

    class Registry:
        def mcp_prompts(self):  # noqa: ANN201
            return [{
                "server": "research",
                "name": "daily",
                "description": "Daily prompt",
                "arguments": [{"name": "ticker", "required": True}],
            }]

        def get_mcp_prompt(self, server, name, arguments):  # noqa: ANN001, ANN201
            assert (server, name, arguments) == ("research", "daily", {"ticker": "AAPL"})
            return {"messages": [{"role": "user", "content": {"type": "text", "text": "Analyze AAPL"}}]}

    dynamic = DynamicSlashCommands(
        Registry(),
        command_roots=[command_root],
        skill_root=skill_root,
    )

    assert dynamic.expand("/review AAPL") == "Review AAPL carefully."
    assert "List disconfirming evidence." in dynamic.expand("/risk-check AAPL")
    assert "Analyze AAPL" in dynamic.expand("/mcp:research:daily AAPL")
    values = [item.text for item in dynamic.completion_items()]
    assert "/review" in values
    assert "/risk-check" in values
    assert "/mcp:research:daily" in values


def test_dynamic_mcp_prompt_failure_is_a_command_error(tmp_path) -> None:  # noqa: ANN001
    class Registry:
        def mcp_prompts(self):  # noqa: ANN201
            return [{"server": "broken", "name": "daily", "arguments": []}]

        def get_mcp_prompt(self, server, name, arguments):  # noqa: ANN001, ANN201
            raise RuntimeError("server died")

    dynamic = DynamicSlashCommands(Registry(), command_roots=[], skill_root=tmp_path)

    with pytest.raises(ValueError, match="server died"):
        dynamic.expand("/mcp:broken:daily")


def test_dynamic_completion_refreshes_new_skills(tmp_path) -> None:  # noqa: ANN001
    skill_root = tmp_path / "skills"
    dynamic = DynamicSlashCommands(type("Registry", (), {"mcp_prompts": lambda self: []})(), command_roots=[], skill_root=skill_root)
    assert dynamic.completion_items() == []

    path = skill_root / "new-skill" / "SKILL.md"
    path.parent.mkdir(parents=True)
    path.write_text(
        "---\nname: new-skill\ndescription: newly generated\n---\n\nFollow the new workflow.",
        encoding="utf-8",
    )
    dynamic.refresh()

    assert "/new-skill" in [item.text for item in dynamic.completion_items()]
    assert "Follow the new workflow" in dynamic.expand("/new-skill AAPL")
