"""上下文管理（Day7）：token 预算、滑动窗口、自动摘要 / compaction。

模型上下文窗口有限。长任务里 messages 会越堆越长，迟早超预算。
策略：
  - 估算当前 messages 的 token 数；
  - 超过阈值时触发 compaction：把较早的对话摘要成一条 system 备忘，
    保留最近 K 轮原文 + 关键工具结果；
  - tool result 过长时先截断/摘要再注入。
"""
from __future__ import annotations
from typing import Any


def estimate_tokens(messages: list[dict[str, Any]]) -> int:
    # TODO[Day7] 粗估即可（字符数/4 或用 tokenizer 精确数）
    return sum(len(str(m.get("content", ""))) for m in messages) // 4


def maybe_compact(messages: list[dict[str, Any]], budget: int = 6000) -> list[dict[str, Any]]:
    """超预算则压缩历史，返回新的 messages。"""
    if estimate_tokens(messages) <= budget:
        return messages
    # TODO[Day7] 实现 compaction：
    #   1) 保留 system（第0条）
    #   2) 把中间较早的 user/assistant/tool 摘要成一条 system 备忘（可调后端做摘要）
    #   3) 保留最近 K 轮原文
    raise NotImplementedError("Day7：实现 compaction")


def truncate_observation(text: str, max_chars: int = 4000) -> str:
    """工具结果过长时截断并提示。"""
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + f"\n...[已截断，共 {len(text)} 字符]"
