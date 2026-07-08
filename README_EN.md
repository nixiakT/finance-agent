Language / 语言: [中文](README.md) | English

# finance-agent

Command-line stock research assistant for quotes, fundamentals, news verification, indicators, multi-agent debate, simple backtests, prediction scoring, and scheduled WeChat briefs. It is a research assistant, not an auto-trading agent.

## Capabilities

- Quotes: price, change, volume, market cap, data source, and timestamp.
- Symbol resolution: company names, Chinese names, English names, aliases, or tickers to A-share, Hong Kong, and US candidates.
- History and indicators: MA5 / MA20 / MA60, RSI14, MACD, volatility, 1-month / 3-month / 1-year returns.
- Fundamentals: PE, EPS, revenue, profit, cash flow, ROE, margin, and explicit missing-data notes.
- News and web verification: search public pages or fetch URLs to verify codes, listing status, and sources.
- Structured reports: price, trend, fundamentals, technicals, news, risks, and research conclusion.
- Research quality gate: information richness, data gaps, reject/recheck signals, and next verification steps.
- Investment frameworks: Buffett/Munger, Duan Yongping, Li Lu, and Dalio.
- Multi-agent debate: Bull, Bear, Value, Buffett, Munger, Duan, Li Lu, Dalio, Anti-Bias, Macro, Risk, and Judge, with discipline label, mirror test, and testable prediction.
- Prediction scoring loop: record bullish/bearish/neutral calls, evaluate future outcomes, and review accuracy, confidence calibration, and high-confidence misses.
- Strategy helper: moving-average crossover backtests.
- Watchlist briefs: batch summaries for tracked symbols.
- WeChat delivery and scheduling: dry-run outbox, WeCom webhook, local relay, and scheduled local brief jobs.
- Trace2Skill: turn successful task traces into project skills.
- General agent tools: read/write/bash/edit/grep/glob/task_list for live coding tasks.
- MCP: minimal stdio client with an echo server; MCP tools are exposed with the `mcp__` prefix.
- Safety layer: workspace permissions, dangerous command blocking, secret-write blocking, and untrusted-content isolation.

## Quick Start

```bash
pip install -r requirements.txt

python -m agent.cli --selfcheck
python -m agent.cli
```

Interactive mode keeps one persistent session:

```text
finance-agent > /help
finance-agent > /lang en
finance-agent > Analyze AAPL over the last three months
finance-agent > /think off
finance-agent > /proxy test
finance-agent > /quote AAPL
finance-agent > /wechat status
finance-agent > /search "SpaceX SPCX Nasdaq IPO"
finance-agent > /exit
```

Single-run tasks are also supported:

```bash
python -m agent.cli "Analyze AAPL over the last three months and generate a research summary"
python -m agent.cli "Compare NVDA and AMD on fundamentals and technicals"
python -m agent.cli "Analyze NVDA from Buffett, Duan, and Dalio perspectives, then run a multi-agent debate"
python -m agent.cli "Backtest a TSLA 20-day / 60-day moving-average crossover strategy"
python -m agent.cli "Generate a daily brief for AAPL, MSFT, NVDA"
```

## Common Commands

