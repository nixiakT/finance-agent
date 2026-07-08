# 消融草稿（Day3 · 样本轨迹）
- 变量：system-prompt（有 / 无），其余任务集与样本模型设定固定。
- 固定项：任务集=SAMPLE_TASKS；样本数=每组 3 条；指标=成功率与平均 token。
- 结果：有 system-prompt 成功率=1.00，平均 token=364；无 system-prompt 成功率=0.00，平均 token=134。
- 归因：无 system-prompt 时 agent 不知道工具调用约定，倾向直接猜测或把任务推回用户，因此任务成功率下降。
- 局限：样本轨迹是构造的且数量很小；D4 接入真实 agent trace 后应多轮运行并报告均值与方差。
