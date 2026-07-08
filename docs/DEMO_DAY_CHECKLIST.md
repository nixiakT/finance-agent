# Demo Day 满分检查清单

## A. 系统完整性与可运行性

- A1: `python -m agent.cli "任务"` 可运行；`README.md` 有依赖和启动说明。
- A2: backend / 主循环 / 工具系统 / MCP / Skills / 安全层均存在。
- A3: 模块分层清晰；技术文档和复现步骤见 `docs/TECHNICAL_DESIGN.md`。

演示：

```bash
python -m agent.cli --selfcheck
python -m agent.cli /status
python -m agent.cli /compact
```

## B. 现场任务完成度

- 金融随机任务走 `finance_resolve_symbol`、网页核验、行情、报告、质量门禁。
- 代码随机任务可用 `glob/grep/read/edit/write/bash/task_list`。

演示：

```bash
python -m agent.cli "帮我给 minimax 做质量门禁和去劣初筛"
```

## C. 主循环与工具调用正确性

- ReAct 多轮调用、tool result 回填、工具错误 observation、终止都在测试覆盖。
- 通用工具已默认注册。

演示：

```bash
python -m agent.cli /tools
python -m pytest tests/test_agent_cli.py
```

## D. MCP + Skills

- MCP echo server 已注册为 `mcp__echo`。
- Skill 加载器扫描 `skills/*/SKILL.md`。

演示：

```bash
python -m agent.cli /mcp
python - <<'PY'
from tools.base import build_default_registry
print(build_default_registry().get("mcp__echo").run(text="ok"))
PY
```

## E. 上下文管理与鲁棒性

- `truncate_observation` 和 `maybe_compact` 有测试。
- 工具失败会变成 observation。

演示：

```bash
python -m pytest tests/test_agent_cli.py::test_agent_loop_surfaces_tool_error_as_observation
```

## F. 安全机制

- 只读/写入/shell 权限分层。
- 不可信网页/文件内容加边界。
- 危险命令拦截。

演示：

```bash
python -m agent.cli /security
python - <<'PY'
from tools.shell import bash_tool
try:
    print(bash_tool.run(command="rm -rf /tmp/demo"))
except Exception as exc:
    print(type(exc).__name__, exc)
PY
```

## G. 技术理解与答辩

讲解重点：

- 为什么 `edit` 使用唯一 search-replace。
- 为什么 tool result 要截断。
- 为什么错误作为 observation 而不是崩溃。
- 为什么网页/文件内容要标记为 untrusted。
- 为什么 MCP 工具加 `mcp__` 命名空间。

## H. 消融实验与技术文档

- 消融报告：`docs/ABLATION_REPORT.md`
- 技术文档：`docs/TECHNICAL_DESIGN.md`

最终验证命令：

```bash
python -m pytest
python -Werror -m compileall agent backend finance mcp skills tools trace2skill wechat scheduler tests
python -m agent.cli --selfcheck
```