```text
/think on | /think compact | /think off
                              Toggle high-level execution trace; compact is the default folded summary
/trace                       Expand the previous task's detailed thinking trace
/lang zh | /lang en          Switch CLI language
/status                      Show model, data sources, tool count, thinking status, and license
/proxy status/test/set/off   Inspect, test, set, or disable proxy for web and market-data requests
/wechat status/send/send-md  Check WeChat connection or send a report to WeChat/local outbox
/memory list/add             View or add finance research preferences, corrections, and risk rules
/evolve <review/trace>        Save reusable finance lessons into memory and skills
/predict record/list/eval/learn
                              Record predictions, list the ledger, evaluate outcomes, and learn from history
/schedule list/brief/run     Create scheduled WeChat briefs or execute due jobs
/mcp                         Show registered MCP tools
/security                    Show permission and injection-protection policy
/resolve minimax             Resolve a company name or alias to A/HK/US ticker candidates
/quote AAPL                  Get quote
/quality AAPL 1y             Run research quality gate
/history AAPL 1y             Summarize price history and indicators
/financials AAPL             Summarize fundamentals
/news AAPL 5                 Fetch news
/indicators AAPL 1y          Calculate indicators
/report AAPL 1y              Generate stock research report
/export-report AAPL 3mo reports/aapl.md
                              Generate a report and save it as Markdown
/compare NVDA AMD 1y         Compare stocks
/debate NVDA AMD 1y          Run multi-agent debate
/backtest TSLA 20 60 2y      Backtest moving-average strategy
/brief AAPL MSFT NVDA        Generate watchlist brief
/compact                     Summarize older interactive history and keep recent context
/search "Zhipu 02513 stock"  Search public web pages for verification
/fetch https://xueqiu.com/S/02513
                              Fetch and summarize a specific page
/tools                       List tools
/sources                     Show data-source priority
```

Interactive input uses `prompt_toolkit`, with history, cursor movement, deletion, Ctrl+A/E/U/K, and slash-command completion. The CLI also cleans accidentally pasted `finance-agent >` prefixes.

By default, the CLI displays a Claude Code-style high-level `thinking` trace in `compact` mode. It shows a one-line summary with tool count, elapsed time, and tool names while keeping the final answer separate. Use `/think on` for expanded details, `/trace` in interactive mode to expand the previous trace, or `/think off` for quieter output. This is an auditable execution summary, not hidden chain-of-thought.

## Proxy And Language

For Clash/Mihomo, configure the local mixed proxy in `.env.local`:

```bash
FINANCE_HTTP_PROXY=http://127.0.0.1:7897
```

Or set it interactively:

```text
/proxy set http://127.0.0.1:7897
/proxy test
```

CLI language can be selected through an environment variable:

```bash
FINANCE_AGENT_LANG=en python -m agent.cli /help
FINANCE_AGENT_LANG=zh python -m agent.cli /help
```

Or inside the interactive session:

```text
/lang en
/lang zh
```

## WeChat And Self-Evolution

WeChat delivery uses an adapter pattern:

- Default `dry-run`: no network call; messages are written to `.finance_agent/wechat_outbox/`.
- WeCom / group bot: configure `FINANCE_WECHAT_WEBHOOK`.
- Local relay: configure `FINANCE_WECHAT_RELAY_URL` to connect WeChaty, a personal WeChat bridge, or your own message service.

```bash
FINANCE_WECHAT_MODE=dry-run
# FINANCE_WECHAT_WEBHOOK=<paste-full-wecom-webhook-url-in-.env.local>
# FINANCE_WECHAT_RELAY_URL=http://127.0.0.1:8765/wechat/send
```

Useful commands:

```text
/wechat status
/wechat send The watchlist brief is ready
/wechat send-md # AAPL research summary
/memory add For SpaceX tasks, resolve SPCX first and verify live sources
/memory list
/evolve SpaceX queries must resolve SPCX, then verify public pages, quote time, and news sources
/predict record AAPL up 30 0.65 services revenue and buybacks support the thesis
/predict eval all
/predict learn save
/schedule brief AAPL,MSFT,NVDA 1440
/schedule run
```

Finance self-evolution writes preferences, corrections, data-source lessons, and risk rules to `.finance_agent/finance_memory.jsonl`. The core `skills/finance-research-evolution/SKILL.md` remains stable; use the lower-level `finance_evolve_from_trace` with a separate `skill_name` only when a new dedicated skill is needed. Local memory is gitignored, and skill writes sanitize common keys, tokens, and cookies.

The prediction scoring loop writes calls to `.finance_agent/predictions.jsonl`, including baseline price, horizon, confidence, and thesis. `/predict eval` fetches the later price and computes directional hit, realized return, and confidence-weighted score. `/predict eval all` is useful for demos. `/predict learn` reviews direction buckets, accuracy, confidence errors, and high-confidence misses. `/predict learn save` stores the review in finance memory.

