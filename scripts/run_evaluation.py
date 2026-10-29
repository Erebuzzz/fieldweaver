from __future__ import annotations

import asyncio
import json
import statistics
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app import limits  # noqa: E402
from app.schemas import SearchSpec, default_mission_spec  # noqa: E402
from app.services.runner import run_scenario  # noqa: E402
from app.simulation.scenario import get_scenario  # noqa: E402

SEEDS = (42, 43, 44)
CASES = (
    ("open_field", None),
    ("noisy_open", None),
    ("restricted_corridor", None),
    ("disturbed_corridor", None),
    ("near_boundary", None),
    ("infeasible_enclosure", None),
    ("far_source", 20.0),
)
METRICS = (
    "localization_error_m",
    "formation_error_m",
    "minimum_robot_separation_m",
    "minimum_obstacle_clearance_m",
    "path_length_total_m",
    "simulation_duration_s",
    "wall_clock_ms",
    "safety_intervention_count",
    "robot_collision_count",
)


def _aggregate(rows: list[dict[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {"sample_count": len(rows)}
    result["success_count"] = sum(row["success"] for row in rows)
    result["success_rate"] = result["success_count"] / len(rows) if rows else 0.0
    result["termination_reasons"] = {
        reason: sum(row["termination_reason"] == reason for row in rows)
        for reason in sorted({row["termination_reason"] for row in rows})
    }
    summary: dict[str, dict[str, float | int]] = {}
    for metric in METRICS:
        values = [row["metrics"][metric] for row in rows]
        numeric = [float(value) for value in values if isinstance(value, (int, float))]
        if numeric:
            summary[metric] = {
                "sample_count": len(numeric),
                "mean": statistics.mean(numeric),
                "median": statistics.median(numeric),
                "sample_stddev": statistics.stdev(numeric) if len(numeric) > 1 else 0.0,
            }
    result["metrics"] = summary
    return result


async def build_report() -> dict[str, Any]:
    runs: list[dict[str, Any]] = []
    for scenario_id, duration_override in CASES:
        for seed in SEEDS:
            mission = default_mission_spec()
            if duration_override is not None:
                mission = mission.model_copy(
                    update={
                        "search": SearchSpec(
                            max_duration_s=duration_override,
                        )
                    }
                )
            scenario = get_scenario(scenario_id)
            for controller, agent_mode in (("quadratic", "mock"), ("baseline", "off")):
                outcome = await run_scenario(
                    scenario=scenario,
                    mission=mission,
                    seed=seed,
                    controller=controller,
                    agent_mode=agent_mode,
                )
                metrics = {
                    name: outcome.evaluation.metrics[name]
                    for name in METRICS
                }
                runs.append(
                    {
                        "scenario_id": scenario_id,
                        "seed": seed,
                        "controller": controller,
                        "agent_mode": agent_mode,
                        "mission_duration_limit_s": mission.search.max_duration_s,
                        "success": outcome.evaluation.success,
                        "failure_reason": outcome.evaluation.failure_reason,
                        "termination_reason": outcome.evaluation.metrics["termination_reason"],
                        "metrics": metrics,
                        "decision_calls": outcome.agent["decision_calls"],
                        "replans": outcome.agent["replans"],
                        "live_calls": outcome.agent["live_calls"],
                        "live_verified": outcome.agent["live_verified"],
                    }
                )

    grouped = {
        controller: _aggregate([row for row in runs if row["controller"] == controller])
        for controller in ("quadratic", "baseline")
    }
    disturbance_runs = [
        row
        for row in runs
        if row["scenario_id"] == "disturbed_corridor"
        and row["controller"] == "quadratic"
    ]
    recovered_runs = [
        row
        for row in disturbance_runs
        if row["success"] and row["replans"] > 0
    ]
    quadratic_agent_runs = [
        row for row in runs if row["controller"] == "quadratic"
    ]
    return {
        "report_version": "1.0",
        "generated_at_utc": datetime.now(UTC).isoformat(timespec="seconds"),
        "application_version": limits.APP_VERSION,
        "provider": {
            "name": "mock",
            "model": "deterministic-rule-mock",
            "live_inference_used": False,
        },
        "configuration": {
            "seeds": list(SEEDS),
            "dt_s": limits.DT_S,
            "scenario_count": len(CASES),
            "controllers_per_scenario": 2,
            "runs_per_controller": len(CASES) * len(SEEDS),
            "noise": "scenario-defined; noisy_open uses seeded Gaussian noise",
            "baseline_policy": "weighted-centroid estimator, shared safety, agent off",
            "proposed_policy": "quadratic estimator, shared safety, deterministic mock agent",
            "timeout_case": "far_source uses a 20 second mission duration cap",
        },
        "controller_summary": grouped,
        "agent_summary": {
            "agent_runs": len(quadratic_agent_runs),
            "disturbance_scenario": "disturbed_corridor",
            "disturbance_trials": len(disturbance_runs),
            "disturbance_recoveries": len(recovered_runs),
            "disturbance_recovery_rate": (
                len(recovered_runs) / len(disturbance_runs) if disturbance_runs else 0.0
            ),
            "mean_decision_calls_per_run": statistics.mean(
                row["decision_calls"] for row in quadratic_agent_runs
            ),
            "mean_replans_per_run": statistics.mean(
                row["replans"] for row in quadratic_agent_runs
            ),
            "live_inference_latency_ms": None,
            "live_inference_latency_sample_count": 0,
            "invalid_decision_rejection": "covered by backend unit tests; no live inference trial",
        },
        "runs": runs,
        "limitations": [
            "Three fixed seeds per scenario provide limited spread evidence, not broad "
            "robustness evidence.",
            "All agent decisions used the deterministic offline mock; Baseten was not called.",
            "Live inference latency was not measured because this evaluation "
            "used no live requests.",
            "The baseline and proposed controller share the same formation objective "
            "and safety filter.",
        ],
    }


async def main() -> None:
    report = await build_report()
    output = ROOT / "artifacts" / "evaluation_report.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {output.relative_to(ROOT)}")
    for name, summary in report["controller_summary"].items():
        print(
            f"{name}: {summary['success_count']}/{summary['sample_count']} succeeded; "
            f"terminations={summary['termination_reasons']}"
        )
    agent = report["agent_summary"]
    print(
        "disturbed_corridor recovery: "
        f"{agent['disturbance_recoveries']}/{agent['disturbance_trials']}"
    )


if __name__ == "__main__":
    asyncio.run(main())
