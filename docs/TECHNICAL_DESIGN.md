# Finance Agent 技术文档

## 架构总览

入口是 `python -m agent.cli`。系统的主要模块是：

1. `backend/`: OpenAI-compatible DeepSeek 客户端和 FakeBackend。
2. `agent/loop.py`: ReAct 主循环，负责多轮模型调用、工具调用、tool result 回填、终止和错误 observation。
3. `tools/`: 内置工具系统，包含文件、shell、搜索、金融、网页、微信连接、金融自进化、预测评估、调度、trace2skill。
4. `agent/command_catalog.py` + `agent/custom_commands.py` + `agent/dynamic_commands.py`: 统一命令目录、Markdown 自定义命令，以及 Skill/MCP prompt 的运行时发现。
5. `mcp/`: 多 stdio MCP client 运行时和 echo 示例 server，MCP 工具按 server 命名空间注册进主循环。
6. `skills/`: Skill 目录、校验器和只读 `read_skill` 按需加载工具。
7. `tools/security.py`: 权限分层、安全拦截和不可信内容隔离。

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

确定性 `finance_route_task` 产生的问答会通过 `AgentSession.record_finance_turn()` 记入同一会话，因此后续代词问题可以引用上一轮标的，不会因为绕过模型主循环而丢失上下文。

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

项目根目录的 `.mcp.json` 可配置多个 stdio server：

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

工具注册名为 `mcp__<server>__<tool>`，避免多 server 同名工具冲突。每次 RPC 都有超时上限；一个 server 连接/发现失败会记入状态，不影响其他 server。`/mcp` 展示 server、错误、工具和 prompt。`ToolRegistry.close()` 会关闭所有受管 MCP 子进程。没有 `.mcp.json` 时默认连接 `python -m mcp.echo_server`，并保留 `mcp__echo` 兼容别名。

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

- `prediction_record`: 保存 symbol、direction、horizon、confidence、thesis、baseline price。
- `prediction_list`: 查看历史预测。
- `prediction_evaluate`: 到期后拉取最新价格，计算方向命中、实际收益和置信度加权分数。
- `prediction_learn`: 按方向桶、命中率、置信度失误和高置信错判生成复盘报告；可保存到金融 memory。

预测数据写入 `.finance_agent/predictions.jsonl`，不提交到仓库。这个模块用来量化研究框架是否真的有效，而不是事后只看主观感觉。

### 历史学习预测

`finance/history_learning.py` 把历史 K 线转换成 walk-forward 样本：

- 每个样本计算 20/60 日动量、价格相对 MA20/MA60、波动率、RSI 等可解释特征。
- 对每个特征桶统计未来 N 天收益均值和胜率。
- 用当前特征桶匹配历史表现，输出方向、置信度和期望收益。
- 学习结果写入 `.finance_agent/history_learning.jsonl`。
- `finance_learn_from_history` 会同时更新 `skills/finance-history-learning/SKILL.md`，并写入预测账本用于未来评分。

该模块是可解释校准器，不是黑箱交易模型；样本不足或匹配不足时会降置信度。

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
- bash 只允许单条白名单命令；危险命令、多命令、管道、重定向、外传命令默认拦截。
- read/web_fetch 会给不可信内容加边界，提示模型不得执行内容中的指令。
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
