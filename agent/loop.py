"""ReAct 主循环（Agent 的心脏）。

  while 没到最终答复:
      assistant = backend.chat(messages, tools)      # 模型这一步：思考 or 调工具
      if assistant 有 tool_calls:
          for call in tool_calls:
              obs = registry.get(call.name).run(**call.arguments)   # 执行工具
              messages.append(tool_result(obs))                     # 注入 observation
      else:
          return assistant.content                                 # 最终答复

工具结果会被截断，长会话会按预算压缩，避免把上下文撑爆。
"""
from __future__ import annotations
from typing import Any, Callable

from agent.context import compact_with_model, maybe_compact, truncate_observation
from tools.base import ToolRegistry


class AgentLoop:
    def __init__(self, backend: Any, registry: ToolRegistry, system_prompt: str,
                 max_turns: int = 20,
                 context_budget: int = 6000,
                 max_observation_chars: int = 4000,
                 observer: Callable[[str, dict[str, Any]], None] | None = None):
        self.backend = backend
        self.registry = registry
        self.system_prompt = system_prompt
        self.max_turns = max_turns          # 防死循环：硬上限
        self.context_budget = context_budget
        self.max_observation_chars = max_observation_chars
        self.observer = observer

    def run(self, user_task: str) -> str:
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": user_task},
        ]
        return self.run_messages(messages)

    def run_messages(self, messages: list[dict[str, Any]]) -> str:
        for turn in range(self.max_turns):
            compacted = maybe_compact(messages, self.context_budget)
            if compacted is not messages:
                messages[:] = compacted
                self._emit("context_compacted", {"messages": len(messages)})
            self._emit("model_start", {"turn": turn + 1})
            assistant = self.backend.chat(messages, tools=self.registry.schemas())
            self._emit("model_end", {
                "turn": turn + 1,
                "tool_calls": [call.get("name", "") for call in assistant.get("tool_calls") or []],
                "content_preview": _preview(assistant.get("content", "")),
            })
            messages.append({"role": "assistant",
                             "content": assistant.get("content", ""),
                             "tool_calls": assistant.get("tool_calls", [])})

            tool_calls = assistant.get("tool_calls") or []
            if not tool_calls:
                return assistant.get("content", "")

            for call in tool_calls:
                tool = self.registry.get(call["name"])
                if tool is None:
                    obs = f"错误：未知工具 {call['name']}"
                else:
                    try:
                        self._emit("tool_start", {
                            "name": call["name"],
                            "arguments": call.get("arguments", {}),
                        })
                        obs = truncate_observation(
                            str(tool.run(**call.get("arguments", {}))),
                            self.max_observation_chars,
                        )
                        self._emit("tool_end", {
                            "name": call["name"],
                            "preview": _preview(obs),
                        })
                    except Exception as exc:  # noqa: BLE001 - surface tool errors to the model/user
                        obs = f"工具 {call['name']} 执行失败：{exc}"
                        self._emit("tool_error", {
                            "name": call["name"],
                            "error": str(exc),
                        })
                messages.append({"role": "tool", "name": call["name"],
                                 "tool_call_id": call.get("id"), "content": obs})

        return "[达到最大轮数上限，未完成任务]"

    def _emit(self, event: str, payload: dict[str, Any]) -> None:
        if self.observer:
            self.observer(event, payload)


class AgentSession:
    def __init__(self, loop: AgentLoop, max_history_messages: int = 24):
        self.loop = loop
        self.max_history_messages = max_history_messages
        self.messages: list[dict[str, Any]] = [
            {"role": "system", "content": loop.system_prompt},
        ]

    def ask(self, user_task: str) -> str:
        self.messages.append({"role": "user", "content": user_task})
        answer = self.loop.run_messages(self.messages)
        self._compact_history()
        return answer

    def reset(self) -> None:
        self.messages = [{"role": "system", "content": self.loop.system_prompt}]

    def compact(self) -> str:
        before = len(self.messages)
        compacted, used_model_summary = compact_with_model(self.messages, self.loop.backend)
        if compacted is self.messages:
            return "当前会话上下文很短，无需压缩。"
        self.messages[:] = compacted
        self.loop._emit("context_compacted", {
            "messages": len(self.messages),
            "manual": True,
            "model_summary": used_model_summary,
        })
        method = "模型摘要" if used_model_summary else "规则摘要"
        return f"已压缩当前会话上下文（{method}）：{before} -> {len(self.messages)} 条消息。"

    def _compact_history(self) -> None:
        if len(self.messages) <= self.max_history_messages + 1:
            return
        system = self.messages[0]
        self.messages = [system, *self.messages[-self.max_history_messages:]]


def _preview(text: str, limit: int = 180) -> str:
    clean = " ".join(str(text).split())
    if len(clean) <= limit:
        return clean
    return clean[:limit] + "..."
