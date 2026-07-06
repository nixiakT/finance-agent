# finance-agent（mini-OpenClaw 金融股票研究助手）

> 当前项目已经从通用 starter 扩展为金融股票研究 Agent。它面向股票行情、基本面、新闻、技术指标、多智能体辩论和策略回测，只做研究辅助，不做自动交易。

## 金融 Agent 能力

- 股票行情查询：`finance_get_quote`
- 历史价格和技术指标：MA5 / MA20 / MA60、RSI、MACD、波动率、近 1 月 / 3 月 / 1 年收益率
- 基本面研究：市值、PE、EPS、营收、利润、现金流、ROE、利润率等
- 新闻摘要：获取相关新闻标题、时间、来源和链接
- 结构化股票研究报告：价格、走势、基本面、技术面、新闻、风险、结论
- 投资框架蒸馏：巴菲特/芒格、段永平、达利欧
- 多智能体辩论：多头、空头、价值、宏观、风险、裁判
- 策略辅助：移动均线交叉策略回测
- 自选股简报：批量生成每日跟踪摘要
- 数据源扩展：Alpha Vantage、Tushare、AKShare、Yahoo Finance，并带样例 fallback
- Trace2Skill 自进化：把成功任务轨迹沉淀成新的项目 Skill

## 快速演示

```bash
pip install -r requirements.txt

python -m agent.cli --selfcheck
python -m agent.cli "分析一下 AAPL 最近三个月走势，并生成投资研究摘要"
python -m agent.cli "比较 NVDA 和 AMD 的基本面和技术面"
python -m agent.cli "用巴菲特、段永平、达利欧三个视角分析 NVDA，并让多智能体辩论是否值得继续跟踪"
python -m agent.cli "帮我回测 TSLA 的 20 日均线上穿 60 日均线策略"
python -m agent.cli "生成我的自选股每日简报：AAPL, MSFT, NVDA"
```

没有配置 `DEEPSEEK_API_KEY` 时，`FakeBackend` 会把金融任务路由到 `finance_route_task`，仍然可以跑通 Demo。配置真模型后，Agent 会自动使用 DeepSeek API 选择工具和组织答案。

可选本地配置：

```bash
cp .env.example .env.local
# 在 .env.local 中填写，不要提交：
# DEEPSEEK_API_KEY=...
# DEEPSEEK_BASE_URL=https://api.penguinsaichat.dpdns.org/v1
# DEEPSEEK_MODEL=gpt-5.5-openai-compact
# TUSHARE_TOKEN=...
```

`.env.local` 已被 `.gitignore` 忽略。不要把 API key、token、cookie 写进代码或文档。

如果公开数据源被限流，系统会降级到明确标注的 `SAMPLE_FALLBACK` 样例数据。样例数据只用于离线演示，不能用于真实投资判断。

Trace2Skill 示例：

```bash
python - <<'PY'
from trace2skill import generate_skill
generate_skill(
    task="把成功的金融分析流程沉淀成 Skill",
    trace="读取数据源 -> 生成报告 -> 运行 selfcheck 验证 -> 注意不要提交密钥",
    skill_name="finance-report-workflow",
)
PY
```

## 项目进度文档

计划、进度、已实现功能和已知限制维护在 [FINANCE_AGENT_PROGRESS.md](FINANCE_AGENT_PROGRESS.md)。

> 你将在这 10 天里，把这个骨架填成一个能在命令行里干活的通用智能体。
> 每个模块里都有 `# TODO[DayN]` 标记，告诉你哪天该填哪里。

## 这是什么

mini-OpenClaw 是一个 Claude Code 式的命令行 Agent：
一个**主循环**反复调用**大模型后端**，模型输出**工具调用**（read/write/bash/…），
主循环执行工具、把结果喂回模型，直到任务完成。再叠加 **MCP**（可插拔外部工具）、
**Skills**（可加载领域能力）和**安全层**（权限/沙箱/注入防护）。

```
你的请求 ──► [主循环 loop.py] ──► [后端 server.py ──► 大模型]
                  ▲   │  模型输出 <tool_call>{...}</tool_call>
                  │   ▼
            tool result ◄── [工具分发：read/write/bash/edit/grep/...]
                              ├── 内置工具 (tools/)
                              ├── MCP 工具 (mcp/)
                              └── Skills (skills/)
```

## 目录结构与建设节奏

| 模块 | 你要做什么 | 哪天 |
|------|-----------|------|
| `backend/` | DeepSeek API 客户端（已给 `client.py`，配 key 即用）；Day2 连通后端 + 首个工具 schema | Day1–2 |
| `prompt/` | render_prompt(messages, tools) 对话模板渲染 + parse_tool_calls | Day3 |
| `agent/` | 系统提示词（Day2 起草，Day5 完善）、ReAct 主循环、上下文管理 | Day2, Day5, Day7 |
| `tools/` | read/write/bash → edit/grep/glob → web_fetch/task_list | Day5, Day6, Day7 |
| `mcp/` | 最小 MCP 客户端（stdio + JSON-RPC）| Day8 |
| `skills/` | Skills 加载器 + 你领域的 Skill | Day9 |
| `eval/` | 任务集 + 指标评测 + 消融 | Day7, Day10 |

> 逐日构建目标详见各 `course/dayNN/lab-guide.md`；`grep -rn "TODO\[Day" .` 可看全部施工点。
> 里程碑：**v1（Day6）** 端到端可用 · **v3（Day9）** 可扩展 · **终版（Day10）** 含安全层，Demo Day 展示（占总评 95%）。

## 快速开始

```bash
# 1. Python 环境（agent 侧不吃显存）
conda create -n openclaw python=3.11 && conda activate openclaw
pip install -r requirements.txt

# 2. 先跑通骨架的"假后端"自检（Day1 就能跑）
python -m agent.cli --selfcheck

# 3. 之后每天填对应模块，重跑相关入口
```

## 里程碑

- **v1（Day6）**：`python -m agent.cli "创建 hello.py 并运行输出当前时间"` 能完成。
- **v3（Day9）**：能加载 MCP server 工具 + 自定义 Skill。
- **终版（Day10）**：含安全层，Demo Day 现场任务。

## 约定

- 全程一个 git 仓库，**按 day 打 tag**（`v1`, `v3`, `final`）。
- 每个模块自带一个 `README.md`，记录你的设计决策（技术文档分数来源）。
