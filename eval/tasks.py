"""评测任务集与指标（Day4 体验 / Day7 评测；Day10 任务成功率 / 消融）。

两类评测：
  A) 工具调用质量：在固定测试集上算三项指标（Day4 用 API 体验，Day7 系统化）。
  B) 端到端任务成功率（Day7 起 / Day10 消融）：跑一批任务，看完成率，对比不同配置。
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Callable


Trajectory = dict


@dataclass
class ToolCallCase:
    request: str                 # 用户请求
    expected_tool: str           # 期望调用的工具名
    expected_args: dict          # 期望参数（可只校验关键字段）


# Day6 固定测试集（教师会提供 ~50 条；这里给格式示例）
TOOLCALL_TESTSET: list[ToolCallCase] = [
    ToolCallCase("把 a.txt 的内容读出来", "read", {"path": "a.txt"}),
    ToolCallCase("在当前目录运行 ls", "bash", {"command": "ls"}),
    # TODO[Day7] 按你组的领域补充更多用例
]


@dataclass
class Task:
    name: str
    instruction: str
    check: Callable[[Trajectory], bool]


def _tool_calls(traj: Trajectory) -> list[dict]:
    return [
        tc
        for step in traj.get("steps", [])
        for tc in step.get("tool_calls", [])
    ]


def _check_read_config(traj: Trajectory) -> bool:
    used_read = any(tc.get("name") == "read" for tc in _tool_calls(traj))
    return used_read and "30" in traj.get("final", "")


def _check_list_dir(traj: Trajectory) -> bool:
    return any(
        tc.get("name") == "bash" and "ls" in str(tc.get("arguments", {}))
        for tc in _tool_calls(traj)
    )


def _check_finance_report(traj: Trajectory) -> bool:
    used_finance = any(
        tc.get("name") in {"finance_get_quote", "finance_generate_report", "finance_route_task"}
        for tc in _tool_calls(traj)
    )
    final = traj.get("final", "")
    has_symbol = "AAPL" in final.upper() or "苹果" in final
    has_finance_value = any(token in final for token in ["美元", "$", "价格", "风险", "报告"])
    return used_finance and has_symbol and has_finance_value


def _check_write_report(traj: Trajectory) -> bool:
    used_write = any(tc.get("name") == "write" for tc in _tool_calls(traj))
    final = traj.get("final", "").lower()
    return used_write and ("report" in final or "报告" in final)


SAMPLE_TASKS: list[Task] = [
    Task("read-config", "读取 config.json，告诉我 timeout 是多少", _check_read_config),
    Task("list-dir", "列出当前目录下的文件", _check_list_dir),
    Task("finance-report", "查询 AAPL 并生成一段包含价格和风险提示的金融研究摘要", _check_finance_report),
    Task("write-report", "把分析结果写入 report.md", _check_write_report),
]


@dataclass
class E2ETask:
    name: str
    instruction: str
    check: str                   # 如何判定成功（人工/脚本）


# Day10 端到端任务集（消融用）
E2E_TASKS: list[E2ETask] = [
    E2ETask("hello", "创建 hello.py 并运行，输出当前时间", "存在 hello.py 且运行打印了时间"),
    E2ETask("todo-report", "扫描本项目所有 Python 文件里的 TODO 注释，生成 markdown 报告",
            "生成的报告列出了真实存在的 TODO"),
    # TODO[Day10] 补充你领域的任务
]
