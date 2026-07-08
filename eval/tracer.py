"""极小轨迹记录器：一步一行 JSON（JSONL），可回放。"""
from __future__ import annotations

import json
import time
from pathlib import Path


class Tracer:
    def __init__(self, path: str):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text("", encoding="utf-8")

    def log_step(
        self,
        step: int,
        tool_calls: list,
        prompt_tokens: int,
        completion_tokens: int,
        note: str = "",
    ) -> None:
        event = {
            "ts": round(time.time(), 3),
            "step": step,
            "tool_calls": tool_calls,
            "note": note,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
        }
        with self.path.open("a", encoding="utf-8") as file:
            file.write(json.dumps(event, ensure_ascii=False) + "\n")


def replay(path: str) -> None:
    """把一条 JSONL 轨迹逐步打印出来。"""
    total_tokens = 0
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        event = json.loads(line)
        tokens = event["prompt_tokens"] + event["completion_tokens"]
        total_tokens += tokens
        names = [tc["name"] for tc in event["tool_calls"]] or ["(无工具调用)"]
        print(f"  step {event['step']}: 调用 {names}  | 本步 {tokens} tok  | {event['note']}")
    print(f"  —— 轨迹共 {total_tokens} token")


if __name__ == "__main__":
    from eval.metrics import SAMPLE_RECORDS

    record = SAMPLE_RECORDS[0]
    tracer = Tracer("eval/trace_sample.jsonl")
    for index, step in enumerate(record["steps"]):
        tracer.log_step(
            index,
            step.get("tool_calls", []),
            step.get("prompt_tokens", 0),
            step.get("completion_tokens", 0),
            note=step.get("raw", "")[:40],
        )
    print(f"已写入 eval/trace_sample.jsonl（任务={record['task']}）；回放：")
    replay("eval/trace_sample.jsonl")
