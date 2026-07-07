"""受控 shell 执行（Day5：bash；Day10：加沙箱与权限）。"""
from __future__ import annotations

import subprocess

from .base import Tool
from .security import guard_shell


def _bash(command: str, timeout: int = 30) -> str:
    args = guard_shell(command)
    try:
        result = subprocess.run(
            args,
            cwd=".",
            text=True,
            capture_output=True,
            timeout=max(1, min(timeout, 120)),
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        return f"命令超时: {command}\nstdout:\n{exc.stdout or ''}\nstderr:\n{exc.stderr or ''}"
    stdout = _truncate(result.stdout or "")
    stderr = _truncate(result.stderr or "")
    return "\n".join([
        f"command: {command}",
        f"returncode: {result.returncode}",
        "stdout:",
        stdout,
        "stderr:",
        stderr,
    ]).rstrip()


bash_tool = Tool(
    name="bash",
    description="在工作目录中执行一条 shell 命令并返回输出。",
    parameters={"type": "object",
                "properties": {"command": {"type": "string"},
                               "timeout": {"type": "integer", "description": "超时秒数，默认 30，最大 120"}},
                "required": ["command"]},
    run=_bash,
)


def _truncate(text: str, limit: int = 12_000) -> str:
    if len(text) <= limit:
        return text
    return text[:limit] + f"\n...[已截断，共 {len(text)} 字符]"
