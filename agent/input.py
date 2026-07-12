"""Interactive input helpers for the finance CLI."""
from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Callable, Iterable

from agent.command_catalog import command_completions, completion_meta

class InteractiveInput:
    def __init__(
        self,
        prompt: str,
        commands: Iterable[str] | None = None,
        command_metadata: dict[str, str] | None = None,
        completion_refresh: Callable[[], tuple[list[str], dict[str, str]]] | None = None,
        bottom_toolbar: Callable[[], str] | None = None,
    ):
        self.prompt = prompt
        self.commands = list(commands) if commands is not None else command_completions()
        self.command_metadata = command_metadata if command_metadata is not None else completion_meta()
        self.completion_refresh = completion_refresh
        self.bottom_toolbar = bottom_toolbar
        self._session = self._build_prompt_session()
        self._setup_readline_fallback()

    def read(self) -> str:
        if self._session is not None:
            return self._session.prompt()
        return input(self.prompt)

    def _build_prompt_session(self):
        if not sys.stdin.isatty():
            return None
        try:
            from prompt_toolkit import PromptSession
            from prompt_toolkit.completion import FuzzyCompleter, WordCompleter
            from prompt_toolkit.formatted_text import ANSI
            from prompt_toolkit.history import FileHistory
            from prompt_toolkit.key_binding import KeyBindings
        except Exception:
            return None

        bindings = KeyBindings()

        @bindings.add("c-j")
        def _(event):  # noqa: ANN001
            event.current_buffer.insert_text("\n")

        history_path = Path.home() / ".finance_agent_history"
        base_completer = WordCompleter(
            self._completion_words,
            ignore_case=True,
            sentence=True,
            meta_dict=self.command_metadata,
        )
        completer = FuzzyCompleter(base_completer, pattern=r"^.*")
        return PromptSession(
            message=ANSI(self.prompt),
            history=FileHistory(str(history_path)),
            completer=completer,
            complete_while_typing=True,
            multiline=False,
            key_bindings=bindings,
            enable_history_search=True,
            bottom_toolbar=self.bottom_toolbar,
        )

    def _completion_words(self) -> list[str]:
        if self.completion_refresh is not None:
            commands, metadata = self.completion_refresh()
            self.commands = list(commands)
            self.command_metadata.clear()
            self.command_metadata.update(metadata)
        return self.commands

    def _setup_readline_fallback(self) -> None:
        if self._session is not None or not sys.stdin.isatty():
            return
        try:
            import readline
        except Exception:
            return
        readline.parse_and_bind("tab: complete")
        readline.parse_and_bind("set editing-mode emacs")
        history_path = Path.home() / ".finance_agent_history"
        try:
            history_path.touch(exist_ok=True)
            readline.read_history_file(str(history_path))
        except OSError:
            return
        import atexit

        atexit.register(readline.write_history_file, str(history_path))


def clean_user_input(raw: str) -> str:
    """Remove accidentally pasted CLI prompt prefixes from user input."""
    text = raw.strip()
    pattern = re.compile(r"^(?:finance-agent\s*>\s*)+", flags=re.IGNORECASE)
    previous = None
    while previous != text:
        previous = text
        text = pattern.sub("", text).strip()
    return text
