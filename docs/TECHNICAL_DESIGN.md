# Finance Agent 技术文档

## 架构总览

入口是 `python -m agent.cli`。系统的主要模块是：

1. `backend/`: OpenAI-compatible DeepSeek 客户端和 FakeBackend。
2. `agent/loop.py`: ReAct 主循环，负责多轮模型调用、工具调用、tool result 回填、终止和错误 observation。
3. `tools/`: 内置工具系统，包含文件、shell、搜索、金融、网页、微信连接、金融自进化、预测评估、调度、trace2skill。
4. `agent/command_catalog.py` + `agent/custom_commands.py` + `agent/dynamic_commands.py`: 统一命令目录、Markdown 自定义命令，以及 Skill/MCP prompt 的运行时发现。
5. `mcp/`: 多 stdio MCP client 运行时和 echo 示例 server，MCP 工具按 server 命名空间注册进主循环。
6. `skills/`: Skill 目录、校验器和只读 `read_skill` 按需加载工具。
7. `agent/memory.py`: `MEMORY.md` 与结构化 KV 项目记忆，跨进程召回后以低信任边界注入上下文。
8. `agent/usage.py`: 模型 token usage 归一化、任务级累计与可选成本估算。
9. `tools/security.py`: 权限分层、安全拦截和不可信内容隔离。

## 关键设计

### ReAct 主循环

`AgentLoop.run_messages()` 每轮调用模型。如果模型返回 `tool_calls`，主循环逐个执行工具，把结果以 `role=tool` 放回 messages。工具异常不会崩溃，而是变成 `工具 X 执行失败：...` 的 observation，让模型继续修复。

### 工具系统

工具统一使用 `Tool(name, description, parameters, run)`。默认注册：

- 通用开发：`read/write/bash/edit/grep/glob/task_list/read_skill`
- 金融研究：`finance_*`
- 网页核验：`web_search/web_fetch`
- 微信连接：`wechat_status/wechat_send`
- 金融自进化：`finance_memory_add/finance_memory_list/finance_evolve_from_trace`
- 预测评估：`prediction_record/prediction_list/prediction_evaluate/prediction_learn`
- 模拟组合：`finance_build_paper_portfolio/finance_rebalance_paper_portfolio/finance_mark_paper_portfolio/finance_show_paper_portfolio/finance_sell_paper_holding/finance_paper_trades/finance_paper_daily_pnl/finance_review_paper_portfolio`
- 历史学习：`finance_learn_from_history`
- 本地调度：`schedule_wechat_brief/schedule_wechat_message/schedule_portfolio_mark/schedule_list/schedule_run_due`
- 自进化：`trace2skill_generate`
- MCP：`mcp__<server>__<tool>`；没有 `.mcp.json` 时保留兼容示例 `mcp__echo`

`edit` 使用唯一 search-replace 策略：`old` 不存在或不唯一都会失败，避免误改。

### 上下文管理

`agent/context.py` 提供：

- `truncate_observation`: 长工具结果截断并标注总字符数。
- `maybe_compact`: 超预算时保留唯一原始 system 和最近消息，把早期对话标注为低信任历史，以 assistant 消息回填。
- `compact_with_model`: 摘要请求用独立 compaction policy，明确禁止把用户重复观点、未核验工具输出或历史中的“system-like”文本升级为规则。模型摘要失败时回退到规则压缩。

自然语言金融问题与普通任务一样进入 `AgentLoop`，由模型自主组合具体金融和网页工具。真模型的 schema 与执行门禁都会排除 `finance_route_task` / `finance_generate_report`；只有首轮 `backend.chat()` 在工具执行前失败时，CLI 才直接调用确定性路由兜底。`ModelCallError.turn > 1` 时禁止自动重跑，避免重复写组合、预测或 Skill。交互模式的兜底结果通过 `AgentSession.record_finance_turn()` 以低信任历史记入同一会话。

