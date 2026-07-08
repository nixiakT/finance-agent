"""最小消融：有/无 system-prompt 两组样本轨迹的成功率对比。"""
from __future__ import annotations

from pathlib import Path

from eval.metrics import success_rate, token_count
from eval.tasks import SAMPLE_TASKS


GROUP_WITH_SYS = [
    {
        "task": "read-config",
        "steps": [
            {
                "tool_calls": [{"name": "read", "arguments": {"path": "config.json"}}],
                "raw": '<tool_call>{"name":"read","arguments":{"path":"config.json"}}</tool_call>',
                "prompt_tokens": 330,
                "completion_tokens": 22,
            }
        ],
        "final": "config.json 里 timeout = 30 秒。",
    },
    {
        "task": "list-dir",
        "steps": [
            {
                "tool_calls": [{"name": "bash", "arguments": {"command": "ls"}}],
                "raw": '<tool_call>{"name":"bash","arguments":{"command":"ls"}}</tool_call>',
                "prompt_tokens": 300,
                "completion_tokens": 18,
            }
        ],
        "final": "当前目录有：main.py config.json README.md",
    },
    {
        "task": "finance-report",
        "steps": [
            {
                "tool_calls": [{"name": "finance_generate_report", "arguments": {"symbol": "AAPL", "period": "3mo"}}],
                "raw": '<tool_call>{"name":"finance_generate_report","arguments":{"symbol":"AAPL","period":"3mo"}}</tool_call>',
                "prompt_tokens": 390,
                "completion_tokens": 32,
            }
        ],
        "final": "AAPL 当前价格约 195 美元，报告提示估值和市场波动风险。",
    },
]


GROUP_NO_SYS = [
    {
        "task": "read-config",
        "steps": [{"tool_calls": [], "raw": "timeout 应该是个常见的默认值。", "prompt_tokens": 120, "completion_tokens": 14}],
        "final": "timeout 应该是个常见的默认值。",
    },
    {
        "task": "list-dir",
        "steps": [{"tool_calls": [], "raw": "你可以自己用 ls 看看。", "prompt_tokens": 110, "completion_tokens": 12}],
        "final": "你可以自己用 ls 看看。",
    },
    {
        "task": "finance-report",
        "steps": [{"tool_calls": [], "raw": "AAPL 应该还不错。", "prompt_tokens": 130, "completion_tokens": 16}],
        "final": "AAPL 应该还不错，但我没有查询实时数据。",
    },
]


def summarize(name: str, records: list[dict]) -> float:
    rate = success_rate(SAMPLE_TASKS, records)
    avg_tokens = sum(token_count(record) for record in records) / len(records)
    print(f"{name:16s} 成功率={rate:.2f}  平均token={avg_tokens:.0f}")
    return rate


def write_notes(path: str | Path = "eval/ablation_notes.md") -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with_sys = success_rate(SAMPLE_TASKS, GROUP_WITH_SYS)
    no_sys = success_rate(SAMPLE_TASKS, GROUP_NO_SYS)
    with_tok = sum(token_count(record) for record in GROUP_WITH_SYS) / len(GROUP_WITH_SYS)
    no_tok = sum(token_count(record) for record in GROUP_NO_SYS) / len(GROUP_NO_SYS)
    target.write_text(
        "\n".join([
            "# 消融草稿（Day3 · 样本轨迹）",
            "- 变量：system-prompt（有 / 无），其余任务集与样本模型设定固定。",
            f"- 固定项：任务集=SAMPLE_TASKS；样本数=每组 {len(GROUP_WITH_SYS)} 条；指标=成功率与平均 token。",
            f"- 结果：有 system-prompt 成功率={with_sys:.2f}，平均 token={with_tok:.0f}；无 system-prompt 成功率={no_sys:.2f}，平均 token={no_tok:.0f}。",
            "- 归因：无 system-prompt 时 agent 不知道工具调用约定，倾向直接猜测或把任务推回用户，因此任务成功率下降。",
            "- 局限：样本轨迹是构造的且数量很小；D4 接入真实 agent trace 后应多轮运行并报告均值与方差。",
            "",
        ]),
        encoding="utf-8",
    )
    return target


if __name__ == "__main__":
    print("=== 消融：有/无 system-prompt ===")
    a = summarize("有 system-prompt", GROUP_WITH_SYS)
    b = summarize("无 system-prompt", GROUP_NO_SYS)
    print(f"结论：system-prompt 使成功率 {b:.2f} -> {a:.2f}（Δ={a-b:+.2f}）")
    print(f"消融草稿已写入：{write_notes()}")
