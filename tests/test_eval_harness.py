from __future__ import annotations

import json
from pathlib import Path


def test_day3_tasks_include_programmatic_finance_domain_check() -> None:
    from eval.tasks import SAMPLE_TASKS

    names = [task.name for task in SAMPLE_TASKS]
    assert len(SAMPLE_TASKS) >= 3
    assert {"read-config", "list-dir", "finance-report"}.issubset(names)

    by_name = {task.name: task for task in SAMPLE_TASKS}
    record = {
        "task": "finance-report",
        "steps": [
            {
                "tool_calls": [
                    {"name": "finance_get_quote", "arguments": {"symbol": "AAPL"}},
                    {"name": "finance_generate_report", "arguments": {"symbol": "AAPL"}},
                ]
            }
        ],
        "final": "AAPL 当前价格约 195.0 美元，报告包含风险提示。",
    }
    assert by_name["finance-report"].check(record)


def test_day3_metrics_on_sample_records_distinguish_quality() -> None:
    from eval.metrics import (
        SAMPLE_RECORDS,
        json_valid_rate,
        step_count,
        success_rate,
        token_count,
    )
    from eval.tasks import SAMPLE_TASKS

    assert 0 < success_rate(SAMPLE_TASKS, SAMPLE_RECORDS) < 1
    assert sum(step_count(record) for record in SAMPLE_RECORDS) / len(SAMPLE_RECORDS) > 0
    assert sum(token_count(record) for record in SAMPLE_RECORDS) > 0
    assert 0 < json_valid_rate(SAMPLE_RECORDS) < 1


def test_day3_judge_parses_score_without_network(monkeypatch) -> None:  # noqa: ANN001
    import eval.judge as judge_mod

    class Backend:
        def chat(self, messages):  # noqa: ANN001
            assert messages[0]["role"] == "system"
            return {"content": "【理由】回答直接给出了 timeout。\n【分数: 5】"}

    monkeypatch.setattr(judge_mod, "DeepSeekBackend", Backend)

    result = judge_mod.judge("timeout 是多少？", "timeout = 30 秒。")

    assert result["score"] == 5
    assert "理由" in result["raw"]


def test_day3_tracer_writes_jsonl_and_replay(tmp_path, capsys) -> None:  # noqa: ANN001
    from eval.tracer import Tracer, replay

    trace_path = tmp_path / "trace.jsonl"
    tracer = Tracer(str(trace_path))
    tracer.log_step(
        0,
        [{"name": "read", "arguments": {"path": "config.json"}}],
        prompt_tokens=10,
        completion_tokens=3,
        note="read config",
    )

    line = trace_path.read_text(encoding="utf-8").strip()
    event = json.loads(line)
    assert event["step"] == 0
    assert event["tool_calls"][0]["name"] == "read"

    replay(str(trace_path))
    output = capsys.readouterr().out
    assert "step 0" in output
    assert "read" in output
    assert "轨迹共 13 token" in output


def test_day3_ablation_reports_system_prompt_delta(tmp_path, monkeypatch, capsys) -> None:  # noqa: ANN001
    from eval.ablation import GROUP_NO_SYS, GROUP_WITH_SYS, write_notes
    from eval.metrics import success_rate
    from eval.tasks import SAMPLE_TASKS

    with_sys = success_rate(SAMPLE_TASKS, GROUP_WITH_SYS)
    no_sys = success_rate(SAMPLE_TASKS, GROUP_NO_SYS)
    assert with_sys > no_sys

    notes_path = tmp_path / "ablation_notes.md"
    write_notes(notes_path)
    notes = notes_path.read_text(encoding="utf-8")
    for keyword in ["变量", "固定", "结果", "归因", "局限"]:
        assert keyword in notes
