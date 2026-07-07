"""完整工具集：edit / grep / glob（Day6，→ v1）+ web_fetch / task_list（Day7）。

每个工具上午讲设计权衡，下午实现。这里只给签名与 TODO，便于你拆到独立文件。
建议最终拆成 edit.py / search.py / web.py / todo.py，再在 base.build_default_registry 注册。
"""
from __future__ import annotations

import fnmatch
import subprocess
from pathlib import Path

from .base import Tool
from .security import WORKSPACE_ROOT, guard_read, guard_write


# --- edit：三种策略权衡（整文件重写 / unified diff / search-replace）---
def _edit(path: str, old: str = "", new: str = "") -> str:
    resolved = guard_read(path)
    content = resolved.read_text(encoding="utf-8")
    count = content.count(old)
    if not old:
        raise ValueError("old 不能为空")
    if count == 0:
        raise ValueError("edit 匹配失败：old 文本不存在")
    if count > 1:
        raise ValueError(f"edit 匹配不唯一：old 出现 {count} 次，请提供更精确上下文")
    updated = content.replace(old, new, 1)
    guard_write(path, updated)
    resolved.write_text(updated, encoding="utf-8")
    return f"编辑成功: {resolved} (替换 1 处)"


# --- grep：基于 ripgrep ---
def _grep(pattern: str, path: str = ".") -> str:
    resolved = guard_read(path) if Path(path).expanduser().is_file() else _guard_directory(path)
    try:
        result = subprocess.run(
            ["rg", "--line-number", "--with-filename", "--no-heading", "--color", "never", pattern, str(resolved)],
            cwd=WORKSPACE_ROOT,
            text=True,
            capture_output=True,
            timeout=20,
            check=False,
        )
    except FileNotFoundError:
        return _grep_python(pattern, resolved)
    if result.returncode == 1:
        return "未找到匹配。"
    if result.returncode != 0:
        return f"grep 失败: {result.stderr.strip()}"
    return _truncate(result.stdout)


# --- glob：按文件名模式找文件 ---
def _glob(pattern: str, limit: int = 200) -> str:
    matches: list[str] = []
    for path in WORKSPACE_ROOT.rglob("*"):
        if any(part in {".git", "__pycache__", ".pytest_cache"} for part in path.parts):
            continue
        rel = path.relative_to(WORKSPACE_ROOT).as_posix()
        if fnmatch.fnmatch(rel, pattern) or fnmatch.fnmatch(path.name, pattern):
            matches.append(rel)
            if len(matches) >= limit:
                break
    if not matches:
        return "未找到匹配文件。"
    return "\n".join(matches)


# --- web_fetch：URL -> markdown，控 token 预算 ---
def _web_fetch(url: str, max_tokens: int = 2000) -> str:
    from finance.web import web_fetch

    return web_fetch(url, max_tokens * 4)


# --- task_list（TodoWrite）：自维护待办，提升长任务成功率 ---
def _task_list(action: str, items: list | None = None) -> str:
    normalized = action.lower().strip()
    store = _task_store()
    current = _load_tasks(store)
    if normalized in {"clear", "reset"}:
        store.write_text("", encoding="utf-8")
        return "任务清单已清空。"
    if normalized in {"add", "set", "update"}:
        if not items:
            raise ValueError("items 不能为空")
        current = [str(item) for item in items]
        store.write_text("\n".join(current), encoding="utf-8")
        return "任务清单已更新：\n" + "\n".join(f"- {item}" for item in current)
    if normalized in {"complete", "done"}:
        if items:
            done = {str(item) for item in items}
            current = [item for item in current if item not in done]
            store.write_text("\n".join(current), encoding="utf-8")
        return "剩余任务：\n" + ("\n".join(f"- {item}" for item in current) if current else "无")
    if normalized in {"list", "show"}:
        return "当前任务：\n" + ("\n".join(f"- {item}" for item in current) if current else "无")
    raise ValueError("action 必须是 add/update/complete/list/clear")


edit_tool = Tool("edit", "编辑文件：把 old 文本替换为 new。",
                 {"type": "object", "properties": {"path": {"type": "string"},
                  "old": {"type": "string"}, "new": {"type": "string"}},
                  "required": ["path", "old", "new"]}, _edit)
grep_tool = Tool("grep", "在文件中搜索匹配 pattern 的行（基于 ripgrep）。",
                 {"type": "object", "properties": {"pattern": {"type": "string"},
                  "path": {"type": "string"}}, "required": ["pattern"]}, _grep)
glob_tool = Tool("glob", "按通配模式查找文件路径。",
                 {"type": "object", "properties": {"pattern": {"type": "string"},
                  "limit": {"type": "integer"}},
                  "required": ["pattern"]}, _glob)
web_fetch_tool = Tool("web_fetch", "抓取 URL 并转为 markdown（受 token 预算限制）。",
                      {"type": "object", "properties": {"url": {"type": "string"}},
                       "required": ["url"]}, _web_fetch)
task_list_tool = Tool("task_list", "维护任务待办清单（add/update/complete）。",
                      {"type": "object", "properties": {"action": {"type": "string"},
                       "items": {"type": "array"}}, "required": ["action"]}, _task_list)


def _guard_directory(path: str) -> Path:
    candidate = Path(path).expanduser()
    if not candidate.is_absolute():
        candidate = WORKSPACE_ROOT / candidate
    resolved = candidate.resolve()
    resolved.relative_to(WORKSPACE_ROOT)
    if not resolved.is_dir():
        raise FileNotFoundError(f"目录不存在: {path}")
    return resolved


def _grep_python(pattern: str, path: Path) -> str:
    import re

    regex = re.compile(pattern)
    rows: list[str] = []
    files = [path] if path.is_file() else [p for p in path.rglob("*") if p.is_file()]
    for file_path in files:
        if any(part in {".git", "__pycache__", ".pytest_cache"} for part in file_path.parts):
            continue
        try:
            lines = file_path.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            continue
        for index, line in enumerate(lines, start=1):
            if regex.search(line):
                rel = file_path.relative_to(WORKSPACE_ROOT)
                rows.append(f"{rel}:{index}:{line}")
                if len(rows) >= 200:
                    return "\n".join(rows)
    return "\n".join(rows) if rows else "未找到匹配。"


def _task_store() -> Path:
    path = WORKSPACE_ROOT / ".agent_task_list"
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def _load_tasks(path: Path) -> list[str]:
    if not path.exists():
        return []
    return [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _truncate(text: str, limit: int = 12_000) -> str:
    if len(text) <= limit:
        return text
    return text[:limit] + f"\n...[已截断，共 {len(text)} 字符]"
