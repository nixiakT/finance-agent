"""工具调用三项指标（Day6 Lab3 验收用）。

  - JSON 合法率：模型输出的 tool_call 能否被 json.loads 成功解析。
  - 工具选择正确率：选对工具名的比例。
  - 参数正确率：关键参数与期望一致的比例。
"""
from __future__ import annotations
import json
import re
from typing import Any


TOOL_CALL_RE = re.compile(r"<tool_call>\s*(\{.*?\})\s*</tool_call>", re.DOTALL)


SAMPLE_RECORDS: list[dict[str, Any]] = [
    {
        "task": "read-config",
        "steps": [
            {
                "tool_calls": [{"name": "read", "arguments": {"path": "config.json"}}],
                "raw": '<tool_call>{"name":"read","arguments":{"path":"config.json"}}</tool_call>',
                "prompt_tokens": 310,
                "completion_tokens": 22,
            },
        ],
        "final": "config.json 里 timeout = 30 秒。",
    },
    {
        "task": "list-dir",
        "steps": [
            {
                "tool_calls": [{"name": "bash", "arguments": {"command": "ls"}}],
                "raw": '<tool_call>{"name":"bash","arguments":{"command":"ls"}}</tool_call>',
                "prompt_tokens": 290,
                "completion_tokens": 18,
            },
        ],
        "final": "当前目录有：main.py config.json README.md",
    },
    {
        "task": "finance-report",
        "steps": [
            {
                "tool_calls": [{"name": "finance_get_quote", "arguments": {"symbol": "AAPL"}}],
                "raw": '<tool_call>{"name":"finance_get_quote","arguments":{"symbol":"AAPL"}}</tool_call>',
                "prompt_tokens": 360,
                "completion_tokens": 28,
            },
            {
                "tool_calls": [{"name": "finance_generate_report", "arguments": {"symbol": "AAPL", "period": "3mo"}}],
                "raw": '<tool_call>{"name":"finance_generate_report","arguments":{"symbol":"AAPL","period":"3mo"}}</tool_call>',
                "prompt_tokens": 420,
                "completion_tokens": 35,
            },
        ],
        "final": "AAPL 当前价格约 195 美元，短期风险包括估值波动和财报不确定性。",
    },
    {
        "task": "read-config",
        "steps": [
            {
                "tool_calls": [],
                "raw": '<tool_call>{"name":"read","arguments":{"path":',
                "prompt_tokens": 305,
                "completion_tokens": 12,
            },
            {
                "tool_calls": [],
                "raw": "我不确定 timeout 的值。",
                "prompt_tokens": 340,
                "completion_tokens": 15,
            },
        ],
        "final": "我不确定 timeout 的值。",
    },
]


def success_rate(tasks: list, records: list[dict]) -> float:
    """对每条轨迹运行对应任务的 check，返回成功比例。"""
    by_name = {task.name: task for task in tasks}
    ok = 0
    for record in records:
        task = by_name.get(record.get("task"))
        if task and task.check(record):
            ok += 1
    return ok / max(len(records), 1)


def step_count(record: dict) -> int:
    return len(record.get("steps", []))


def token_count(record: dict) -> int:
    return sum(
        step.get("prompt_tokens", 0) + step.get("completion_tokens", 0)
        for step in record.get("steps", [])
    )


def json_valid_rate(raw_outputs: list[str] | list[dict]) -> float:
    """校验 <tool_call>{...}</tool_call> JSON；兼容旧 raw 列表与 Day3 轨迹列表。"""
    snippets = _tool_call_snippets(raw_outputs)
    ok = 0
    for snippet in snippets:
        try:
            json.loads(snippet); ok += 1
        except Exception:  # noqa
            pass
    return ok / max(len(snippets), 1)


def tool_choice_accuracy(preds: list[dict], expected_tools: list[str]) -> float:
    correct = sum(1 for p, e in zip(preds, expected_tools) if p.get("name") == e)
    return correct / max(len(expected_tools), 1)


def arg_accuracy(preds: list[dict], expected_args: list[dict]) -> float:
    """关键参数匹配率：期望 args 的每个键值都在预测里对上。"""
    correct = 0
    for p, e in zip(preds, expected_args):
        pa = p.get("arguments", {})
        if all(str(pa.get(k)) == str(v) for k, v in e.items()):
            correct += 1
    return correct / max(len(expected_args), 1)


def _extract_json(text: str) -> str:
    # TODO[Day7] 从 <tool_call>...</tool_call> 中取出 JSON 串
    start, end = text.find("{"), text.rfind("}")
    return text[start:end + 1] if start >= 0 else "{}"


def _tool_call_snippets(values: list[str] | list[dict]) -> list[str]:
    snippets: list[str] = []
    for value in values:
        if isinstance(value, dict):
            for step in value.get("steps", []):
                raw = step.get("raw", "")
                match = TOOL_CALL_RE.search(raw)
                if match:
                    snippets.append(match.group(1))
                elif "<tool_call>" in raw:
                    snippets.append(_extract_json(raw))
            continue
        snippets.append(_extract_json(value))
    return snippets


if __name__ == "__main__":
    from eval.tasks import SAMPLE_TASKS

    recs = SAMPLE_RECORDS
    print("成功率        :", success_rate(SAMPLE_TASKS, recs))
    print("平均步数      :", sum(step_count(r) for r in recs) / len(recs))
    print("平均 token    :", sum(token_count(r) for r in recs) / len(recs))
    print("JSON 合法率   :", json_valid_rate(recs))
