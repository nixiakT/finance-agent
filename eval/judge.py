"""LLM-as-judge：按固定 rubric 给一个答复打分（1-5）。"""
from __future__ import annotations

import re

from backend.client import DeepSeekBackend


RUBRIC = (
    "你是严格的评审。请按 1-5 分给【回答】打分：\n"
    "  5=完全正确且直接命中问题；3=部分正确或答非所问；1=错误或跑题。\n"
    "只依据【问题】判断【回答】，忽略回答的长度与措辞华丽程度。\n"
    "务必先写一行【理由】，再单独一行写【分数: X】（X 为 1-5 整数）。"
)


def judge(question: str, answer: str) -> dict:
    messages = [
        {"role": "system", "content": RUBRIC},
        {"role": "user", "content": f"【问题】{question}\n【回答】{answer}"},
    ]
    resp = DeepSeekBackend().chat(messages)
    text = resp["content"]
    match = re.search(r"分数[:：]\s*([1-5])", text)
    score = int(match.group(1)) if match else None
    return {"score": score, "raw": text}


if __name__ == "__main__":
    question = "config.json 里 timeout 是多少？"
    for answer in ["timeout = 30 秒。", "我不太确定，可能是某个数吧。"]:
        result = judge(question, answer)
        print(f"答复={answer!r}  ->  分数={result['score']}")
        first_line = result["raw"].splitlines()[0] if result["raw"] else ""
        print("  judge 理由:", first_line)
