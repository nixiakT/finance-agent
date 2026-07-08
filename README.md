Language / 语言: 中文 | [English](README_EN.md)

# finance-agent

命令行股票研究助手。它面向行情查询、基本面研究、新闻核验、技术指标、多智能体辩论和简单策略回测，只做研究辅助，不做自动交易。

## 能力

- 股票行情：价格、涨跌、成交量、市值、数据源和时间。
- 标的解析：公司名、简称、中文名、英文名或 ticker 自动解析为 A 股/港股/美股候选代码。
- 历史价格与技术指标：MA5 / MA20 / MA60、RSI14、MACD、波动率、近 1 月 / 3 月 / 1 年收益率。
- 基本面：PE、EPS、营收、利润、现金流、ROE、利润率等字段，缺失时明确标注。
- 新闻和网页核验：搜索公开页面或抓取指定 URL，确认代码、上市状态和来源。
- 结构化报告：价格、走势、基本面、技术面、新闻、风险和研究结论。
- 研究质量门禁：信息丰富度 A/B/C、数据缺口、快速否决/重审信号、下一步核验。
- 投资框架：巴菲特/芒格、段永平、李录、达利欧。
- 多智能体辩论：Bull、Bear、Value、Buffett、Munger、Duan、Li Lu、Dalio、Anti-Bias、Macro、Risk、Judge，并输出纪律结论、镜子测试和可检验预测。
- 预测评分闭环：记录每次看涨/看跌/中性判断，按真实后续价格评估命中率、置信度和高置信错判。
- 历史学习预测：从历史 K 线 walk-forward 学习可解释特征，生成方向/置信度，并沉淀为 Skill。
- 模拟投资账户：给 agent 100 万纸面资金，按股票池评分、计算买入数量和仓位，并每日记录净值。
- 策略辅助：移动均线交叉策略回测。
- 自选股简报：批量生成跟踪摘要。
- 微信连接与定时推送：支持 dry-run outbox、企业微信 webhook、本地 relay 和本地定时简报任务。
- Trace2Skill：把成功任务轨迹沉淀为项目 Skill。
- 通用 Agent 工具：read/write/bash/edit/grep/glob/task_list，支持现场随机代码任务。
- MCP：最小 stdio client 已接入 echo server，MCP 工具以 `mcp__` 前缀透明并入主循环。
- 安全层：工作区权限、危险命令拦截、疑似 secret 写入拦截、不可信内容隔离。

## 快速开始

```bash
pip install -r requirements.txt

python -m agent.cli --selfcheck
python -m agent.cli
```

进入交互模式后可以持续对话：

```text
finance-agent > /help
finance-agent > /lang en
finance-agent > 分析一下 AAPL 最近三个月走势
finance-agent > /think off
finance-agent > /proxy test
finance-agent > /quote AAPL
finance-agent > /wechat status
finance-agent > /memory add 以后港股报告要同时说明展示代码和 Yahoo 查询代码
finance-agent > /search 智谱 02513 股票
finance-agent > /fetch https://xueqiu.com/S/02513
finance-agent > /exit
```

也支持单次任务：

```bash
python -m agent.cli "分析一下 AAPL 最近三个月走势，并生成投资研究摘要"
python -m agent.cli "比较 NVDA 和 AMD 的基本面和技术面"
python -m agent.cli "用巴菲特、段永平、达利欧三个视角分析 NVDA，并让多智能体辩论是否值得继续跟踪"
python -m agent.cli "帮我回测 TSLA 的 20 日均线上穿 60 日均线策略"
python -m agent.cli "生成我的自选股每日简报：AAPL, MSFT, NVDA"
python -m agent.cli "给 agent 100 万模拟投资 AAPL, MSFT, NVDA, AMD，告诉我买哪些、买多少"
```

## 常用命令

```text
/think on | compact | off    切换高层执行轨迹：展开、折叠摘要或隐藏
/trace                       展开上一轮任务的详细 thinking 轨迹
/lang zh | /lang en          切换 CLI 交互语言
/status                      查看模型、数据源、工具数、thinking 状态和 License
/compact                     用模型摘要压缩当前交互会话历史，保留最近上下文
/proxy status/test/set/off   查看、测试、临时设置或关闭网页/行情查询代理
/wechat status/send/send-md  查看微信连接状态，或发送报告到微信/本地 outbox
/memory list/add             查看或新增金融研究偏好、纠错和风险规则
/evolve <复盘/纠错/轨迹>       把金融经验沉淀为 memory 和 Skill
/predict record/list/eval/learn
                              记录预测、查看预测账本、事后评分和复盘学习
/learn-history AAPL 2y 20     从历史数据学习预测规则，记录预测并更新 Skill
/portfolio init/status/mark/sell/trades/rebalance
                              创建 100 万纸面组合、查看持仓、每日估值、模拟卖出、交易流水、再平衡
/schedule list/brief/portfolio/run
                              创建微信定时简报或组合每日估值任务，或执行到期任务
/mcp                         查看已接入 MCP 工具
/security                    查看权限分层和注入防护策略
/resolve minimax             解析公司名/简称到 A 股、港股、美股候选代码
/quote AAPL                  查询行情
/quality AAPL 1y             研究质量门禁和去劣初筛
/history AAPL 1y             历史价格和指标摘要
/financials AAPL             基本面摘要
/news AAPL 5                 新闻
/indicators AAPL 1y          技术指标
/report AAPL 1y              研究报告
/export-report AAPL 3mo reports/aapl.md
                              生成研究报告并保存为 Markdown 文件
/compare NVDA AMD 1y         股票对比
/debate NVDA AMD 1y          多智能体辩论
/backtest TSLA 20 60 2y      均线策略回测
/brief AAPL MSFT NVDA        自选股简报
/search 智谱 02513 股票       搜索公开网页核验标的
/fetch https://xueqiu.com/S/02513
                              抓取指定页面摘要
/tools                       查看工具
/sources                     查看数据源优先级
```

