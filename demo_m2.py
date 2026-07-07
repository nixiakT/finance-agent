"""Day2 M2 demo: DeepSeek backend + first tool schema round trip."""
from __future__ import annotations

from agent.prompts import SYSTEM_PROMPT
from backend.client import DeepSeekBackend


tools = [
    {
        "type": "function",
        "function": {
            "name": "get_time",
            "description": "返回当前时间。用户询问现在几点、当前时间时使用。",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    }
]


def print_response(title: str, response: dict) -> None:
    print(f"\n=== {title} ===")
    print(response)


def main() -> None:
    try:
        backend = DeepSeekBackend()
    except RuntimeError as exc:
        raise SystemExit(
            f"{exc}\n"
            "请先在 .env.local 或当前 shell 环境中配置 DEEPSEEK_API_KEY 后再运行。"
        ) from exc

    plain_resp = backend.chat(
        [{"role": "user", "content": "用一句话自我介绍"}],
    )
    print_response("plain chat", plain_resp)

    tool_resp = backend.chat(
        [{"role": "user", "content": "现在几点？请调用工具，不要自己猜。"}],
        tools=tools,
    )
    print_response("tool schema round trip", tool_resp)

    prompted_tool_resp = backend.chat(
        [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": "现在几点？请调用工具，不要自己猜。"},
        ],
        tools=tools,
    )
    print_response("system prompt + tool schema", prompted_tool_resp)

    tool_call_names = [
        call.get("name")
        for response in (tool_resp, prompted_tool_resp)
        for call in response.get("tool_calls", [])
    ]
    print(f"\ntool_calls: {tool_call_names}")


if __name__ == "__main__":
    main()
