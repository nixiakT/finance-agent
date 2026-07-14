# 消融实验报告

## Demo Day 量化摘要

`python -m eval.ablation` 在固定的 6 个任务轨迹上比较“完整 system policy（含规划和错误恢复约定）”与“移除 policy”两组，并统一计算四项指标。

| 配置 | 样本数 | 成功率 | 平均步数 | 平均 token | JSON 合法率 |
|---|---:|---:|---:|---:|---:|
| 完整 system policy | 6 | 1.00 | 2.33 | 878 | 1.00 |
| 移除 policy | 6 | 0.33 | 1.00 | 158 | 0.50 |

完整策略组会先规划、调用工具并在路径失败后换路，因此 token 和步骤更多，但任务成功率与工具调用 JSON 合法率明显提高。移除策略后虽然更省 token，但更多任务直接猜测、输出不完整或在第一次失败后停止。

```bash
python -m eval.ablation
cat eval/ablation_results.json
```

限制：这组数据来自**确定性构造轨迹回放**，用于验证指标计算、轨迹格式和消融分析流程，不代表 DeepSeek 的真实成功率，更不代表投资预测准确率。真实模型抗注入评测使用 `FINANCE_RUN_LIVE_EVAL=1 python -m pytest tests/test_live_injection_eval.py -q` 单独运行，并明确消耗 API 额度。

## 目标

证明以下设计不是装饰，而是提高 Demo Day 随机任务成功率和鲁棒性的关键：

- tool result 截断
- context compaction
- task_list
- 错误恢复
- 安全层

## 实验环境

- 日期：2026-07-07
- 命令：`python -m pytest`
- 样本：项目内回归测试和 CLI smoke test

## 实验 1：tool result 截断

设计：

- 有截断：`AgentLoop(max_observation_chars=12)` 注入工具结果前调用 `truncate_observation`。
- 无截断：长 observation 原样塞回上下文。

验证：

```bash
python -m pytest tests/test_agent_cli.py::test_agent_loop_truncates_tool_results
```

结果：

| 设置 | observation 行为 | 结果 |
|---|---|---|
| 有截断 | 长结果截到 12 字符并标注总长度 | 通过 |
| 无截断 | 长工具结果会持续堆进上下文 | 风险：长任务更快撑爆上下文 |

结论：截断能保持主循环可控，尤其适合网页、行情、财报和 grep 大结果。

## 实验 2：context compaction

验证：

```bash
python -m pytest tests/test_agent_cli.py::test_maybe_compact_preserves_system_and_recent_messages
```

结果：

| 设置 | 行为 | 结果 |
|---|---|---|
| 有 compaction | 保留 system 和最近消息，早期内容变 system memo | 通过 |
| 无 compaction | messages 线性增长 | 风险：长会话 token 超预算 |

结论：compaction 保留最近上下文和关键历史摘要，适合持续交互模式。

## 实验 3：错误恢复

验证：

```bash
python -m pytest tests/test_agent_cli.py::test_agent_loop_surfaces_tool_error_as_observation
```

结果：

| 设置 | 工具失败时 | 结果 |
|---|---|---|
| 有错误 observation | `工具 fail_tool 执行失败：boom` 回填给模型 | 通过 |
| 无错误 observation | 主循环崩溃或丢失错误上下文 | 风险：现场失败无法自修复 |

结论：工具失败不是终点，而是下一轮推理的输入。

## 实验 4：task_list

验证：

```bash
python - <<'PY'
from tools.more_tools import task_list_tool
print(task_list_tool.run(action="add", items=["定位", "修改", "测试"]))
print(task_list_tool.run(action="complete", items=["定位"]))
PY
```

结果：

| 设置 | 长任务状态 | 结果 |
|---|---|---|
| 有 task_list | 可维护待办和剩余任务 | 成功 |
| 无 task_list | 只能依赖上下文自然语言记忆 | 风险：多步骤任务遗漏 |

结论：task_list 对现场随机任务的“边做边查”更稳。

## 实验 5：安全层

验证：

```bash
python - <<'PY'
from tools.shell import bash_tool
try:
    print(bash_tool.run(command="rm -rf /tmp/demo"))
except Exception as exc:
    print(type(exc).__name__, exc)
PY
```

结果：

| 设置 | 危险命令 | 结果 |
|---|---|---|
| 有安全层 | `rm` 被拦截 | 通过 |
| 无安全层 | 可能执行破坏性命令 | 不可接受 |

结论：权限分层直接降低现场误操作和 prompt injection 风险。

## 总结

这些设计分别对应评分项：

- E1：compaction + observation 截断
- E2：错误 observation
- F1：权限分层
- F2：不可信内容隔离 + 红队用例
- B2/C2：task_list 与通用工具协同
