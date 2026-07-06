"""受控 shell 执行（Day5：bash；Day10：加沙箱与权限）。"""
from __future__ import annotations
from .base import Tool


def _bash(command: str, timeout: int = 30) -> str:
    # TODO[Day5] subprocess 执行，捕获 stdout/stderr/returncode，超时保护
    # TODO[Day10] 接入权限层 + 沙箱（bwrap/firejail/docker），危险命令需确认
    raise NotImplementedError("Day5：实现 bash")


bash_tool = Tool(
    name="bash",
    description="在工作目录中执行一条 shell 命令并返回输出。",
    parameters={"type": "object",
                "properties": {"command": {"type": "string"}},
                "required": ["command"]},
    run=_bash,
)
