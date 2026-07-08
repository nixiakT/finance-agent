"""上下文管理（Day7）：token 预算、滑动窗口、自动摘要 / compaction。

模型上下文窗口有限。长任务里 messages 会越堆越长，迟早超预算。
策略：
  - 估算当前 messages 的 token 数；
  - 超过阈值时触发 compaction：把较早的对话摘要成一条 system 备忘，
    保留最近 K 轮原文 + 关键工具结果；
  - tool result 过长时先截断/摘要再注入。
"""
from __future__ import annotations
import re
from typing import Any


COMPACTION_PROMPT = """你正在为命令行金融研究智能体压缩会话上下文。
请生成一份给后续模型继续工作的交接摘要，必须包含：
- 当前进展和已经做出的关键决定
- 用户偏好、约束、不能丢失的上下文
- 已经用过的重要工具结果或数据来源
- 下一步还需要做什么

要求：简洁、结构化、只保留可复用信息；不要编造；不要保留 API key、token、cookie、密码或其他密钥。"""

COMPACTED_PREFIX = "Earlier conversation was compacted. Handoff summary:"

SECRET_PATTERNS = (
    re.compile(r"(?i)(api[_-]?key|token|secret|password|cookie)\s*[:=]\s*['\"]?[^'\"\s]+"),
    re.compile(r"\bsk-[A-Za-z0-9_\-]{16,}\b"),
)


def estimate_tokens(messages: list[dict[str, Any]]) -> int:
    # TODO[Day7] 粗估即可（字符数/4 或用 tokenizer 精确数）
    return sum(len(str(m.get("content", ""))) for m in messages) // 4


def maybe_compact(messages: list[dict[str, Any]], budget: int = 6000) -> list[dict[str, Any]]:
    """超预算则压缩历史，返回新的 messages。"""
    if estimate_tokens(messages) <= budget:
        return messages
    if len(messages) <= 4:
        return messages

    system = messages[0]
    keep_recent = min(8, max(3, len(messages) // 3))
    older = messages[1:-keep_recent]
    recent = messages[-keep_recent:]
    memo_lines = ["Earlier conversation was compacted. Key prior entries:"]
    for message in older[-12:]:
        role = message.get("role", "message")
        name = f"/{message.get('name')}" if message.get("name") else ""
        content = truncate_observation(str(message.get("content", "")), 500)
        content = " ".join(content.split())
        if content:
            memo_lines.append(f"- {role}{name}: {content}")
    compacted = {"role": "system", "content": "\n".join(memo_lines)}
    return [system, compacted, *recent]


def compact_with_model(
    messages: list[dict[str, Any]],
    backend: Any,
    *,
    keep_recent: int = 8,
    max_source_chars: int = 12000,
    max_message_chars: int = 1200,
    max_summary_chars: int = 4000,
) -> tuple[list[dict[str, Any]], bool]:
    """Manually compact conversation history using the configured backend.

    Returns ``(messages, used_model_summary)``. If the model summary fails or is
    empty, falls back to the deterministic local compaction path.
    """
    if len(messages) <= 3:
        return messages, False

    system = messages[0]
    recent_count = min(keep_recent, max(1, len(messages) // 3))
    older = messages[1:-recent_count]
    recent = messages[-recent_count:]
    if not older:
        return messages, False

    source = _render_compaction_source(
        older,
        max_source_chars=max_source_chars,
        max_message_chars=max_message_chars,
    )
    summary = _summarize_with_backend(backend, source)
    if not summary:
        compacted = maybe_compact(messages, budget=0)
        return compacted, False

    summary = truncate_observation(_sanitize_for_compaction(summary), max_summary_chars)
    compacted = {"role": "system", "content": f"{COMPACTED_PREFIX}\n{summary}"}
    return [system, compacted, *recent], True


def truncate_observation(text: str, max_chars: int = 4000) -> str:
    """工具结果过长时截断并提示。"""
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + f"\n...[已截断，共 {len(text)} 字符]"


def _render_compaction_source(
    messages: list[dict[str, Any]],
    *,
    max_source_chars: int,
    max_message_chars: int,
) -> str:
    lines: list[str] = []
    total = 0
    for index, message in enumerate(messages, start=1):
        role = str(message.get("role", "message"))
        name = f"/{message.get('name')}" if message.get("name") else ""
        content = _sanitize_for_compaction(str(message.get("content", "")))
        content = " ".join(truncate_observation(content, max_message_chars).split())
        tool_calls = message.get("tool_calls") or []
        if tool_calls:
            names = ", ".join(str(call.get("name", "")) for call in tool_calls if call.get("name"))
            if names:
                content = f"{content} [tool_calls: {names}]".strip()
        line = f"{index}. {role}{name}: {content}"
        if total + len(line) > max_source_chars:
            lines.append("...[source truncated before model compaction]")
            break
        lines.append(line)
        total += len(line)
    return "\n".join(lines)


def _summarize_with_backend(backend: Any, source: str) -> str:
    prompt_messages = [
        {"role": "system", "content": COMPACTION_PROMPT},
        {"role": "user", "content": source},
    ]
    try:
        response = backend.chat(prompt_messages, tools=[])
    except Exception:
        return ""
    return str(response.get("content", "")).strip()


def _sanitize_for_compaction(text: str) -> str:
    clean = text
    for pattern in SECRET_PATTERNS:
        clean = pattern.sub("[REDACTED_SECRET]", clean)
    return clean
