# mcp

`mcp/` 实现基于 stdio 的 Model Context Protocol 运行时，把外部 MCP Server 的工具注册到同一个 `ToolRegistry`，供 AgentLoop 统一选择和执行。

## 主要入口

- `client.py`：`MCPClient`、`MCPRuntime`、工具/Prompt 发现、JSON-RPC 生命周期与注册。
- `echo_server.py`：默认本地回声 Server，用于连通性与测试。
- `finance_server.py`：示例金融风险预算工具。

项目存在 `.mcp.json` 时，`connect_project_mcp()` 读取其中的 stdio Server；不存在时使用默认 echo Server。远端工具统一命名为：

```text
mcp__<server>__<tool>
```

## 生命周期与错误处理

客户端执行 `initialize`，再发现 `tools/list` 和可选的 `prompts/list`。单一 stdio 流上的 RPC 用锁串行化；超时、无效 JSON、进程提前退出和命名冲突都会留下状态信息。`ToolRegistry.close()` 负责关闭托管的 MCP 进程。

## 安全边界

- 当前只支持本地配置的 stdio 传输，不自动连接任意远程地址。
- 配置、远端 schema、Prompt 元数据和工具结果都视为不可信数据。
- schema 在注册前清洗；工具名带 Server 命名空间并进行冲突检查。
- MCP 只能扩展工具能力，不能绕过 AgentLoop 的权限、副作用和真实交易限制。
