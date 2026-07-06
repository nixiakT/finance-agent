"""工具调用三项指标（Day6 Lab3 验收用）。

  - JSON 合法率：模型输出的 tool_call 能否被 json.loads 成功解析。
  - 工具选择正确率：选对工具名的比例。
  - 参数正确率：关键参数与期望一致的比例。
"""
from __future__ import annotations
import json
from typing import Any


def json_valid_rate(raw_outputs: list[str]) -> float:
    """raw_outputs：模型为每条用例生成的 <tool_call>{...}</tool_call> 原文。"""
    ok = 0
    for out in raw_outputs:
        # TODO[Day7] 抽出 {...} 部分尝试 json.loads（可复用 prompt.render.parse_tool_calls）
        try:
            json.loads(_extract_json(out)); ok += 1
        except Exception:  # noqa
            pass
    return ok / max(len(raw_outputs), 1)


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
