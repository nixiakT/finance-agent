# Finance Agent 计划与进度

## 项目定位

把 mini-OpenClaw 扩展成金融股票研究助手。系统只做研究、解释、回测和策略辅助，不做自动下单，也不输出确定性买卖建议。

核心原则：
- 数据必须标注来源、时间和是否为实时/准实时。
- 结论必须区分事实、推断和风险。
- 任何策略结果必须说明回测假设和局限。
- API 不可用时可以降级，但必须明确说明降级来源。

## 实现计划

1. 数据层
   - 统一股票代码规范化。
   - 支持实时/准实时行情、历史 K 线、基本面、新闻。
   - 数据 Provider 可替换，先实现 Alpha Vantage/Tushare/AKShare/Yahoo Finance/样例 fallback。

2. 分析层
   - 技术指标：MA5、MA20、MA60、RSI、MACD、波动率、1 月/3 月/1 年收益率。
   - 基本面摘要：估值、盈利、市值、现金流等字段，缺失时明确说明。
   - 投资框架：巴菲特/芒格、段永平、达利欧三类检查清单。

3. Agent 工具化
   - `finance_get_quote`
   - `finance_get_price_history`
   - `finance_get_financials`
   - `finance_get_news`
   - `finance_calculate_indicators`
   - `finance_generate_report`
   - `finance_compare_stocks`
   - `finance_debate_stocks`
   - `finance_backtest_strategy`
   - `finance_daily_brief`

4. 多智能体辩论
   - 多头、空头、价值、宏观、风险、裁判六个角色。
   - 输出主要分歧、共识、跟踪结论和需要继续验证的问题。

5. 策略辅助
   - 先实现移动均线交叉策略回测。
   - 支持从自然语言提取常见窗口参数。
   - 输出收益率、最大回撤、夏普、交易次数、胜率。

6. 自进化能力
   - 从成功任务轨迹、复盘记录和工具调用日志中提炼新的 Skill。
   - 自动脱敏密钥，默认写入项目内 `skills/` 目录。

## 进度记录

### 2026-07-06

- [x] 初始化 GitHub 仓库并推送首次提交。
- [x] 明确产品方向：股票研究助手，不做自动交易。
- [x] 确认当前骨架状态：默认工具注册表为空，CLI/FakeBackend/AgentLoop 有最小主循环。
- [x] 创建本进度文档，作为后续计划、进度和功能记录。
- [x] 实现金融核心模块。
- [x] 注册金融工具。
- [x] 增加金融 Skill。
- [x] 补充 README 和演示命令。
- [x] 运行自检并提交推送。
- [x] 接入本地 `.env.local` 配置读取，避免把 key 推到仓库。
- [x] 兼容带 `/v1` 的 OpenAI-compatible base URL。
- [x] 接入 Tushare/AKShare 可选 A 股数据 Provider。
- [x] 增加 `trace2skill` Skill 和 `trace2skill_generate` 工具。
- [x] 优化 CLI：无参数启动显示招财猫欢迎页，`/help` 显示功能菜单。
- [x] 优化 CLI：无参数启动进入持续交互会话，支持 `/help`、`/clear`、`/selfcheck`、`/exit`。
- [x] 增加 slash commands：`/quote`、`/history`、`/financials`、`/news`、`/indicators`、`/report`、`/compare`、`/debate`、`/backtest`、`/brief`、`/tools`、`/sources`。
- [x] 增加 `/think on|off`，展示高层执行轨迹、工具调用和结果摘要。
- [x] 修复智谱/港股标的识别：`智谱`、`智谱AI`、`02513` 归一为 `02513.HK`。
- [x] 修复 Yahoo 港股查询格式：展示 `02513.HK`，查询 Yahoo 时转换为 `2513.HK`。
- [x] 增加网页核验能力：`web_search`、`web_fetch` 工具，以及 CLI `/search`、`/fetch` 命令。
- [x] 收紧未知标的 fallback：未知代码不再生成通用样例财务数据，避免把演示数据误当真实数据。
- [x] 增加 snapshot 容错：行情、历史、基本面、新闻可独立失败并在报告中明确标注。
- [x] 修复 CLI 输入体验：接入 `prompt_toolkit`，支持历史记录、光标移动、Backspace/Delete、Ctrl+A/E/U/K 和 slash command 补全。
- [x] 修复重复提示符污染：自动清理用户误粘贴的 `finance-agent >` 前缀。
- [x] 修复 `prompt_toolkit` 下 ANSI 颜色码原样显示的问题，使用 formatted ANSI prompt 渲染。
- [x] 优化欢迎页视觉：重绘“招财进宝”金融猫 Logo，保持固定宽度和中英文对齐。
- [x] 参考 Hermes 风格重构欢迎页：双栏启动面板，展示品牌视觉、工具、数据源、命令、会话和风险边界。
- [x] 加强欢迎页金色品牌区：左侧招财猫/研究卡片整体使用金色，补齐模型、模式和边界信息，减少空白。
- [x] 按参考图片重绘招财猫形象：用线条和符号表现笑脸猫、招手、身体、坐垫和金币点缀，中文只保留“招财进宝符”。