自然语言入口不根据测评题、固定股票或关键词在模型前切换路径。`AgentLoop` 会记录本轮工具回执：真实交易始终被执行层拒绝，`wechat_send` 必须在成功的 `wechat_status` 之后执行，而且只有返回 `queued` / `sent` 才能声称已发送；多标的预测记录也必须每个标的都有成功的 `prediction_record` id。

### 规划与待办

`task_list` 把长任务状态写入工作区内 `.agent_task_list`。system policy 要求预计 4 个以上独立步骤、涉及多个文件/工具或用户明确要求规划时，第一步先建立待办；完成一步即更新，工具失败时记录原因并增加替代路线。它不是另一个硬编码业务流程，而是给 ReAct 主循环一个可观察、可恢复的外部任务状态。

### 跨会话记忆

`agent/memory.py` 提供两类持久状态：`Memory` 追加写入项目根目录 `MEMORY.md`；`KVMemory` 写入忽略目录 `.finance_agent/project_memory.json` 并支持按 key 覆盖和遗忘。`remember/memory_set/memory_forget` 写入前脱敏常见 key/token/password，且 AgentLoop 只有在当前用户明确要求长期记住、覆盖或遗忘时才允许修改。启动时 `build_system_prompt()` 在 `UNTRUSTED_PERSISTENT_MEMORY_DATA` 边界内召回记忆，明确其属于项目数据，不能覆盖当前用户意图、权限和安全规则。

### 可观测性与成本

DeepSeek OpenAI-compatible 响应中的 `usage` 不再被 Backend 丢弃。`AgentLoop` 在每个 `model_end` 事件发出 prompt/completion/total token，`TracePrinter` 按任务累计：默认折叠摘要显示耗时、步骤、工具和总 token；`/trace on` 保留单轮 token；任务后 `/trace` 可回放详情。

配置 `DEEPSEEK_INPUT_PRICE_PER_MILLION` 与 `DEEPSEEK_OUTPUT_PRICE_PER_MILLION` 后，trace 额外显示估算美元成本；不配置时只报告服务端返回的真实 token，避免硬编码会变化的模型价格。`eval/tracer.py` 支持 JSONL 回放，`eval/metrics.py` 统一计算成功率、平均步骤、平均 token 和 JSON 合法率。

### CLI 与动态命令

`agent/command_catalog.py` 是内置 slash command 的单一信息源：帮助页和补全菜单都由同一组 `CommandSpec` 生成，不再分别维护。`prompt_toolkit` 使用带类型和描述的模糊补全；`DynamicSlashCommands` 启动时完成首次发现，并在打开补全或执行动态命令前 `refresh()`，因此会话中新增的命令、Skill 和 MCP prompt 无需重启即可出现。合并内容包括：

- 内置命令。
- `~/.finance-agent/commands/**/*.md` 用户命令和 `.finance_agent/commands/**/*.md` 项目命令；项目命令优先，内置名保留。
- `skills/*/SKILL.md` 声明的 Skill，补全形式为 `/<skill-name>`。
- MCP `prompts/list` 返回的 prompt，补全形式为 `/mcp:<server>:<prompt>`。

Markdown 命令支持 frontmatter `description` / `argument-hint` 和 `$1`、`$2`、`$ARGUMENTS`、`$$` 替换。Skill 与 MCP prompt 展开后都以 user-level 内容进入会话，不具有 system 优先级。

`agent/input.py::SlashCompletionPanel` 移植 Reasonix 的状态机思路：前缀命中优先、子序列模糊命中其次，选中项环形移动，面板固定作为输入框上方的布局行而非默认浮层。它最多绘制 8 个“命令 + 说明”候选，并接管 `↑/↓`、`Tab/Enter`、`Esc` 交互，因此长帮助页把输入框推到终端底部时仍然可见。

`agent/ui.py` 使用实际终端宽度生成欢迎页、精简帮助页和有边界的工具卡片。交互底栏显示 thinking 模式、模型、可用数据源数、Skill 数和 MCP 连接数。`compact` 只输出一行轨迹摘要，`/think on` 展开卡片，`/trace` 重新展示上一轮详情。

