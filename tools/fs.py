"""文件读写工具（Day5：read / write）。"""
from __future__ import annotations
from .base import Tool


def _read(path: str, max_bytes: int = 100_000) -> str:
    # TODO[Day5] 读取文件，超长截断并提示；带行号更利于后续 edit 定位
    raise NotImplementedError("Day5：实现 read")


def _write(path: str, content: str) -> str:
    # TODO[Day5] 写文件；注意权限层（Day10）后续会拦截工作目录外的写入
    raise NotImplementedError("Day5：实现 write")


read_tool = Tool(
    name="read",
    description="读取指定路径的文本文件内容。",
    parameters={"type": "object",
                "properties": {"path": {"type": "string", "description": "文件路径"}},
                "required": ["path"]},
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
