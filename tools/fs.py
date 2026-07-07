"""文件读写工具（Day5：read / write）。"""
from __future__ import annotations

from .base import Tool
from .security import guard_read, guard_write, untrusted_block


def _read(path: str, max_bytes: int = 100_000) -> str:
    resolved = guard_read(path)
    data = resolved.read_bytes()
    truncated = len(data) > max_bytes
    text = data[:max_bytes].decode("utf-8", errors="replace")
    numbered = "\n".join(f"{idx:>4} {line}" for idx, line in enumerate(text.splitlines(), start=1))
    result = f"路径: {resolved}\n"
    if truncated:
        result += f"备注: 文件共 {len(data)} bytes，已截断到 {max_bytes} bytes。\n"
    result += numbered
    return untrusted_block("FILE", str(resolved), result)


def _write(path: str, content: str) -> str:
    resolved = guard_write(path, content)
    resolved.write_text(content, encoding="utf-8")
    return f"写入成功: {resolved} ({len(content)} chars)"


read_tool = Tool(
    name="read",
    description="读取指定路径的文本文件内容。",
    parameters={
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "文件路径"},
            "max_bytes": {"type": "integer", "description": "最多读取字节数，默认 100000"},
        },
        "required": ["path"],
    },
    run=_read,
)

write_tool = Tool(
    name="write",
    description="把内容写入指定路径（覆盖）。",
    parameters={"type": "object",
                "properties": {"path": {"type": "string"},
                               "content": {"type": "string"}},
                "required": ["path", "content"]},
    run=_write,
)
