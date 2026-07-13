Language / 语言: [中文](README.md) | English

# finance-agent

Command-line stock research assistant for quotes, fundamentals, news verification, indicators, multi-agent debate, simple backtests, prediction scoring, and scheduled WeChat briefs. It is a research assistant, not an auto-trading agent.

## Capabilities

- Quotes: price, change, volume, market cap, data source, and timestamp.
- Symbol resolution: company names, Chinese names, English names, aliases, or tickers to A-share, Hong Kong, and US candidates.
- History and indicators: MA5 / MA20 / MA60, RSI14, MACD, volatility, 1-month / 3-month / 1-year returns.
- Fundamentals: real-source lookup through Tushare, AKShare, Yahoo, and optional providers for PE, EPS, revenue, profit, cash flow, ROE, and margin. Empty results fall through to the next provider; unresolved gaps stay explicit.
- News and web verification: news is filtered by ticker/company-specific terms. An upstream failure is reported as a data failure, never converted into a fake news item.
- Structured reports: price, trend, fundamentals, technicals, news, risks, and research conclusion.
- Research quality gate: information richness, data gaps, reject/recheck signals, and next verification steps.
- Investment frameworks: Buffett/Munger, Duan Yongping, Li Lu, and Dalio.
- Multi-agent debate: Bull, Bear, Value, Buffett, Munger, Duan, Li Lu, Dalio, Anti-Bias, Macro, Risk, and Judge, with discipline label, mirror test, and testable prediction.
- Prediction scoring loop: record bullish/bearish/neutral calls, evaluate future outcomes, and review accuracy, confidence calibration, and high-confidence misses.
- Historical learning forecast: run walk-forward learning on historical candles, generate direction/confidence, and persist the result as a Skill.
- Paper investment account: give the agent 1,000,000 paper cash, score a stock pool, calculate shares and allocation, record daily NAV, and review weak holdings/replacement candidates.
- Strategy helper: moving-average crossover backtests.
- Watchlist briefs: batch summaries for tracked symbols.
- WeChat delivery and scheduling: dry-run outbox, WeCom webhook, local relay, and scheduled local brief jobs.
- Trace2Skill: turn successful task traces into project skills.
- General agent tools: read/write/bash/edit/grep/glob/task_list for live coding tasks.
- Dynamic CLI: built-ins, Markdown custom commands, project Skills, and MCP prompts share one fuzzy-completion menu. The welcome screen, help, status bar, and tool cards adapt to terminal width.
- MCP: `.mcp.json` can connect multiple stdio servers. Tools use `mcp__<server>__<tool>` names, with bounded timeouts, status reporting, and process cleanup.
- Skills: the system layer exposes only validated Skill names. Descriptions stay in `/skills` and completion metadata; `read_skill` loads the body on demand as lower-priority context.
- Safety layer: workspace permissions, dangerous command blocking, secret-write blocking, and untrusted-content isolation.

## Quick Start

The repository includes `environment.yml`. Create or update the `openclaw` environment:

```bash
conda env create -f environment.yml        # first setup
# conda env update -n openclaw -f environment.yml --prune  # existing environment
conda activate openclaw
python -m agent.cli --selfcheck
python -m agent.cli
```

Interactive mode keeps one persistent session:

```text
finance-agent > /help
finance-agent > /lang en
finance-agent > Analyze AAPL over the last three months
finance-agent > /trace off
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
python -m agent.cli "Give the agent 1,000,000 paper cash to invest in AAPL, MSFT, NVDA, AMD; show what to buy and how much"
```

## Common Commands

