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
- [x] 按参考图片重绘招财猫形象：加入招财进宝符、笑脸三花猫、招财手、发财扇、红色花垫和金币点缀。

## 已实现功能

- 数据层：`ProviderChain`，支持 Alpha Vantage、Tushare、AKShare、Yahoo Finance public endpoints 和样例 fallback。
- 行情：`finance_get_quote`。
- 历史价格：`finance_get_price_history`，支持摘要和 CSV。
- 基本面：`finance_get_financials`。
- 新闻：`finance_get_news`。
- 技术指标：`finance_calculate_indicators`，包含 MA5/20/60、RSI14、MACD、年化波动率和区间收益。
- 研究报告：`finance_generate_report`。
- 多股票对比：`finance_compare_stocks`。
- 多智能体辩论：`finance_debate_stocks`。
- 策略回测：`finance_backtest_strategy`，第一版支持移动均线交叉。
- 自选股简报：`finance_daily_brief`。
- 离线路由：未配置真模型时，`FakeBackend` 会用 `finance_route_task` 跑通金融 Demo。
- Skill：`skills/finance-stock/SKILL.md` 规定金融分析边界和流程。
- Trace2Skill：`skills/trace2skill/SKILL.md` 和 `trace2skill_generate` 支持从成功轨迹生成新 Skill。
- CLI 欢迎页：`python -m agent.cli` 显示招财猫入口。
- CLI 品牌页：欢迎页包含“招财进宝”金融猫、研究边界和核心能力入口。
- CLI 启动面板：双栏展示 Logo、Available Tools、Market Sources、Commands、Session 和 Boundary。
- CLI 金色品牌区：左侧完整卡片展示招财进宝猫、模型、research only 和 no auto trading。
- CLI 招财猫造型：左侧 Logo 使用照片风格的符纸、三花猫、折扇和坐垫元素。
- CLI 帮助菜单：`python -m agent.cli /help` 显示功能列表和示例命令。
- CLI 交互模式：`python -m agent.cli` 后可在同一进程中持续提问，复用会话上下文。
- CLI 命令模式：常用金融工具有对应 slash command，可绕过自然语言路由直接执行。
- CLI 高层 trace：`/think on` 展示模型回合、工具调用和结果摘要，不输出隐藏推理链。
- CLI 行编辑：支持历史记录、方向键、删除键、常见 Emacs 快捷键和命令补全。
- CLI 输入清洗：误粘贴 `finance-agent >` 前缀时会自动剥离。
- 标的核验：自然语言包含“标的/代码/上市”等问题时，先做公开网页搜索，再做行情核验。
- 网页工具：`web_search` 使用公开搜索结果核验来源，`web_fetch` 抓取指定 URL 并标注 WAF/JS 限制。

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
