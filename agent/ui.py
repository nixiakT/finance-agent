"""CLI presentation helpers."""
from __future__ import annotations


WELCOME = r"""
       /\_/\
      ( o.o )
       > ^ <
   ____/| |\____
  /    FINANCE   \
 /   AGENT  招财  \
 \______________/

欢迎使用 finance-agent。
输入 /help 查看功能菜单；输入自然语言任务开始分析。
""".strip("\n")


HELP = """
finance-agent 功能菜单

基础命令：
  /help
    显示当前功能菜单。
  --selfcheck
    运行工具注册、后端和主循环自检。

股票研究：
  python -m agent.cli "分析一下 AAPL 最近三个月走势，并生成投资研究摘要"
  python -m agent.cli "分析一下 贵州茅台 的基本面和技术面"

行情与数据：
  - 实时/准实时行情：价格、涨跌幅、成交量、市值等
  - 历史价格：K 线摘要或 CSV
  - 基本面：PE、EPS、营收、利润、现金流、ROE、利润率
  - 新闻事件：相关新闻标题、来源、时间和链接

技术指标：
  - MA5 / MA20 / MA60
  - RSI14
  - MACD
  - 年化波动率
  - 近 1 月 / 3 月 / 1 年收益率

投资框架：
  - 巴菲特/芒格：护城河、现金流、安全边际
  - 段永平：好生意、用户价值、长期主义
  - 达利欧：宏观周期、利率、组合风险

多智能体辩论：
  python -m agent.cli "用多智能体辩论 NVDA 和 AMD 哪个更值得继续研究"
  角色包括 Bull、Bear、Value、Macro、Risk、Judge。

策略辅助：
  python -m agent.cli "帮我回测 TSLA 的 20 日均线上穿 60 日均线策略"
  当前支持移动均线交叉策略回测。

自选股简报：
  python -m agent.cli "生成我的自选股每日简报：AAPL, MSFT, NVDA"

Trace2Skill 自进化：
  可把成功任务轨迹沉淀成新的 skills/<name>/SKILL.md。

数据源：
  Alpha Vantage、Tushare、AKShare、Yahoo Finance、SAMPLE_FALLBACK。
  若数据源限流或缺失，报告会标注来源、时间和降级情况。

边界：
  本系统只做研究辅助，不做自动交易，不承诺收益，不输出确定性买卖指令。
""".strip()


def render_welcome() -> str:
    return WELCOME


def render_help() -> str:
    return HELP
