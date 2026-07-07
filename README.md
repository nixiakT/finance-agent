# finance-agent

命令行股票研究助手。它面向行情查询、基本面研究、新闻核验、技术指标、多智能体辩论和简单策略回测，只做研究辅助，不做自动交易。

## 能力

- 股票行情：价格、涨跌、成交量、市值、数据源和时间。
- 标的解析：公司名、简称、中文名、英文名或 ticker 自动解析为 A 股/港股/美股候选代码。
- 历史价格与技术指标：MA5 / MA20 / MA60、RSI14、MACD、波动率、近 1 月 / 3 月 / 1 年收益率。
- 基本面：PE、EPS、营收、利润、现金流、ROE、利润率等字段，缺失时明确标注。
- 新闻和网页核验：搜索公开页面或抓取指定 URL，确认代码、上市状态和来源。
- 结构化报告：价格、走势、基本面、技术面、新闻、风险和研究结论。
- 投资框架：巴菲特/芒格、段永平、达利欧。
- 多智能体辩论：Bull、Bear、Value、Macro、Risk、Judge。
- 策略辅助：移动均线交叉策略回测。
- 自选股简报：批量生成跟踪摘要。
- Trace2Skill：把成功任务轨迹沉淀为项目 Skill。

## 快速开始

```bash
pip install -r requirements.txt

python -m agent.cli --selfcheck
python -m agent.cli
```

进入交互模式后可以持续对话：

```text
finance-agent > /help
finance-agent > 分析一下 AAPL 最近三个月走势
finance-agent > /think on
finance-agent > /quote AAPL
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
```

## 常用命令

```text
/think on | /think off       开关高层执行轨迹
/resolve minimax             解析公司名/简称到 A 股、港股、美股候选代码
/quote AAPL                  查询行情
/history AAPL 1y             历史价格和指标摘要
/financials AAPL             基本面摘要
/news AAPL 5                 新闻
/indicators AAPL 1y          技术指标
/report AAPL 1y              研究报告
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

## 配置

没有配置 `DEEPSEEK_API_KEY` 时，系统会使用 `FakeBackend`，并把金融任务路由到本地 `finance_route_task`，方便离线演示。配置真模型后，Agent 会使用 OpenAI-compatible chat completions 接口选择工具和组织答案。

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

## 边界

- 本项目只做研究辅助，不做自动交易。
- 输出必须区分事实、推断、风险和数据缺口。
- 回测不包含滑点、手续费、税费、分红复权和真实成交约束。
- 免费数据源可能延迟、限流或缺失字段。
- 网页抓取遇到 WAF/JS challenge 时只会标注限制，不会假装读取完整正文。

## 开发验证

```bash
python -m compileall agent backend finance skills tools trace2skill
python -m agent.cli --selfcheck
python -m pytest
```

项目进度和历史决策见 [FINANCE_AGENT_PROGRESS.md](FINANCE_AGENT_PROGRESS.md)。
