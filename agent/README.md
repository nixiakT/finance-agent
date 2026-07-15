# agent

`agent/` 负责把用户请求组织成可观察、可停止的 Agent 工作流。模型负责决定下一步调用工具还是输出答案，Python 主循环负责执行工具、回填 observation，并在执行层落实安全边界。

## 主要入口

- `cli.py`：命令行入口、Agent 组装、可见 Trace 与 Token 汇总。
- `loop.py`：ReAct 主循环，默认最多 20 轮；处理工具调用、错误 observation、结果截断和副作用回执。
- `context.py`：上下文预算、摘要压缩、敏感文本脱敏和 observation 截断。
- `prompts.py`：系统提示词。
- `permissions.py`：工具调用前的 deny/confirm/allow 判定。
- `memory.py`：项目 Memory 与键值记忆的本地持久化。

## 数据流

`用户请求 -> AgentLoop -> 模型返回 tool_calls -> ToolRegistry 执行 -> observation 回填 -> 继续调用或最终答案`。

模型只能选择当前公开在 schema 中的工具。工具异常会变成 observation，而不是直接终止整个进程；是否能从错误中恢复仍取决于模型和备用路径。

## 安全与副作用边界

- 真正的文件、Shell、消息和预测写入都由执行层检查，不能只依赖提示词。
- 真实交易请求会被拒绝；纸面组合工具不能被表述成真实成交。
- `wechat_send` 前必须先有成功的 `wechat_status` 回执。
- 工具结果、网页内容和历史摘要按不可信数据处理，不能覆盖系统规则。
- 模型调用失败只允许在受限条件下进入确定性金融 fallback，避免重复执行副作用。

## 可观测性

`AgentLoop` 通过 observer 发出 `model_start/end`、`tool_start/end/error`、`context_compacted` 等事件。`cli.py` 将其渲染为可见 Trace，并汇总模型轮次、工具、耗时和 Token。成本只有在显式配置单价时才换算为金额。