```text
/trace on | /trace off
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
/learn-history AAPL 2y 20     Learn forecast rules from history, record the forecast, and update Skill
/portfolio init/status/review/mark/sell/trades/pnl/rebalance
                              Create a paper portfolio, inspect holdings, review replacements, mark daily NAV, simulate sells, view trades, daily PnL, and rebalance
/schedule list/brief/portfolio/run
                              Create scheduled WeChat briefs or portfolio marks, or execute due jobs
/skills                      List project Skills available for on-demand loading
/mcp                         Show MCP server status, tools, and prompt commands
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

Interactive input uses `prompt_toolkit`, with history, cursor movement, Ctrl+A/E/U/K, and fuzzy slash-command completion. Typing `/` or a command prefix pins up to eight matching commands and descriptions above the input; use `Up/Down` to move, `Tab/Enter` to accept, and `Esc` to close. One catalog drives help and built-in completion, then runtime discovery merges Markdown custom commands, Skills, and MCP prompts. A persistent bottom bar shows thinking mode, model, available data sources, Skill count, and MCP connection count. The CLI also cleans accidentally pasted `finance-agent >` prefixes.

The CLI defaults to `trace off`: current progress refreshes in place and folds into one completion summary. `/trace on` keeps every model turn, tool call, argument, and result preview visible. After a task, bare `/trace` reopens the previous full details. This is an auditable execution trace, not hidden chain-of-thought.

## Custom Commands, Skills, And MCP

Place Markdown commands in project-local `.finance_agent/commands/` or user-level `~/.finance-agent/commands/`. The relative file path becomes the slash command. Project commands override user commands with the same name, but built-ins remain reserved. Templates support `$1`, `$2`, `$ARGUMENTS`, and `$$`:

```markdown
---
description: Review disconfirming evidence for a stock
argument-hint: <ticker> <period>
---
Review counter-evidence and risks for $1 over $2. Full input: $ARGUMENTS
```

`/skills` lists `skills/*/SKILL.md`. The model can call the read-only `read_skill` tool by name, or you can invoke a Skill directly as `/<skill-name> ...`. Prompts declared by MCP servers appear in the same completion menu as `/mcp:<server>:<prompt>`.

Configure multiple stdio servers in the project-root `.mcp.json`:

```json
{
  "mcpServers": {
    "research": {
      "command": "python",
      "args": ["-m", "your_mcp_server"],
      "cwd": ".",
      "timeoutSeconds": 10
    }
  }
}
```

One broken server does not hide healthy servers. `/mcp` reports each server's status, errors, tools, and prompts. Managed MCP subprocesses close when an interactive or one-shot run exits. If `.mcp.json` is absent, the built-in echo server remains available as a local example.

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
FINANCE_PORTFOLIO_DIR=~/.finance-agent/portfolios
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
/learn-history AAPL 2y 20
/portfolio init 1000000 AAPL MSFT NVDA AMD GOOGL
/portfolio review GOOGL AVGO META AMZN TSLA JPM
/portfolio mark
/portfolio sell AMD all high volatility, reduce paper risk
/portfolio trades
/portfolio pnl
/schedule portfolio default 1440
/schedule brief AAPL,MSFT,NVDA 1440
/schedule run
```

Finance self-evolution writes preferences, corrections, data-source lessons, and risk rules to `.finance_agent/finance_memory.jsonl`. The core `skills/finance-research-evolution/SKILL.md` remains stable; use the lower-level `finance_evolve_from_trace` with a separate `skill_name` only when a new dedicated skill is needed. Local memory is gitignored, and skill writes sanitize common keys, tokens, and cookies.

The prediction scoring loop writes calls to `.finance_agent/predictions.jsonl`, including baseline price, horizon, confidence, and thesis. `/predict eval` fetches the later price and computes directional hit, realized return, and confidence-weighted score. `/predict eval all` is useful for demos. `/predict learn` reviews direction buckets, accuracy, confidence errors, and high-confidence misses. `/predict learn save` stores the review in finance memory.

Historical learning turns historical candles into walk-forward samples and checks how the current feature buckets performed in the past. `/learn-history AAPL 2y 20` outputs direction, confidence, sample count, and matched features, appends the result to `.finance_agent/history_learning.jsonl`, updates `skills/finance-history-learning/SKILL.md`, and records a forecast for future scoring.

The paper investment account persists to `~/.finance-agent/portfolios/portfolio_default.json`, independent of the launch directory, terminal, or code worktree. On first use, the old `.finance_agent/portfolio_default.json` is migrated automatically. Reinitializing an account creates a timestamped copy under `backups/`. Set `FINANCE_PORTFOLIO_DIR` to choose another persistent location. `/portfolio init 1000000 AAPL MSFT NVDA` builds paper holdings from current quotes, fundamentals, indicators, and data-source confidence, and records BUY transactions. Scoring is split into momentum, quality, risk, and data confidence, with weak relative strength penalized explicitly. `/portfolio review GOOGL AVGO ...` performs a read-only review of current holdings, weak positions, and replacement candidates; `/portfolio mark` appends a NAV record using latest prices; `/portfolio sell AMD all <reason>` simulates a SELL with realized PnL and reason; `/portfolio trades` shows the trade ledger; `/portfolio pnl` summarizes daily buy amount, sell amount, realized PnL, ending NAV, and NAV change; `/portfolio rebalance ...` recalculates allocation from a new stock pool and records the buy/sell differences. It is paper-only and never connects to a broker or sends real orders.

Scheduled WeChat delivery uses `.finance_agent/scheduled_jobs.json`. `/schedule portfolio default 1440` can mark the paper portfolio daily and send it to the WeChat connector or dry-run outbox. Create jobs with `/schedule brief` or `/schedule portfolio`, then run due jobs manually or through cron/launchd:

```bash
python -m agent.cli /schedule run
```

## Configuration

Without `DEEPSEEK_API_KEY`, the system uses `FakeBackend`, which selects local `finance_route_task` from inside the Agent loop for offline demos. With a real model configured, the agent uses an OpenAI-compatible chat completions endpoint to select tools and organize answers.

With a real model, every natural-language finance query enters the ReAct loop: the model decomposes the request, combines quote, history, fundamentals, news, and web-verification tools, then synthesizes the answer. Explicit slash commands such as `/report` and `/compare` remain deterministic. A finance task falls back to the fixed report only when the very first model request fails before any tool has run; later model failures never rerun tools automatically.

```bash
cp .env.example .env.local
```

Optional environment variables:

```bash
DEEPSEEK_API_KEY=...
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat
# GPT-5.6 Sol + xhigh requires the Responses API:
# DEEPSEEK_MODEL=gpt-5.6-sol
# DEEPSEEK_API_MODE=responses
# DEEPSEEK_REASONING_EFFORT=xhigh
ALPHAVANTAGE_API_KEY=...
TUSHARE_TOKEN=...
FINANCE_ALLOW_SAMPLE_FALLBACK=0
FINANCE_HTTP_PROXY=http://127.0.0.1:7897
FINANCE_AGENT_LANG=en
FINANCE_WECHAT_MODE=dry-run
# FINANCE_WECHAT_WEBHOOK=...
# FINANCE_WECHAT_RELAY_URL=...
```

`.env.local` is ignored by git. Do not put API keys, tokens, or cookies in code or docs.

## Data Sources

Provider order:

1. Alpha Vantage, requires `ALPHAVANTAGE_API_KEY`
2. Tushare, requires `TUSHARE_TOKEN`, mainly for A-shares
3. AKShare, mainly for public A-share data
4. Yahoo Finance public endpoints
5. `SAMPLE_FALLBACK`, only for offline demos

`SAMPLE_FALLBACK` is clearly labeled, must not be used for real investment judgment, and is disabled by default. Enable it explicitly only for offline demos:

```bash
FINANCE_ALLOW_SAMPLE_FALLBACK=1
```

Applicable real providers run concurrently under one deadline per operation and one total snapshot deadline. Timed-out providers are reported and temporarily circuit-broken instead of blocking successful fallbacks. Configure `FINANCE_PROVIDER_TIMEOUT_SECONDS`, `FINANCE_SNAPSHOT_TIMEOUT_SECONDS`, and `FINANCE_PROVIDER_COOLDOWN_SECONDS`; defaults are 25, 45, and 60 seconds.

Quote lookup checks every applicable real provider, prefers the freshest real-time result, and reports the maximum price spread. Historical candles also query every applicable real provider using unadjusted closes, select the freshest/most complete series, and report overlap-window spread. Fundamentals fill missing fields only when currency, report date, and period basis are compatible, and report overlapping-field differences. News aggregates all applicable real providers, filters relevance, deduplicates across sources, and diversifies sources before applying the limit; only events from the last 180 days count as recent quality coverage. AKShare maps public financial indicators for A-share, Hong Kong, and US symbols. Sample fallback never counts as real-source coverage or cross-validation.

Yahoo news first requests a larger candidate set, then filters on the ticker, provider query code, and distinctive company-name terms. Generic words such as `technology`, `group`, and `inc` cannot cause a match by themselves. No strong match is reported as empty/filtered; transport or provider failures are reported separately.

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
- Repeating "this stock will rise," asking to omit risks, or claiming insider information adds no evidence and does not raise confidence.
- A deterministic finance fallback produced after a first-turn model failure is recorded in the same interactive session, so follow-ups such as "what about it?" retain context. Compacted history is low-trust data and is never promoted to a system instruction.

## License

MIT. See [LICENSE](LICENSE).

## Development Checks

```bash
python -m compileall agent backend eval finance mcp skills tools trace2skill wechat scheduler tests
python -m agent.cli --selfcheck
python -m pytest

# Five-stock real-source check with demo fallback disabled
FINANCE_ALLOW_SAMPLE_FALLBACK=0 python -m agent.cli /compare AAPL 600519.SS 0700.HK 02513.HK SPCX 1y

# Three-round bullish/insider-pressure evaluation; requires DEEPSEEK_API_KEY and spends three calls
FINANCE_RUN_LIVE_EVAL=1 python -m pytest tests/test_live_injection_eval.py -q
```

Regular `pytest` skips the live model evaluation. It runs only when `FINANCE_RUN_LIVE_EVAL=1` is set explicitly.

Technical design: [docs/TECHNICAL_DESIGN.md](docs/TECHNICAL_DESIGN.md). Ablation report: [docs/ABLATION_REPORT.md](docs/ABLATION_REPORT.md).

Progress and historical decisions: [FINANCE_AGENT_PROGRESS.md](FINANCE_AGENT_PROGRESS.md).
