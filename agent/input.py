"""Interactive input helpers for the finance CLI."""
from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Iterable


DEFAULT_COMMANDS = [
    "/help",
    "/think on",
    "/think off",
    "/selfcheck",
    "/clear",
    "/compact",
    "/exit",
    "/status",
    "/security",
    "/mcp",
    "/proxy ",
    "/wechat ",
    "/memory ",
    "/evolve ",
    "/predict ",
    "/schedule ",
    "/lang ",
    "/quote ",
    "/quality ",
    "/history ",
    "/financials ",
    "/news ",
    "/indicators ",
    "/report ",
    "/compare ",
    "/debate ",
    "/backtest ",
    "/brief ",
    "/search ",
    "/fetch ",
    "/tools",
    "/sources",
]


class InteractiveInput:
    def __init__(self, prompt: str, commands: Iterable[str] = DEFAULT_COMMANDS):
        self.prompt = prompt
        self.commands = list(commands)
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
            from prompt_toolkit.completion import WordCompleter
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
        completer = WordCompleter(self.commands, ignore_case=True, sentence=True)
        return PromptSession(
            message=ANSI(self.prompt),
            history=FileHistory(str(history_path)),
            completer=completer,
            complete_while_typing=False,
            multiline=False,
            key_bindings=bindings,
            enable_history_search=True,
        )

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