### 2026-07-07

- [x] 修正 CLI 欢迎页招财猫：去掉用中文代替形象部件的文字，图形区只保留“招财进宝符”。
- [x] 收敛 README：移除通用课程骨架叙述，明确项目是 finance-agent。
- [x] 增加 Agent 主循环上下文保护：工具 observation 截断、长会话 compaction 和 `/think on` 可见提示。
- [x] 增加 `FINANCE_ALLOW_SAMPLE_FALLBACK=0`，可在严肃研究时禁用样例 fallback。
- [x] 增强 `/sources`：展示数据源 enabled/disabled 状态和缺失 token 说明。
- [x] 支持单次 slash command：`python -m agent.cli /tools`、`python -m agent.cli /sources` 等无需进入交互模式。
- [x] 增加 pytest 回归测试，覆盖符号归一、Provider fallback、样例 fallback 开关、路由、回测、上下文截断和 slash command。
- [x] 修复网页核验失败路径：`web_search` 遇到 `No route to host` 等连接错误时返回公开财经页面 fallback，而不是让 Agent 直接放弃联网。
- [x] 增加“今天/今日/最新/情况”市场核验路由：先网页核验，再输出行情、技术面和新闻摘要。
- [x] 修复单次 slash command 多参数解析：`python -m agent.cli /search 智谱 02513 股票` 可直接运行。
- [x] 自测迭代：未知标的 slash command 不再 traceback，返回可读的数据获取失败信息。
- [x] 自测迭代：基本面来自样例 fallback 或不可用时，不再对巴菲特/段永平/达利欧框架打分。
- [x] 自测迭代：Yahoo 新闻结果增加标的相关性过滤，避免把无关股票新闻放进报告。
- [x] 自测迭代：回测窗口倒置时明确说明规范化结果，并去重提示。
- [x] 自测迭代：改用 timezone-aware UTC 时间，消除 Python 3.13 `datetime.utcnow()` 弃用 warning。
- [x] 增加通用标的解析：`finance_resolve_symbol` / `/resolve` 可用公司名、简称、中文名、英文名动态解析 A 股、港股、美股候选，不再依赖逐个硬编码。
- [x] 修复 MiniMax 查询：`minimax`、`稀宇科技` 等名称优先通过东方财富/Yahoo/web 搜索解析到港股候选，再查行情。
- [x] 参考 Claude Code 的终端执行可见性，默认开启高层 `thinking` 轨迹。
- [x] `thinking` 轨迹增加本地时间、模型回合、工具选择、工具参数摘要、结果预览和耗时。
- [x] 单次自然语言任务和单次 slash command 默认展示 trace；交互模式仍可用 `/think off` 关闭。
- [x] 增加 MIT License。
- [x] 参考 AI Berkshire 的研究纪律，增加信息丰富度 A/B/C、数据缺口、快速否决/重审信号和下一步核验。
- [x] 增加 `finance_quality_screen` 工具和 `/quality` 命令，用于研究质量门禁和去劣初筛。
- [x] 增加 `/status` 命令，快速展示模型、base URL、工具数、数据源、thinking 状态和 License。
- [x] 补齐 Demo Day 必考通用工具：`read/write/bash/edit/grep/glob/task_list`。
- [x] 实现最小 stdio MCP client，默认接入 echo server，并注册 `mcp__echo`。
- [x] 增加安全层：工作区路径限制、敏感路径拦截、危险命令拦截、疑似 secret 写入拦截、不可信内容隔离。
- [x] 增加 `/mcp` 和 `/security` 命令，方便现场展示扩展能力和安全策略。
- [x] 增加技术文档 `docs/TECHNICAL_DESIGN.md` 和消融实验报告 `docs/ABLATION_REPORT.md`。
- [x] 增加可配置 HTTP 代理：`FINANCE_HTTP_PROXY` 和 `/proxy status/test/set/off`，网页搜索、抓取、Yahoo、Eastmoney 等查询统一走代理。
- [x] 修复 SpaceX 最新上市核验路径：`SpaceX` 解析为 `SPCX`，市场更新增加“上市状态与代码核验”段落。
- [x] CLI 支持中英文切换：`FINANCE_AGENT_LANG=zh|en` 和 `/lang zh|en`；README 增加 English Quick Start。
- [x] 单次和交互自然语言金融查询优先走确定性 `finance_route_task`，防止新上市/改名标的被模型旧知识误判；普通开发任务仍走 ReAct 主循环。
- [x] 增加微信连接适配器：默认 dry-run outbox，支持企业微信 webhook 和本地 HTTP relay。
- [x] 增加金融自进化 memory：保存偏好、纠错、数据源经验、风险规则，并支持从轨迹更新 `finance-research-evolution` Skill。
- [x] 增加预测记录、事后评分和复盘学习：保存 baseline、方向、期限、置信度和 thesis，用真实后续价格评估命中率，并按方向桶/高置信错判复盘；复盘可保存进金融 memory。
- [x] 增加微信定时推送任务：本地任务表 + `/schedule run`，可由 cron/launchd 驱动每日简报。
- [x] 增强多智能体辩论：加入 Buffett、Munger、Duan、Dalio、Anti-Bias 角色和可检验预测字段。

