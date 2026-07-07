# Finance Agent 技术文档

## 架构总览

入口是 `python -m agent.cli`。系统由六块组成：

1. `backend/`: OpenAI-compatible DeepSeek 客户端和 FakeBackend。
2. `agent/loop.py`: ReAct 主循环，负责多轮模型调用、工具调用、tool result 回填、终止和错误 observation。
3. `tools/`: 内置工具系统，包含文件、shell、搜索、金融、网页、微信连接、金融自进化、trace2skill。
4. `mcp/`: 最小 stdio MCP client 和 echo server，MCP 工具以 `mcp__` 前缀透明注册进主循环。
5. `skills/`: Skill 加载器和领域 Skill，系统提示词会注入可用 Skill 清单。
6. `tools/security.py`: 权限分层、安全拦截和不可信内容隔离。

## 关键设计

### ReAct 主循环

`AgentLoop.run_messages()` 每轮调用模型。如果模型返回 `tool_calls`，主循环逐个执行工具，把结果以 `role=tool` 放回 messages。工具异常不会崩溃，而是变成 `工具 X 执行失败：...` 的 observation，让模型继续修复。

### 工具系统

工具统一使用 `Tool(name, description, parameters, run)`。默认注册：

- 通用开发：`read/write/bash/edit/grep/glob/task_list`
- 金融研究：`finance_*`
- 网页核验：`web_search/web_fetch`
- 微信连接：`wechat_status/wechat_send`
- 金融自进化：`finance_memory_add/finance_memory_list/finance_evolve_from_trace`
- 自进化：`trace2skill_generate`
- MCP：`mcp__echo`

`edit` 使用唯一 search-replace 策略：`old` 不存在或不唯一都会失败，避免误改。

### 上下文管理

`agent/context.py` 提供：

- `truncate_observation`: 长工具结果截断并标注总字符数。
- `maybe_compact`: 超预算时保留 system 和最近消息，把早期对话压缩成 system memo。

### MCP

`mcp/client.py` 实现 stdio JSON-RPC：

- `initialize`
- `tools/list`
- `tools/call`

默认连接 `python -m mcp.echo_server`，注册为 `mcp__echo`。演示命令：

```bash
python - <<'PY'
from tools.base import build_default_registry
tool = build_default_registry().get("mcp__echo")
print(tool.run(text="hello mcp"))
PY
```

### Skills

`skills/loader.py` 扫描 `skills/*/SKILL.md`，解析 frontmatter，生成可用 Skill 清单并注入系统提示词。当前包含：

- `finance-stock-research`
- `finance-research-evolution`
- `trace2skill`
- `example-skill`

### 微信连接

`wechat/connector.py` 使用适配器模式：

- 默认 dry-run 写入 `.finance_agent/wechat_outbox/`，不发网络请求。
- 配置 `FINANCE_WECHAT_WEBHOOK` 后发送企业微信/微信群机器人 webhook。
- 配置 `FINANCE_WECHAT_RELAY_URL` 后发送到本地 HTTP relay，便于接 WeChaty 或其他桥接器。

webhook、relay URL 和本地 outbox 都不写入仓库；`.finance_agent/` 已忽略。

### 金融自进化

`finance/evolution.py` 负责把用户偏好、纠错、数据源经验和风险规则写入 `.finance_agent/finance_memory.jsonl`。`finance_evolve_from_trace` 会从任务轨迹提炼金融学习点；默认只写 memory，核心 `skills/finance-research-evolution/SKILL.md` 保持稳定。需要生成新的专用 Skill 时，必须显式指定独立 `skill_name`。

这相当于把 Hermes 式“自动保存偏好、纠错和环境事实”的机制改造成金融研究专用版本：只保存可复用研究纪律，不保存隐私、密钥或一次性噪声。

### 安全层

`tools/security.py` 实现分层：

- 只读工具只能访问工作区内普通文件，阻止 `.env`、`.git` 等敏感路径。
- 写入和 edit 只能写工作区内普通文件，并拦截疑似 API key/token/secret。
- bash 只允许单条白名单命令；危险命令、多命令、管道、重定向、外传命令默认拦截。
- read/web_fetch 会给不可信内容加边界，提示模型不得执行内容中的指令。

红队演示：

```bash
python - <<'PY'
from tools.shell import bash_tool
try:
    print(bash_tool.run(command="rm -rf /tmp/demo"))
except Exception as exc:
    print(type(exc).__name__, exc)
PY
```

## Demo Day 命令

```bash
python -m agent.cli --selfcheck
python -m agent.cli /status
python -m agent.cli /tools
python -m agent.cli /mcp
python -m agent.cli /security
python -m agent.cli /wechat status
python -m agent.cli /memory list
python -m agent.cli /quality minimax 3mo
python -m agent.cli "帮我分析 AAPL 最近三个月走势，并生成投资研究摘要"
python -m agent.cli "帮我给 minimax 做质量门禁和去劣初筛"
```

## 评分表映射

- A: CLI 一键启动、README、模块化目录、MIT License。
- B: 金融随机任务通过符号解析、网页核验、行情、质量门禁、报告工具协同完成。
- C: ReAct 主循环和通用工具集已实现并测试。
- D: MCP echo server 已接入；Skills 加载器和金融 Skill 可用。
- E: compaction、observation 截断、工具错误 observation 已测试。
- F: 安全层、注入隔离、危险命令拦截已测试。
- G: 本文档可用于现场讲解设计取舍。
- H: `docs/ABLATION_REPORT.md` 给出消融实验。
