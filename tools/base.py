"""工具抽象与注册表。

核心思想（贯穿全课）：
  「工具」就是一个有 name / description / 输入 schema / run() 的对象。
  模型并不会"真的调用函数"——它只是生成一段文本
  <tool_call>{"name": ..., "arguments": {...}}</tool_call>，
  由主循环（agent/loop.py）解析出来，找到同名 Tool，执行它的 run()，
  再把返回值作为 observation 喂回模型。

Day5 实现 read/write/bash；Day6 补 edit/grep/glob；Day7 补 web_fetch/task_list。
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass
class Tool:
    name: str
    description: str
    # JSON Schema（OpenAI tools 格式里的 parameters）。Day3 你会明白它最终如何变成 prompt 里的文本。
    parameters: dict[str, Any]
    run: Callable[..., str]   # run(**arguments) -> str（observation 文本）

    def schema(self) -> dict[str, Any]:
        """转成 OpenAI tools 字段的一项。"""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }


@dataclass
class ToolRegistry:
    _tools: dict[str, Tool] = field(default_factory=dict)
    _managed_resources: list[Any] = field(default_factory=list, repr=False)

    def register(self, tool: Tool) -> None:
        if tool.name in self._tools:
            raise ValueError(f"工具重名：{tool.name}")
        self._tools[tool.name] = tool

    def get(self, name: str) -> Tool | None:
        return self._tools.get(name)

    def schemas(self) -> list[dict[str, Any]]:
        return [t.schema() for t in self._tools.values()]

    def names(self) -> list[str]:
        return list(self._tools)

    def manage(self, resource: Any) -> None:
        """Attach a runtime resource so callers can inspect and close it centrally."""
        self._managed_resources.append(resource)

    def mcp_statuses(self) -> list[dict[str, str]]:
        rows: list[dict[str, str]] = []
        for resource in self._managed_resources:
            statuses = getattr(resource, "statuses", None)
            if callable(statuses):
                rows.extend(statuses())
        return sorted(rows, key=lambda row: row.get("name", ""))

    def mcp_prompts(self) -> list[dict[str, Any]]:
        prompts: list[dict[str, Any]] = []
        for resource in self._managed_resources:
            catalog = getattr(resource, "prompt_catalog", None)
            if callable(catalog):
                prompts.extend(catalog())
        return sorted(prompts, key=lambda item: (item.get("server", ""), item.get("name", "")))

    def get_mcp_prompt(
        self,
        server: str,
        name: str,
        arguments: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        for resource in self._managed_resources:
            getter = getattr(resource, "get_prompt", None)
            if not callable(getter):
                continue
            try:
                return getter(server, name, arguments)
            except KeyError:
                continue
        raise KeyError(f"unknown MCP prompt '{server}/{name}'")

    def close(self) -> None:
        """Close every managed runtime, even if one close operation fails."""
        errors: list[str] = []
        for resource in reversed(self._managed_resources):
            close = getattr(resource, "close", None)
            if not callable(close):
                continue
            try:
                close()
            except Exception as exc:  # noqa: BLE001 - finish closing the remaining resources
                errors.append(str(exc))
        if errors:
            raise RuntimeError("failed to close managed resources: " + "; ".join(errors))

    def __len__(self) -> int:
        return len(self._tools)


def build_default_registry() -> ToolRegistry:
    """组装内置工具。随课程推进逐步取消注释。"""
    reg = ToolRegistry()
    from .evolution_tools import evolution_tools
    from .finance_tools import finance_tools
    from .fs import read_tool, write_tool
    from .memory_tools import memory_tools
    from .more_tools import edit_tool, glob_tool, grep_tool, task_list_tool
    from .scheduler_tools import scheduler_tools
    from .shell import bash_tool
    from .skill_tools import read_skill_tool
    from .trace2skill_tools import trace2skill_tools
    from .web_tools import web_tools
    from .wechat_tools import wechat_tools

    for tool in [
        read_tool,
        write_tool,
        bash_tool,
        edit_tool,
        grep_tool,
        glob_tool,
        task_list_tool,
        *memory_tools,
        read_skill_tool,
        *finance_tools,
        *evolution_tools,
        *trace2skill_tools,
        *web_tools,
        *scheduler_tools,
        *wechat_tools,
    ]:
        reg.register(tool)

    from mcp.client import connect_project_mcp

    connect_project_mcp(reg)
    return reg