## 已实现功能

- 数据层：`ProviderChain`，支持 Alpha Vantage、Tushare、AKShare、Yahoo Finance public endpoints 和样例 fallback。
- 通用工具层：`read/write/bash/edit/grep/glob/task_list`，用于现场随机代码任务。
- MCP：最小 JSON-RPC stdio client 和 `mcp__echo` 工具已透明并入默认工具注册表。
- 安全层：`tools/security.py` 统一处理路径、写入、shell 和不可信内容边界。
- 行情：`finance_get_quote`。
- 历史价格：`finance_get_price_history`，支持摘要和 CSV。
- 基本面：`finance_get_financials`。
- 新闻：`finance_get_news`。
- 技术指标：`finance_calculate_indicators`，包含 MA5/20/60、RSI14、MACD、年化波动率和区间收益。
- 研究报告：`finance_generate_report`。
- 研究质量门禁：`finance_quality_screen` 和 `/quality`，输出信息丰富度、数据完整性、快速否决/重审信号和下一步核验。
- 多股票对比：`finance_compare_stocks`。
- 多智能体辩论：`finance_debate_stocks`。
- 策略回测：`finance_backtest_strategy`，第一版支持移动均线交叉。
- 自选股简报：`finance_daily_brief`。
- 离线路由：未配置真模型时，`FakeBackend` 会用 `finance_route_task` 跑通金融 Demo。
- 确定性金融路由：配置真模型时，自然语言金融查询也会先走 `finance_route_task` 做标的解析、网页核验、行情、技术面和新闻，再输出报告。
- Skill：`skills/finance-stock/SKILL.md` 规定金融分析边界和流程。
- Trace2Skill：`skills/trace2skill/SKILL.md` 和 `trace2skill_generate` 支持从成功轨迹生成新 Skill。
- Finance Evolution：`finance_memory_add/list` 和 `finance_evolve_from_trace` 支持金融偏好、纠错、数据源经验和研究流程沉淀。
- WeChat Connector：`wechat_status/wechat_send` 与 `/wechat` 支持企业微信群机器人、本地 relay 和 dry-run outbox。
- Prediction Ledger：`prediction_record/list/evaluate/learn` 与 `/predict` 支持记录预测、未来评分和历史复盘。
- Scheduler：`schedule_wechat_brief/message/list/run` 与 `/schedule` 支持定时微信简报。
- CLI 欢迎页：`python -m agent.cli` 显示招财猫入口。
- CLI 品牌页：欢迎页包含“招财进宝”金融猫、研究边界和核心能力入口。
- CLI 启动面板：双栏展示 Logo、Available Tools、Market Sources、Commands、Session 和 Boundary。
- CLI 金色品牌区：左侧完整卡片展示招财进宝猫、模型、research only 和 no auto trading。
- CLI 招财猫造型：左侧 Logo 使用照片风格的符纸、笑脸猫、招手、身体、坐垫和金币点缀；图形区中文只保留“招财进宝符”。
- CLI 帮助菜单：`python -m agent.cli /help` 显示功能列表和示例命令。
- CLI 交互模式：`python -m agent.cli` 后可在同一进程中持续提问，复用会话上下文。
- CLI 命令模式：常用金融工具有对应 slash command，可绕过自然语言路由直接执行。
- CLI 高层 trace：默认展示模型回合、工具调用、结果摘要、时间戳和耗时，不输出隐藏推理链；可用 `/think off` 关闭。
- CLI 状态面板：`/status` 展示模型、数据源、工具数、thinking 和 License。
- CLI 代理诊断：`/proxy test` 可验证 Clash/Mihomo 等本地代理是否可用。
- CLI 双语界面：欢迎页和 `/help` 支持中文/英文。
- CLI 行编辑：支持历史记录、方向键、删除键、常见 Emacs 快捷键和命令补全。
- CLI 输入清洗：误粘贴 `finance-agent >` 前缀时会自动剥离。
- 标的核验：自然语言包含“标的/代码/上市”等问题时，先做公开网页搜索，再做行情核验。
- 今日市场核验：自然语言包含“今天/今日/最新/情况”等时效性问题时，先做网页核验，再输出行情、技术面和新闻摘要。
- 网页工具：`web_search` 使用公开搜索结果核验来源；搜索入口失败时会生成公开财经页面 fallback；`web_fetch` 抓取指定 URL 并标注 WAF/JS/连接限制。
- 新闻过滤：Yahoo 新闻会按 symbol、查询代码、公司名关键词过滤，过滤后为空时明确说明相关新闻不足。
- 错误呈现：slash command 捕获数据源错误并返回用户可读信息，避免 Python traceback 泄漏到 CLI。
- 标的解析：`finance_resolve_symbol` 使用东方财富 suggest、Yahoo Finance search、AKShare 和网页搜索 fallback 解析 A 股/港股/美股候选。

