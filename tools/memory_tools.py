"""Tools for project-level persistent memory."""
from __future__ import annotations

from agent.memory import KVMemory, Memory
from .base import Tool


def _remember(note: str) -> str:
    path = Memory().write(note)
    return f"已记住：{note}\n写入: {path}"


def _memory_set(key: str, value: str) -> str:
    path = KVMemory().remember(key, value)
    return f"已更新结构化记忆：{key}\n写入: {path}"


def _memory_forget(key: str) -> str:
    path = KVMemory().forget(key)
    return f"已遗忘结构化记忆：{key}\n写入: {path}"


remember_tool = Tool(
    name="remember",
    description="当用户明确要求长期记住一条跨会话仍成立的项目约定、偏好或关键决策时调用。不要记录密钥、密码、token、cookie 或一次性闲聊。",
    parameters={
        "type": "object",
        "properties": {"note": {"type": "string", "description": "要长期记住的脱敏项目约定或偏好"}},
        "required": ["note"],
    },
    run=_remember,
)

memory_set_tool = Tool(
    name="memory_set",
    description="更新一条结构化项目记忆。适合用户纠正已有约定，例如把 package_manager 从 npm 改成 pnpm。",
    parameters={
        "type": "object",
        "properties": {
            "key": {"type": "string"},
            "value": {"type": "string"},
        },
        "required": ["key", "value"],
    },
    run=_memory_set,
)

memory_forget_tool = Tool(
    name="memory_forget",
    description="当用户明确要求忘记某条结构化项目记忆时调用。",
    parameters={
        "type": "object",
        "properties": {"key": {"type": "string"}},
        "required": ["key"],
    },
    run=_memory_forget,
)


memory_tools = [remember_tool, memory_set_tool, memory_forget_tool]