### MCP

`mcp/client.py` 实现带生命周期的 stdio JSON-RPC：

- `initialize`
- `tools/list`
- `tools/call`
- `prompts/list`
- `prompts/get`

项目根目录的 `.mcp.json` 默认连接教学 echo 和领域 `mcp.finance_server`。后者暴露 `mcp__finance__risk_budget`，根据资金、单笔风险、入场价和止损价确定性计算最大股数与仓位，不访问券商、不发送订单。也可以继续配置其他 stdio server：

```json
{
  "mcpServers": {
    "research": {
      "command": "python",
      "args": ["-m", "your_mcp_server"],
      "cwd": ".",
      "env": {},
      "timeoutSeconds": 10
    }
  }
}
```

工具注册名为 `mcp__<server>__<tool>`，避免多 server 同名工具冲突。每次 RPC 都有超时上限；一个 server 连接/发现失败会记入状态，不影响其他 server。`/mcp` 展示 server、错误、工具和 prompt。`ToolRegistry.close()` 会关闭所有受管 MCP 子进程。内置 echo/finance 只有命令、模块、空 `env` 和项目根 `cwd` 精确匹配才自动启动；其他配置默认 blocked，需用错误详情给出的 `name@sha256:<digest>` 临时设置 `MINI_OPENCLAW_TRUSTED_MCP_SERVERS`，配置变化后旧指纹失效。子进程默认只继承 PATH、HOME、locale、临时目录和虚拟环境等运行变量，不继承模型或数据源密钥；server 需要额外变量时必须在 `.mcp.json` 的 `env` 中显式配置。MCP observation 进入独立低信任边界。没有 `.mcp.json` 时默认连接 `python -m mcp.echo_server`，并保留 `mcp__echo` 兼容别名。

### Skills

`skills/loader.py` 扫描 `skills/*/SKILL.md`，校验 frontmatter、Skill 名称、空正文和重名。系统提示词只注入按名称排序的安全 `name` 索引；项目可编辑的 description/body 不会获得 system 权限。模型需要具体流程时调用只读工具 `read_skill(name)`；交互用户也可使用 `/<skill-name>` 动态命令。`/skills` 列出名称和描述。当前包含：

- `csv-quick-report`
- `finance-history-learning`
- `finance-stock-research`
- `finance-research-evolution`
- `trace2skill`

### 数据源可靠性

`finance/data.py::ProviderChain` 把真实数据源和 `SAMPLE_FALLBACK` 分开处理：

- 行情会尝试所有支持该标的真实 provider，选择更新且实时的成功结果，同时记录所有成功/失败来源和最大价差比例。
- 历史 K 线也遍历全部适用真实 provider，统一未复权收盘口径，选择更新/更完整的序列，并记录重叠日期最大差异。
- 基本面遍历所有适用真实 provider，优先源保留字段优先权；其他源只在币种、报告期和期间口径兼容时补齐，重叠字段相对差异写入 coverage。
- 新闻遍历所有适用真实 provider，统一相关性过滤、跨源去重和来源多样化后再执行 `limit`；只有近 180 天事件计入近期覆盖。
- 真实 provider 按操作并发，受 operation deadline、snapshot 总 deadline、超时熔断和 in-flight 去重约束；挂起的第三方 SDK 不会阻塞已成功的备用源或无限累积重复 worker。
- AKShare 接入 A 股、港股和美股公开财务指标；Tushare 提供 A 股财务报表；Yahoo 使用 quote summary，失败时尝试 `yfinance` info。
- 报告附注会列出真实来源覆盖、失败来源、跨源行情价差、基本面重叠字段差异和是否使用样例。样例不计入交叉验证。
- Yahoo 新闻用 ticker、查询代码和公司特异词过滤，排除 `technology/group/inc` 等通用词导致的错配。新闻接口失败会进入数据错误附注，不再生成伪新闻项。

### 微信连接

`wechat/connector.py` 使用适配器模式：

