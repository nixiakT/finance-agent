# 项目记忆

## 产品边界

- Finance Agent 只做研究辅助、解释、回测和纸面组合，不连接券商，不执行真实交易。
- 金融数字必须来自工具并标注来源、时间和缺失项；真实来源失败时不得由模型补数。
- 微信默认使用 dry-run，本地写入 outbox，不进行真实外发。

## 研究约定

- 港股报告同时保留用户展示代码和数据源查询代码。
- 预测必须记录基准价格、方向、期限、置信度和理由，并用真实后续价格回评。
- 长任务先建立 task_list，工具失败后记录失败原因并选择替代路径。

## 常用命令

- 自检：`python -m agent.cli --selfcheck`
- 测试：`conda run -n openclaw python -m pytest -q`
- 交互入口：`python -m agent.cli`