## 使用说明

```bash
python -m agent.cli --selfcheck
python -m agent.cli
python -m agent.cli /help
python -m agent.cli "分析一下 AAPL 最近三个月走势，并生成投资研究摘要"
python -m agent.cli "比较 NVDA 和 AMD 的基本面和技术面"
python -m agent.cli "用巴菲特、段永平、达利欧三个视角分析 NVDA，并让多智能体辩论是否值得继续跟踪"
python -m agent.cli "帮我回测 TSLA 的 20 日均线上穿 60 日均线策略"
python -m agent.cli "生成我的自选股每日简报：AAPL, MSFT, NVDA"
```

可选环境变量：

```bash
export DEEPSEEK_API_KEY="..."
export ALPHAVANTAGE_API_KEY="..."
export TUSHARE_TOKEN="..."
```

也可以复制 `.env.example` 到 `.env.local`。`.env.local` 已被 git 忽略，不会提交。

## 已知限制

- 数据源的实时性取决于 API 供应商、市场和网络环境。
- 免费数据源可能限流、延迟或缺失部分基本面字段。
- Yahoo Finance 的部分基本面端点可能返回权限/crumb 错误；报告会标注字段缺失，不再用未知标的样例数据填充。
- Tushare 需要 token 和对应接口权限；AKShare 依赖上游公开页面结构，可能随页面变化失效。
- 回测不包含滑点、手续费、分红复权和真实成交约束，第一版只用于研究。
- 若运行环境没有安装 `prompt_toolkit`，CLI 会回退到 `readline/input`，功能取决于终端对 readline 的支持。
- 部分通用 starter 模块仍是课程占位实现，例如 filesystem/shell、MCP 客户端和纯文本 prompt renderer；当前产品主线是金融研究 Agent。