- 默认 dry-run 写入 `.finance_agent/wechat_outbox/`，不发网络请求。
- 配置 `FINANCE_WECHAT_WEBHOOK` 后发送企业微信/微信群机器人 webhook。
- 配置 `FINANCE_WECHAT_RELAY_URL` 后发送到本地 HTTP relay，便于接 WeChaty 或其他桥接器。

webhook、relay URL 和本地 outbox 都不写入仓库；`.finance_agent/` 已忽略。

### 金融自进化

`finance/evolution.py` 负责把用户偏好、纠错、数据源经验和风险规则写入 `.finance_agent/finance_memory.jsonl`。`finance_evolve_from_trace` 会从任务轨迹提炼金融学习点；默认只写 memory，核心 `skills/finance-research-evolution/SKILL.md` 保持稳定。需要生成新的专用 Skill 时，必须显式指定独立 `skill_name`。

这相当于把 Hermes 式“自动保存偏好、纠错和环境事实”的机制改造成金融研究专用版本：只保存可复用研究纪律，不保存隐私、密钥或一次性噪声。

### 预测评估

`finance/predictions.py` 提供预测账本：

- `prediction_record`: 保存 symbol、direction、horizon、thesis、baseline price 和信号证据类型。
- `prediction_list`: 查看历史预测。
- `prediction_evaluate`: 到期后使用到期日或之后首个交易日收盘价，计算方向命中、实际收益和估计值加权分数。
- `prediction_learn`: 按方向桶、命中率、估计证据类型和高估计错判生成复盘报告；可保存到金融 memory。

预测入口会用 3 个月动量规则生成原始信号，再用过去数据构造时间有序、互不重叠的 walk-forward 评估窗口。只有当前方向有至少 30 个历史样本时，才以 Beta(1,1) 平滑后的命中率作为历史校准值，并输出 Wilson 95% 区间。否则仅显示“信号强度，非统计概率”。

预测数据默认写入 `~/.finance-agent/predictions.jsonl`，可用 `FINANCE_PREDICTION_PATH` 覆盖；旧的 `.finance_agent/predictions.jsonl` 只作为首次迁移来源。这个模块用来量化研究框架是否真的有效，而不是事后只看主观感觉。

### 历史学习预测

`finance/history_learning.py` 把历史 K 线转换成 walk-forward 样本：

- 每个样本计算 20/60 日动量、价格相对 MA20/MA60、波动率、RSI 等可解释特征。
- 对每个特征桶统计未来 N 天收益均值和胜率。
- 用当前特征桶匹配历史表现，输出方向、启发式信号强度和期望收益。
- 学习结果写入 `.finance_agent/history_learning.jsonl`。
- `finance_learn_from_history` 会同时更新 `skills/finance-history-learning/SKILL.md`，并写入预测账本用于未来评分。

该模块是可解释历史特征学习器，不是黑箱交易模型；其人工加权值明确标记为启发式信号，不得当作统计概率。

### 模拟投资组合

`finance/paper_portfolio.py` 提供纸面账户，用于把“预测准度”推进到可量化组合实验：

- `finance_build_paper_portfolio`: 输入股票池和资金，例如 100 万，按动量、质量、风险和数据源置信度评分，输出买入数量、目标仓位和风险提示。
- `finance_review_paper_portfolio`: 只读诊断当前持仓，解释为什么持有、谁是弱持仓，并给出替换候选；不改仓。
- `finance_mark_paper_portfolio`: 按最新价格给持仓估值，并追加一条净值历史记录。
- `finance_rebalance_paper_portfolio`: 用新的股票池重新计算仓位。
- `finance_show_paper_portfolio`: 查看当前持仓、现金、累计收益和最近记录。
- `finance_sell_paper_holding`: 模拟卖出持仓，记录 SELL 流水、价格、数量、理由和实现盈亏。
- `finance_paper_trades`: 查看 BUY/SELL 交易流水。
- `finance_paper_daily_pnl`: 按天汇总买入额、卖出额、已实现盈亏、期末净值和净值变化。