交互输入使用 `prompt_toolkit`：支持历史记录、光标移动、删除、Ctrl+A/E/U/K 和 slash command 补全。CLI 会自动清理误粘贴的 `finance-agent >` 前缀。

CLI 默认以 `compact` 模式展示 Claude Code 风格的高层 `thinking` 摘要。它只显示工具数量、耗时和工具名，最终答案会单独显示；需要展开详情时输入 `/think on` 或在交互模式里用 `/trace` 查看上一轮完整轨迹；需要安静输出时可输入 `/think off`。这些内容是可审计执行摘要，不是隐藏推理链。

## 代理与语言

如果本机使用 Clash/Mihomo，截图里的混合代理端口是 `7897`，可以在 `.env.local` 中配置：

```bash
FINANCE_HTTP_PROXY=http://127.0.0.1:7897
```

也可以在交互模式临时设置：

```text
/proxy set http://127.0.0.1:7897
/proxy test
```

CLI 支持中英文切换：

```bash
FINANCE_AGENT_LANG=en python -m agent.cli /help
```

交互模式中也可以输入：

```text
/lang zh
/lang en
```

## 微信连接与自进化

微信连接采用适配器模式：

- 默认 `dry-run`：不会发网络请求，消息写入 `.finance_agent/wechat_outbox/`，方便本地验证。
- 企业微信/微信群机器人：配置 `FINANCE_WECHAT_WEBHOOK` 后，`/wechat send` 会调用 webhook。
- 本地 relay：配置 `FINANCE_WECHAT_RELAY_URL` 后，可对接 WeChaty、个人微信桥接器或你自己的消息服务。

```bash
FINANCE_WECHAT_MODE=dry-run
# FINANCE_WECHAT_WEBHOOK=<paste-full-wecom-webhook-url-in-.env.local>
# FINANCE_WECHAT_RELAY_URL=http://127.0.0.1:8765/wechat/send
```

常用命令：

```text
/wechat status
/wechat send 今天的自选股简报已生成
/wechat send-md # AAPL 研究摘要
/memory add 以后回答 SpaceX 先解析 SPCX 并核验行情，不能用旧知识判断未上市
/memory list
/evolve SpaceX 查询必须先解析 SPCX，再核验公开网页、行情和新闻来源
/predict record AAPL up 30 0.65 服务收入和回购支撑
/predict eval all
/predict learn save
/learn-history AAPL 2y 20
/portfolio init 1000000 AAPL MSFT NVDA AMD GOOGL
/portfolio mark
/portfolio sell AMD all 波动率过高，模拟止盈/降风险
/portfolio trades
/schedule portfolio default 1440
/schedule brief AAPL,MSFT,NVDA 1440
/schedule run
```

金融自进化会把偏好、纠错、数据源经验和风险规则写入 `.finance_agent/finance_memory.jsonl`。核心 `skills/finance-research-evolution/SKILL.md` 保持稳定；如果确实需要生成新的专用 Skill，可以通过底层 `finance_evolve_from_trace` 指定独立 `skill_name`。本地 memory 目录已被 git 忽略；写入 Skill 前会脱敏常见 key/token/cookie。

预测评分闭环会把每次方向判断保存到 `.finance_agent/predictions.jsonl`，包含 baseline 价格、期限、置信度和 thesis。到期后运行 `/predict eval`，系统会拉取最新价格并计算方向命中、实际收益和置信度加权分数。`/predict eval all` 可用于 Demo 立即评分未到期预测；`/predict learn` 会按方向桶、命中率、置信度失误和高置信错判生成复盘，用来量化研究框架是否真的有效。`/predict learn save` 会把复盘写入金融 memory，后续可用 `/memory list` 查看。

历史学习预测会把历史 K 线切成 walk-forward 样本，学习当前特征桶在历史上对应的未来收益和胜率。`/learn-history AAPL 2y 20` 会输出方向、置信度、样本数和匹配特征，把结果写入 `.finance_agent/history_learning.jsonl`，同时更新 `skills/finance-history-learning/SKILL.md` 并记录一条可到期评分的预测。

