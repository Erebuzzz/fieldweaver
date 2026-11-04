from __future__ import annotations

import asyncio
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
from app.schemas import default_mission_spec  # noqa: E402
from app.services.runner import run_scenario  # noqa: E402
from app.simulation.scenario import get_scenario  # noqa: E402


async def main() -> None:
    scenarios = (
        "open_field",
        "noisy_open",
        "restricted_corridor",
        "disturbed_corridor",
    )
    rows = []
    for scenario_id in scenarios:
        for seed in range(42, 52):
            for controller in ("quadratic", "baseline"):
                outcome = await run_scenario(
                    get_scenario(scenario_id),
                    default_mission_spec(),
                    seed,
                    controller=controller,
                    agent_mode="off",
                )
                rows.append(
                    {
                        "scenario": scenario_id,
                        "seed": seed,
                        "controller": controller,
                        "success": outcome.evaluation.success,
                        "termination": outcome.evaluation.metrics["termination_reason"],
                        "collisions": outcome.evaluation.metrics[
                            "robot_collision_count"
                        ],
                    }
                )
    for controller in ("quadratic", "baseline"):
        subset = [row for row in rows if row["controller"] == controller]
        print(
            controller,
            sum(row["success"] for row in subset),
            "/",
            len(subset),
            "terminations",
            dict(Counter(row["termination"] for row in subset)),
            "collisions",
            sum(row["collisions"] for row in subset),
        )
    path = ROOT / "artifacts" / "agent_off_ablation.json"
    path.parent.mkdir(exist_ok=True)
    path.write_text(json.dumps({"agent_mode": "off", "runs": rows}, indent=2) + "\n")


if __name__ == "__main__":
    asyncio.run(main())