## 验证记录

2026-07-06 已运行：

```bash
python -m compileall agent backend finance skills tools
python -m agent.cli --selfcheck
python -m agent.cli "分析一下 AAPL 最近三个月走势，并生成投资研究摘要"
python -m agent.cli "比较 NVDA 和 AMD 的基本面和技术面"
python -m agent.cli "用巴菲特、段永平、达利欧三个视角分析 NVDA，并让多智能体辩论是否值得继续跟踪"
python -m agent.cli "帮我回测 TSLA 的 20 日均线上穿 60 日均线策略"
python -m agent.cli "生成我的自选股每日简报：AAPL, MSFT, NVDA"
```

验证结果：
- 11 个金融工具已注册。
- `finance-stock-research` Skill 可加载。
- 未配置 `DEEPSEEK_API_KEY` 时，FakeBackend 可把金融任务路由到 `finance_route_task` 并返回完整报告。
- Yahoo 行情时间戳超过 36 小时时会标注为非实时/延迟数据。
- 基本面降级到 `SAMPLE_FALLBACK` 时，报告和辩论裁判都会降低数据置信度。

追加验证：
- `.env.local` 被 `.gitignore` 忽略，未进入 git status。
- `DEEPSEEK_BASE_URL=https://api.penguinsaichat.dpdns.org/v1` 会规范化为不重复拼接 `/v1`。
- 本地验证 `/v1/models` 可访问，`DEEPSEEK_MODEL=gpt-5.5-openai-compact` 可返回 `OK`。
- 未安装 `tushare/akshare` 时 Provider 链保持可运行，并自动回退到后续数据源。
- `trace2skill_generate` 可创建新 Skill，并脱敏 `sk-...` 风格密钥。

智谱/港股修复验证：
- `normalize_symbol("智谱") -> 02513.HK`。
- `to_yahoo_symbol("02513.HK") -> 2513.HK`。
- `/search 智谱 02513 股票` 返回新浪、东方财富、雪球、同花顺、Yahoo 财经等公开页面。
- `/quote 智谱` 返回 Yahoo Finance public endpoints 的 `2513.HK` 行情，并在备注中说明展示代码为 `02513.HK`。
- `/fetch https://xueqiu.com/S/02513` 能识别雪球 WAF/JS challenge，不再假装读取完整正文。

CLI 输入修复验证：
- `clean_user_input("finance-agent > finance-agent > /quote 智谱") -> /quote 智谱`。
- `InteractiveInput` 在 TTY 中优先使用 `prompt_toolkit`，并维护 `~/.finance_agent_history`。
- 非 TTY 管道输入仍保持兼容。
- PTY 回归验证确认 prompt 不再显示 `^[[38;...` 转义乱码。

2026-07-07 质量改进验证：

```bash
python -m compileall agent backend finance mcp skills tools trace2skill wechat scheduler tests
python -m pytest
python -m agent.cli --selfcheck
python -m agent.cli /tools
python -m agent.cli /sources
```

结果：
- `compileall` 通过。
- `pytest` 通过 11 个测试；本机 xonsh history 权限 warning 不影响项目测试。
- 自检通过，当前注册工具随版本扩展；最新包含金融、网页、MCP、微信连接和金融自进化工具。
- `/tools` 和 `/sources` 可在单次命令模式运行。
