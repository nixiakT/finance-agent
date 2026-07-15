# backend

`backend/` 把具体模型 API 适配成 AgentLoop 使用的统一接口：

```text
chat(messages, tools) -> {content, tool_calls, usage}
```

## 主要入口

- `client.py`：`DeepSeekBackend`，支持 OpenAI 兼容的 Chat Completions 和 Responses 两种接口。
- `fake_backend.py`：离线测试使用的确定性后端，不发起真实模型请求。

`DeepSeekBackend` 负责规范化不同接口返回的文本、工具调用和 Token usage。模型配置来自环境变量；真实 API key 不应写入源码或提交到 Git。

## 关键配置

- `DEEPSEEK_API_KEY`：API 密钥，必需且不得提交。
- `DEEPSEEK_BASE_URL`：兼容接口地址。
- `DEEPSEEK_MODEL`：模型名称。
- `DEEPSEEK_API_MODE`：`chat_completions` 或 `responses`。
- `FINANCE_MODEL_TIMEOUT_SECONDS`、`FINANCE_MODEL_READ_RETRIES`：超时和读取重试。

## 设计边界

- 后端只负责一次模型调用，不执行工具；工具执行属于 `agent/loop.py`。
- 真模型不公开 `finance_route_task` 和 `finance_generate_report` 两个固定报告工具，防止自然语言金融任务绕过 Agent 自主组合具体工具。
- `usage` 统一交给 `agent/usage.py` 统计；缺少服务端 usage 时不虚构 Token 或费用。
- 网络错误向上抛出，由调用方记录 Trace 或决定是否进入受限 fallback。
