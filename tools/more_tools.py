"""完整工具集：edit / grep / glob（Day6，→ v1）+ web_fetch / task_list（Day7）。

每个工具上午讲设计权衡，下午实现。这里只给签名与 TODO，便于你拆到独立文件。
建议最终拆成 edit.py / search.py / web.py / todo.py，再在 base.build_default_registry 注册。
"""
from __future__ import annotations
from .base import Tool


# --- edit：三种策略权衡（整文件重写 / unified diff / search-replace）---
def _edit(path: str, old: str = "", new: str = "") -> str:
    # TODO[Day6] 先实现最稳的 search-replace（old 在文件中唯一时替换为 new）
    #            进阶：支持 unified diff / 整文件重写，比较失败率
    raise NotImplementedError("Day6：实现 edit")


# --- grep：基于 ripgrep ---
def _grep(pattern: str, path: str = ".") -> str:
    # TODO[Day6] 调用系统 rg，返回匹配行（带文件名+行号）。与 glob 互补：grep 搜内容，glob 搜路径
    raise NotImplementedError("Day6：实现 grep")


# --- glob：按文件名模式找文件 ---
def _glob(pattern: str) -> str:
    # TODO[Day6] 用 pathlib.Path().glob / rglob 找路径
    raise NotImplementedError("Day6：实现 glob")


# --- web_fetch：URL -> markdown，控 token 预算 ---
def _web_fetch(url: str, max_tokens: int = 2000) -> str:
    # TODO[Day7] httpx 抓取 -> markdownify 转 markdown -> 截断到预算内
    raise NotImplementedError("Day7：实现 web_fetch")


# --- task_list（TodoWrite）：自维护待办，提升长任务成功率 ---
def _task_list(action: str, items: list | None = None) -> str:
    # TODO[Day7] 维护一个结构化待办（add/update/complete），作为模型的 scratchpad
    raise NotImplementedError("Day7：实现 task_list")


edit_tool = Tool("edit", "编辑文件：把 old 文本替换为 new。",
                 {"type": "object", "properties": {"path": {"type": "string"},
                  "old": {"type": "string"}, "new": {"type": "string"}},
                  "required": ["path", "old", "new"]}, _edit)
grep_tool = Tool("grep", "在文件中搜索匹配 pattern 的行（基于 ripgrep）。",
                 {"type": "object", "properties": {"pattern": {"type": "string"},
                  "path": {"type": "string"}}, "required": ["pattern"]}, _grep)
glob_tool = Tool("glob", "按通配模式查找文件路径。",
                 {"type": "object", "properties": {"pattern": {"type": "string"}},
                  "required": ["pattern"]}, _glob)
web_fetch_tool = Tool("web_fetch", "抓取 URL 并转为 markdown（受 token 预算限制）。",
                      {"type": "object", "properties": {"url": {"type": "string"}},
                       "required": ["url"]}, _web_fetch)
task_list_tool = Tool("task_list", "维护任务待办清单（add/update/complete）。",
                      {"type": "object", "properties": {"action": {"type": "string"},
                       "items": {"type": "array"}}, "required": ["action"]}, _task_list)
