from __future__ import annotations

import os

import httpx

API_BASE = os.getenv("FIELDWEAVER_API_BASE_URL", "http://127.0.0.1:8000").rstrip("/")


def main() -> None:
    with httpx.Client(base_url=API_BASE, timeout=30.0) as client:
        health = client.get("/api/health")
        health.raise_for_status()
        assert health.json()["status"] == "ok"

        scenarios = client.get("/api/scenarios")
        scenarios.raise_for_status()
        assert any(item["id"] == "open_field" for item in scenarios.json()["scenarios"])

        compilation = client.post(
            "/api/missions/compile",
            json={
                "mission_text": (
                    "Search for the signal source, maintain a ring formation, "
                    "and avoid restricted regions."
                ),
                "scenario_id": "open_field",
                "mode": "mock",
            },
        )
        compilation.raise_for_status()
        compiled = compilation.json()
        assert compiled["provider"]["mode"] == "mock"

        run = client.post(
            "/api/simulations/run",
            json={
                "mission": compiled["spec"],
                "scenario_id": "open_field",
                "seed": scenarios.json()["seed"]["default"],
                "controller": "quadratic",
                "agent_mode": "mock",
            },
        )
        run.raise_for_status()
        result = run.json()
        assert result["frames"]
        assert result["scenario"]["source_revealed"] is False

        latest = client.get("/api/evaluations/latest")
        latest.raise_for_status()
        assert latest.json()["run_id"] == result["run_id"]

    metrics = result["evaluation"]["metrics"]
    print(
        "Smoke check passed: health, public scenarios, mock compile, seeded run, "
        f"and latest evaluation. success={result['evaluation']['success']} "
        f"duration_s={metrics['simulation_duration_s']:.1f}"
    )


if __name__ == "__main__":
    main()
