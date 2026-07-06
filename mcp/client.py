"""最小 MCP 客户端（Day8）。

MCP（Model Context Protocol）让工具集从"写死在代码里"变成"可插拔的外部 server"。
本文件实现一个最小客户端：通过 stdio 跟 server 通信，做 JSON-RPC。

要实现的握手与调用：
  1. 启动 server 子进程（stdio transport）
  2. initialize 握手
  3. tools/list  —— 拉取 server 暴露的工具
  4. tools/call  —— 把某次调用转发给 server，拿回结果
然后在 agent/loop 里，把这些 MCP 工具**透明合并**进内置 ToolRegistry。
"""
from __future__ import annotations
import json
import subprocess
from typing import Any

from tools.base import Tool, ToolRegistry


class MCPClient:
    def __init__(self, command: list[str]):
        self.command = command
        self.proc: subprocess.Popen | None = None
        self._id = 0

    def start(self) -> None:
        # TODO[Day8] 启动子进程，stdin/stdout 接管，做 initialize 握手
        raise NotImplementedError("Day8：实现 stdio transport + initialize")

    def _rpc(self, method: str, params: dict | None = None) -> Any:
        # TODO[Day8] 发一条 JSON-RPC 请求（带自增 id），读回对应响应
        raise NotImplementedError("Day8：实现 JSON-RPC 收发")

    def list_tools(self) -> list[dict]:
        # TODO[Day8] 调 tools/list，返回工具描述列表
        raise NotImplementedError("Day8：实现 tools/list")

    def call_tool(self, name: str, arguments: dict) -> str:
        # TODO[Day8] 调 tools/call，返回结果文本
        raise NotImplementedError("Day8：实现 tools/call")


def register_mcp_tools(registry: ToolRegistry, client: MCPClient) -> None:
    """把一个 MCP server 的工具包装成内置 Tool 并注册，实现透明合并。"""
    for spec in client.list_tools():
        name = spec["name"]
        registry.register(Tool(
            name=f"mcp__{name}",            # 命名空间避免和内置工具撞名
            description=spec.get("description", ""),
            parameters=spec.get("inputSchema", {"type": "object", "properties": {}}),
            run=lambda _n=name, **kw: client.call_tool(_n, kw),
        ))
