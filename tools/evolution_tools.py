"""Finance self-evolution tools."""
from __future__ import annotations

from finance.evolution import add_memory, extract_learning, render_memories
from trace2skill import generate_skill
from .base import Tool


def _finance_memory_add(
    content: str,
    category: str = "preference",
    source: str = "user",
    symbol: str = "",
    confidence: str = "medium",
) -> str:
    path = add_memory(content, category=category, source=source, symbol=symbol, confidence=confidence)
    return f"已写入金融记忆: {path}"


def _finance_memory_list(limit: int = 20) -> str:
    return render_memories(limit)


def _finance_evolve_from_trace(
    task: str,
    trace: str,
    answer: str = "",
    skill_name: str = "",
    overwrite: bool = True,
) -> str:
    learning = extract_learning(task=task, answer=answer, trace=trace)
    add_memory(learning, category="workflow", source="trace2skill", confidence="high")
    if not skill_name:
        return "\n".join([
            "Finance evolution completed.",
            f"- memory: .finance_agent/finance_memory.jsonl",
            "- skill: unchanged (core finance-research-evolution remains stable)",
            "",
            learning,
        ])
    result = generate_skill(
        task=task,
        trace=learning + "\n" + trace,
        skill_name=skill_name,
        description=(
            "当用户希望把金融研究纠错、数据源核验、风险边界、标的解析经验"
            "沉淀为可复用流程时使用。"
        ),
        overwrite=overwrite,
    )
    return "\n".join([
        "Finance evolution completed.",
        f"- memory: .finance_agent/finance_memory.jsonl",
        f"- skill: {result.path}",
        "",
        result.content,
    ])


finance_memory_add_tool = Tool(
    name="finance_memory_add",
    description="保存金融研究偏好、纠错、数据源经验、风险规则或策略复盘到本地记忆。",
    parameters={
        "type": "object",
        "properties": {
            "content": {"type": "string"},
            "category": {"type": "string", "description": "preference/correction/source/risk/workflow/symbol/strategy"},
            "source": {"type": "string"},
            "symbol": {"type": "string"},
            "confidence": {"type": "string", "description": "low/medium/high"},
        },
        "required": ["content"],
    },
    run=_finance_memory_add,
)

finance_memory_list_tool = Tool(
    name="finance_memory_list",
    description="列出本地金融研究记忆。",
    parameters={
        "type": "object",
        "properties": {"limit": {"type": "integer", "description": "最多返回条数"}},
    },
    run=_finance_memory_list,
)

finance_evolve_from_trace_tool = Tool(
    name="finance_evolve_from_trace",
    description="从金融研究任务轨迹中提炼记忆并生成/更新金融自进化 Skill。",
    parameters={
        "type": "object",
        "properties": {
            "task": {"type": "string"},
            "trace": {"type": "string"},
            "answer": {"type": "string"},
            "skill_name": {"type": "string"},
            "overwrite": {"type": "boolean"},
        },
        "required": ["task", "trace"],
    },
    run=_finance_evolve_from_trace,
)


evolution_tools = [
    finance_memory_add_tool,
    finance_memory_list_tool,
    finance_evolve_from_trace_tool,
]