模拟投资账户会写入 `.finance_agent/portfolio_default.json`。`/portfolio init 1000000 AAPL MSFT NVDA` 会根据当前行情、基本面、技术面和数据源置信度生成纸面持仓并记录 BUY 交易；`/portfolio mark` 会按最新价格追加一条净值记录；`/portfolio sell AMD all <理由>` 会模拟卖出并记录 SELL、实现盈亏和理由；`/portfolio trades` 查看交易流水；`/portfolio rebalance ...` 会用新的股票池重新计算仓位并记录买卖差额。它只做纸面组合，不会连接真实券商或真实下单。

微信定时推送采用本地文件任务表 `.finance_agent/scheduled_jobs.json`。`/schedule portfolio default 1440` 可以每天给纸面组合估值并推送到微信连接器或 dry-run outbox。创建任务后，需要用 cron、launchd 或手动定期执行：

```bash
python -m agent.cli /schedule run
```

## Configuration

没有配置 `DEEPSEEK_API_KEY` 时，系统会使用 `FakeBackend`，并把金融任务路由到本地 `finance_route_task`，方便离线演示。配置真模型后，Agent 会使用 OpenAI-compatible chat completions 接口选择工具和组织答案。

为了避免模型旧知识误判新上市、改名或跨市场标的，单次命令和交互会话里的自然语言金融问题会先进入确定性 `finance_route_task`：先解析代码、核验公开网页和行情，再组织报告；普通开发任务仍走 ReAct 主循环。

```bash
cp .env.example .env.local
```

可选环境变量：

```bash
DEEPSEEK_API_KEY=...
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat
ALPHAVANTAGE_API_KEY=...
TUSHARE_TOKEN=...
FINANCE_ALLOW_SAMPLE_FALLBACK=1
FINANCE_HTTP_PROXY=http://127.0.0.1:7897
FINANCE_AGENT_LANG=zh
FINANCE_WECHAT_MODE=dry-run
# FINANCE_WECHAT_WEBHOOK=...
# FINANCE_WECHAT_RELAY_URL=...
```

`.env.local` 已被 `.gitignore` 忽略。不要把 API key、token、cookie 写进代码或文档。

## 数据源

Provider 优先级：

1. Alpha Vantage，需 `ALPHAVANTAGE_API_KEY`
2. Tushare，需 `TUSHARE_TOKEN`，主要用于 A 股
3. AKShare，主要用于 A 股公开数据
4. Yahoo Finance public endpoints
5. `SAMPLE_FALLBACK`，仅用于离线演示

`SAMPLE_FALLBACK` 会明确标注，不能用于真实投资判断。如果希望严禁样例数据，设置：

```bash
FINANCE_ALLOW_SAMPLE_FALLBACK=0
```

港股代码会区分展示代码和数据源查询代码。例如公开页面常显示 `智谱(02513)`，Yahoo Finance 查询使用 `2513.HK`；MiniMax 常见展示代码 `00100.HK`，Yahoo 查询使用 `0100.HK`。报告里会保留展示代码并说明查询代码。

美股新上市或刚改名标的必须先做公开网页核验，再查行情。例如 `SpaceX` 会解析为 `SPCX`，可用：

```bash
python -m agent.cli /resolve SpaceX
python -m agent.cli /search "SpaceX SPCX Nasdaq IPO"
python -m agent.cli /quote SPCX
python -m agent.cli "SpaceX 最近情况如何"
```

## English Quick Start

```bash
pip install -r requirements.txt
cp .env.example .env.local
FINANCE_AGENT_LANG=en python -m agent.cli --selfcheck
FINANCE_AGENT_LANG=en python -m agent.cli /help
FINANCE_AGENT_LANG=en python -m agent.cli "Analyze recent SpaceX / SPCX developments"
```

Optional proxy for Clash/Mihomo:

```bash
FINANCE_HTTP_PROXY=http://127.0.0.1:7897
```

Useful commands:

```text
/lang en
/proxy test
/wechat status
/predict record SPCX down 30 0.55 valuation reset risk
/predict learn save
/schedule brief AAPL,MSFT,NVDA 1440
/schedule run
/resolve SpaceX
/quote SPCX
/report AAPL 1y
/quality AAPL 1y
```

## 边界

- 本项目只做研究辅助，不做自动交易。
- 输出必须区分事实、推断、风险和数据缺口。
- 研究报告会包含质量门禁，但通过门禁不代表可以买入，只表示数据更适合继续研究。
- 本地工具有安全层：越界路径、敏感文件、危险命令、疑似密钥写入会被拦截。
- 回测不包含滑点、手续费、税费、分红复权和真实成交约束。
- 免费数据源可能延迟、限流或缺失字段。
- 网页抓取遇到 WAF/JS challenge 时只会标注限制，不会假装读取完整正文。

## License

MIT，见 [LICENSE](LICENSE)。

## 开发验证

```bash
python -m compileall agent backend finance mcp skills tools trace2skill wechat scheduler tests
python -m agent.cli --selfcheck
python -m pytest
```

技术文档见 [docs/TECHNICAL_DESIGN.md](docs/TECHNICAL_DESIGN.md)，消融实验见 [docs/ABLATION_REPORT.md](docs/ABLATION_REPORT.md)。

项目进度和历史决策见 [FINANCE_AGENT_PROGRESS.md](FINANCE_AGENT_PROGRESS.md)。