Scheduled WeChat delivery uses `.finance_agent/scheduled_jobs.json`. Create jobs with `/schedule brief`, then run due jobs manually or through cron/launchd:

```bash
python -m agent.cli /schedule run
```

## Configuration

Without `DEEPSEEK_API_KEY`, the system uses `FakeBackend` and routes finance tasks to local deterministic tools for offline demos. With a real model configured, the agent uses an OpenAI-compatible chat completions endpoint to select tools and organize answers.

To avoid stale model knowledge about newly listed, renamed, or cross-market symbols, natural-language finance queries first go through deterministic `finance_route_task`: resolve symbols, verify public web pages and quotes, then write the report. Non-finance coding tasks still use the ReAct loop.

```bash
cp .env.example .env.local
```

Optional environment variables:

```bash
DEEPSEEK_API_KEY=...
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat
ALPHAVANTAGE_API_KEY=...
TUSHARE_TOKEN=...
FINANCE_ALLOW_SAMPLE_FALLBACK=1
FINANCE_HTTP_PROXY=http://127.0.0.1:7897
FINANCE_AGENT_LANG=en
FINANCE_WECHAT_MODE=dry-run
# FINANCE_WECHAT_WEBHOOK=...
# FINANCE_WECHAT_RELAY_URL=...
```

`.env.local` is ignored by git. Do not put API keys, tokens, or cookies in code or docs.

## Data Sources

Provider priority:

1. Alpha Vantage, requires `ALPHAVANTAGE_API_KEY`
2. Tushare, requires `TUSHARE_TOKEN`, mainly for A-shares
3. AKShare, mainly for public A-share data
4. Yahoo Finance public endpoints
5. `SAMPLE_FALLBACK`, only for offline demos

`SAMPLE_FALLBACK` is clearly labeled and must not be used for real investment judgment. To disable sample data:

```bash
FINANCE_ALLOW_SAMPLE_FALLBACK=0
```

Hong Kong symbols distinguish display codes and provider query codes. For example, public pages may show `Zhipu(02513)`, while Yahoo Finance uses `2513.HK`; MiniMax may be displayed as `00100.HK`, while Yahoo uses `0100.HK`. Reports preserve the display code and explain provider query differences.

Newly listed or recently renamed US stocks must be verified through public web pages before quote lookup. For example, SpaceX resolves to `SPCX`:

```bash
python -m agent.cli /resolve SpaceX
python -m agent.cli /search "SpaceX SPCX Nasdaq IPO"
python -m agent.cli /quote SPCX
python -m agent.cli "Analyze recent SpaceX developments"
```

## Boundaries

- This project is for research assistance only; it does not execute trades.
- Outputs must separate facts, inference, risks, and data gaps.
- Quality gates do not mean "buy"; they only indicate whether the data is suitable for deeper research.
- Local tools enforce safety: blocked paths, sensitive files, dangerous commands, and suspected secret writes are rejected.
- Backtests exclude slippage, fees, taxes, dividend adjustments, and real execution constraints.
- Free data sources may be delayed, rate-limited, or missing fields.
- When a page has WAF or JavaScript challenges, the tool reports the limitation instead of pretending to read the full content.

## License

MIT. See [LICENSE](LICENSE).

## Development Checks

```bash
python -m compileall agent backend finance mcp skills tools trace2skill wechat scheduler tests
python -m agent.cli --selfcheck
python -m pytest
```

Technical design: [docs/TECHNICAL_DESIGN.md](docs/TECHNICAL_DESIGN.md). Ablation report: [docs/ABLATION_REPORT.md](docs/ABLATION_REPORT.md).

Progress and historical decisions: [FINANCE_AGENT_PROGRESS.md](FINANCE_AGENT_PROGRESS.md).
