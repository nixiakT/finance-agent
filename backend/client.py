"""大模型后端：DeepSeek API 客户端（OpenAI 兼容）。

本课程的 mini-OpenClaw 不本地部署模型，而是调用 DeepSeek API 作为"大脑"。
DeepSeek 的接口与 OpenAI 完全兼容，所以下面用通用的 OpenAI 协议写法，
只要改 base_url / api_key / model 就能换任意 OpenAI 兼容厂商。

接口约定（和 FakeBackend 一致，主循环 agent/loop.py 只认这个）：
    chat(messages, tools) -> {"role": "assistant", "content": str, "tool_calls": [ {name, arguments}, ... ]}

环境变量：
    DEEPSEEK_API_KEY   你的 key（千万别提交进 git！）
    DEEPSEEK_BASE_URL  默认 https://api.deepseek.com
    DEEPSEEK_MODEL     默认 deepseek-chat
"""
from __future__ import annotations
import os
import json
from typing import Any

import httpx


class DeepSeekBackend:
    def __init__(self,
                 api_key: str | None = None,
                 base_url: str | None = None,
                 model: str | None = None,
                 timeout: float = 60.0):
        self.api_key = api_key or os.environ.get("DEEPSEEK_API_KEY", "")
        self.base_url = (base_url or os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com")).rstrip("/")
        self.model = model or os.environ.get("DEEPSEEK_MODEL", "deepseek-chat")
        if not self.api_key:
            raise RuntimeError("缺少 DEEPSEEK_API_KEY 环境变量")
        self._client = httpx.Client(timeout=timeout)

    def chat(self, messages: list[dict[str, Any]], tools: list[dict] | None = None,
             temperature: float = 0.0) -> dict[str, Any]:
        """一次（非流式）对话补全，返回归一化的 assistant 消息。"""
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": self._to_openai_messages(messages),
            "temperature": temperature,
        }
        if tools:
            payload["tools"] = tools           # OpenAI tools 格式，base.Tool.schema() 已生成
            payload["tool_choice"] = "auto"

        resp = self._client.post(
            f"{self.base_url}/v1/chat/completions",
            headers={"Authorization": f"Bearer {self.api_key}"},
            json=payload,
        )
        resp.raise_for_status()
        msg = resp.json()["choices"][0]["message"]
        return self._normalize(msg)

    # --- 把内部 messages（含 role=tool）转成 OpenAI 标准格式 ---
    def _to_openai_messages(self, messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
        out = []
        for m in messages:
            role = m.get("role")
            if role == "tool":
                # OpenAI 要求 tool 消息带 tool_call_id；最小实现可用 name 兜底
                out.append({"role": "tool", "content": str(m.get("content", "")),
                            "tool_call_id": m.get("tool_call_id", m.get("name", "tool"))})
            elif role == "assistant" and m.get("tool_calls"):
                out.append({"role": "assistant", "content": m.get("content") or None,
                            "tool_calls": self._to_openai_tool_calls(m["tool_calls"])})
            else:
                out.append({"role": role, "content": m.get("content", "")})
        return out

    @staticmethod
    def _to_openai_tool_calls(calls: list[dict]) -> list[dict]:
        out = []
        for i, c in enumerate(calls):
            out.append({"id": c.get("id", f"call_{i}"), "type": "function",
                        "function": {"name": c["name"],
                                     "arguments": json.dumps(c.get("arguments", {}), ensure_ascii=False)}})
        return out

    # --- 把 OpenAI 返回归一化成内部格式 ---
    @staticmethod
    def _normalize(msg: dict[str, Any]) -> dict[str, Any]:
        tool_calls = []
        for tc in (msg.get("tool_calls") or []):
            fn = tc.get("function", {})
            try:
                args = json.loads(fn.get("arguments") or "{}")
            except json.JSONDecodeError:
                args = {}
            tool_calls.append({"id": tc.get("id"), "name": fn.get("name"), "arguments": args})
        return {"role": "assistant", "content": msg.get("content") or "", "tool_calls": tool_calls}
