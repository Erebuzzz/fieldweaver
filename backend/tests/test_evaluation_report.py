from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
REPORT_PATH = ROOT / "frontend" / "public" / "evaluation-report.json"


def _keys(value: Any) -> set[str]:
    if isinstance(value, dict):
        return set(value).union(*(_keys(item) for item in value.values()))
    if isinstance(value, list):
        return set().union(*(_keys(item) for item in value))
    return set()


def test_public_evaluation_snapshot_keeps_paired_runs_and_aggregates_in_sync() -> None:
    report = json.loads(REPORT_PATH.read_text(encoding="utf-8"))
    runs = report["runs"]

    assert len(runs) == 140
    assert report["configuration"]["runs_per_controller"] == 70
    assert report["provider"]["live_inference_used"] is False
    assert report["agent_summary"]["live_inference_latency_ms"] is None

    controller_pairs: dict[tuple[str, int], set[str]] = defaultdict(set)
    for run in runs:
        controller_pairs[(run["scenario_id"], run["seed"])].add(run["controller"])
    assert len(controller_pairs) == 70
    assert all(
        controllers == {"quadratic", "baseline"}
        for controllers in controller_pairs.values()
    )

    for controller in ("quadratic", "baseline"):
        controller_runs = [run for run in runs if run["controller"] == controller]
        summary = report["controller_summary"][controller]
        assert summary["sample_count"] == len(controller_runs)
        assert summary["success_count"] == sum(run["success"] for run in controller_runs)
        assert summary["termination_reasons"] == dict(
            Counter(run["termination_reason"] for run in controller_runs)
        )

    disturbance_runs = [
        run
        for run in runs
        if run["scenario_id"] == "disturbed_corridor" and run["controller"] == "quadratic"
    ]
    recoveries = sum(run["success"] and run["replans"] > 0 for run in disturbance_runs)
    assert report["agent_summary"]["disturbance_trials"] == len(disturbance_runs)
    assert report["agent_summary"]["disturbance_recoveries"] == recoveries
    assert "source" not in _keys(report)
    assert "ground_truth" not in _keys(report)
