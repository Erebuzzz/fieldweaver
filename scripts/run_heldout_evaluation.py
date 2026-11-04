from __future__ import annotations

import asyncio
import json
import sys
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.schemas import default_mission_spec  # noqa: E402
from app.services.runner import run_scenario  # noqa: E402
from app.simulation.scenario import get_scenario  # noqa: E402

SCENARIOS = ("open_field", "noisy_open", "restricted_corridor", "disturbed_corridor")
SEEDS = tuple(range(52, 62))


async def main() -> None:
    runs: list[dict[str, Any]] = []
    for scenario_id in SCENARIOS:
        for seed in SEEDS:
            outcome = await run_scenario(
                scenario=get_scenario(scenario_id),
                mission=default_mission_spec(),
                seed=seed,
                controller="quadratic",
                agent_mode="mock",
            )
            metrics = outcome.evaluation.metrics
            runs.append(
                {
                    "scenario_id": scenario_id,
                    "seed": seed,
                    "success": outcome.evaluation.success,
                    "termination_reason": metrics["termination_reason"],
                    "robot_collision_count": metrics["robot_collision_count"],
                    "minimum_robot_separation_m": metrics["minimum_robot_separation_m"],
                }
            )
        scenario_runs = [row for row in runs if row["scenario_id"] == scenario_id]
        reasons = Counter(row["termination_reason"] for row in scenario_runs)
        print(
            f"{scenario_id}: {sum(row['success'] for row in scenario_runs)}/"
            f"{len(scenario_runs)} succeeded; terminations={dict(reasons)}",
            flush=True,
        )

    report = {
        "generated_at_utc": datetime.now(UTC).isoformat(timespec="seconds"),
        "controller": "quadratic",
        "agent_mode": "mock",
        "live_inference_used": False,
        "seeds": list(SEEDS),
        "scenarios": list(SCENARIOS),
        "runs": runs,
    }
    output = ROOT / "artifacts" / "heldout_evaluation_report.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {output.relative_to(ROOT)}")


if __name__ == "__main__":
    asyncio.run(main())
