# finance

`finance/` 是确定性金融研究层：负责获取和规范化多源数据、计算指标、检查数据质量、生成结构化报告，并维护预测与纸面组合记录。模型不直接计算关键数值，也不直接拼接 Provider 原始响应。

## 主执行路径

`FinanceResearchAgent`（`agent.py`）是统一入口：

```text
标的解析
  -> ProviderChain 获取 quote/history/financials/news
  -> StockSnapshot 统一结构
  -> 指标与 QualityGate
  -> 报告、比较或多角色辩论
  -> 可选的预测账本/纸面组合记录
```

## 关键文件

- `data.py`：Alpha Vantage、Yahoo/yfinance、Tushare、AKShare 与样例 Provider；缓存、并发查询、超时、熔断、来源覆盖和跨源融合。
- `models.py`：`Quote`、`Candle`、`Financials`、`NewsItem`、`StockSnapshot` 等统一数据模型。
- `indicators.py`：MA、RSI、MACD、收益率和波动率等确定性计算。
- `quality.py`：时效、跨源价差、字段完整性、新闻覆盖和样例数据检查。
- `report.py`：结构化研究报告渲染。
- `debate_orchestrator.py`：共享编号证据下的 Bull、Bear、Value、Macro/Risk、Anti-Bias 与 Judge 流程。
- `predictions.py`、`history_learning.py`：预测账本、到期评价、walk-forward 样本和历史校准。
- `paper_portfolio.py`：纸面组合与交易记录；不执行真实交易。

## 关键设计决策

- `ProviderChain` 不直接拼接全部 API 输出，而是按时效、完整性和兼容性选择或融合，并保留成功源、失败源、选中源及冲突。
- 缓存位于进程内存，并设置分类型 TTL；缓存命中仍恢复来源覆盖信息。
- 只有币种、报告期和口径兼容的基本面字段才允许融合。
- 新闻先做公司相关性过滤、去重和来源多样化。
- 未经历史校准的数值只称为“信号强度”，不冒充统计概率。

## 安全与结论边界

系统只提供研究辅助。QualityGate 会降低或阻止证据不足的结论；多智能体 Judge 也必须受证据编号、方向枚举和数据完整性约束。回测、历史命中率和纸面组合都不能解释为未来收益保证或真实交易回执。
