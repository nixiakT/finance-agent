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

    def __len__(self) -> int:
        return len(self._tools)


def build_default_registry() -> ToolRegistry:
    """组装内置工具。随课程推进逐步取消注释。"""
    reg = ToolRegistry()
    # TODO[Day5] 取消注释并实现：
    # from .fs import read_tool, write_tool
    # from .shell import bash_tool
    # for t in (read_tool, write_tool, bash_tool):
    #     reg.register(t)
    #
    # TODO[Day6] 再加入完整工具集（→ v1 里程碑）：
    # from .more_tools import edit_tool, grep_tool, glob_tool
    # for t in (edit_tool, grep_tool, glob_tool):
    #     reg.register(t)
    #
    # TODO[Day7] 再加入：
    # from .more_tools import web_fetch_tool, task_list_tool
    return reg