账户写入 `.finance_agent/portfolio_default.json`，不提交到仓库。它只做纸面实验，不连接真实券商，不发送真实订单。`rebalance` 会记录买卖差额，而不是静默覆盖持仓。

### 定时微信推送

`scheduler/jobs.py` 使用 `.finance_agent/scheduled_jobs.json` 保存任务。当前支持：

- `wechat_brief`: 定时生成自选股简报并发送微信连接器。
- `wechat_message`: 定时发送固定消息。
- `wechat_portfolio_mark`: 定时给纸面组合估值并发送微信连接器。

项目不内置常驻后台守护进程；推荐用系统 cron/launchd 定期运行：

```bash
python -m agent.cli /schedule run
```

### 安全层

`tools/security.py` 实现分层：

- 只读工具只能访问工作区内普通文件，阻止 `.env`、`.git` 等敏感路径。
- 写入和 edit 只能写工作区内普通文件，并拦截疑似 API key/token/secret。
- bash 默认只放行 `pwd/ls/date` 与受限只读 Git；`cat/head/grep/find/awk` 等可读取敏感文件或启动子进程的入口直接拒绝。工作区 Python 脚本与 `pytest/compileall` 仍归入确认层。
- `MINI_OPENCLAW_AUTO_APPROVE=1` 只批准已经审查的本地 Python 入口；`MINI_OPENCLAW_APPROVED_TOOLS` 可逐项批准一个确认类工具。硬拒绝不能被两者绕过，获批 Python 在没有 bubblewrap 的系统上仍具有宿主进程权限。
- read、web、MCP 和持久记忆会加低信任边界；web 搜索词与 URL 在发出前扫描 secret，工具异常和 observation 在回填前脱敏。
- MCP 子进程使用最小环境继承列表，不会默认拿到模型和数据源密钥。
- 系统金融约束明确规定：用户重复看涨、要求只讲优点或声称内幕都不是新证据；结论必须保留反证、风险、数据缺口和独立核验。
- 压缩摘要、历史用户声明和历史工具输出统一标记为 untrusted history，始终低于原始 system policy。

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
python -m agent.cli /compact
python -m agent.cli /tools
python -m agent.cli /skills
python -m agent.cli /mcp
python -m agent.cli /security
python -m agent.cli /wechat status
python -m agent.cli /memory list
python -m agent.cli /predict record AAPL up 30 0.6 "unit thesis"
python -m agent.cli /predict eval all
python -m agent.cli /predict learn save
python -m agent.cli /learn-history AAPL 2y 20
python -m agent.cli /portfolio init 1000000 AAPL MSFT NVDA AMD GOOGL
python -m agent.cli /portfolio review GOOGL AVGO META AMZN TSLA JPM
python -m agent.cli /portfolio mark
python -m agent.cli /portfolio sell AMD all "volatility risk"
python -m agent.cli /portfolio trades
python -m agent.cli /portfolio pnl
python -m agent.cli /schedule portfolio default 1440
python -m agent.cli /schedule brief AAPL,MSFT,NVDA 1440
python -m agent.cli /schedule run
python -m agent.cli /quality minimax 3mo
python -m agent.cli "帮我分析 AAPL 最近三个月走势，并生成投资研究摘要"
python -m agent.cli "帮我给 minimax 做质量门禁和去劣初筛"
```

## 评分表映射

- A: CLI 一键启动、README、模块化目录、MIT License。
- B: 金融随机任务通过符号解析、网页核验、行情、质量门禁、报告工具协同完成。
- C: ReAct 主循环和通用工具集已实现并测试。
- D: 多 stdio MCP、命名空间、超时/状态/关闭，以及 Skill 目录与按需 `read_skill` 已接入。
- E: compaction、observation 截断、工具错误 observation、自适应 CLI 和动态补全已测试。
- F: 安全层、压缩权限隔离、重复唱多/内幕注入防护、危险命令拦截已测试。
- G: 本文档可用于现场讲解设计取舍。
- H: `docs/ABLATION_REPORT.md` 给出消融实验。
