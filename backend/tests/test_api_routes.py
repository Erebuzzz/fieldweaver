from __future__ import annotations

from fastapi.testclient import TestClient

from app.schemas import default_mission_spec


def _keys(value: object) -> set[str]:
    if isinstance(value, dict):
        return set(value).union(*(key for item in value.values() for key in _keys(item)))
    if isinstance(value, list):
        return set().union(*(_keys(item) for item in value))
    return set()


def test_scenarios_route_exposes_public_geometry_only(client: TestClient) -> None:
    response = client.get("/api/scenarios")

    assert response.status_code == 200
    body = response.json()
    assert {item["id"] for item in body["scenarios"]} >= {
        "open_field",
        "disturbed_corridor",
        "infeasible_enclosure",
    }
    assert all(item["source_revealed"] is False for item in body["scenarios"])
    assert "ground_truth" not in _keys(body)
    assert "source" not in _keys(body)
    assert body["seed"]["default"] == 42
    assert body["request_id"] == response.headers["x-request-id"]


def test_compile_route_returns_validated_spec_and_mock_label(client: TestClient) -> None:
    response = client.post(
        "/api/missions/compile",
        json={
            "mission_text": "Locate the signal source and avoid restricted regions.",
            "scenario_id": "open_field",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["spec"]["schema_version"] == "1.0"
    assert body["spec"]["goal"] == "locate_and_encircle_source"
    assert body["provider"]["mode"] == "mock"
    assert body["provider"]["name"] == "mock"
    assert body["provider"]["live_verified"] is False
    assert body["request_id"] == response.headers["x-request-id"]


def test_unsupported_compile_requires_clarification_before_approval(client: TestClient) -> None:
    response = client.post(
        "/api/missions/compile",
        json={
            "mission_text": "Find two sources with a ring formation.",
            "mode": "mock",
        },
    )

    assert response.status_code == 200
    spec = response.json()["spec"]
    assert spec["unsupported_requirements"] == ["multiple sources"]
    assert spec["clarifying_questions"]


def test_compile_live_without_key_returns_error_envelope(client: TestClient) -> None:
    response = client.post(
        "/api/missions/compile",
        json={
            "mission_text": "Locate one source with a ring formation.",
            "mode": "live",
        },
    )

    assert response.status_code == 503
    error = response.json()["error"]
    assert error["code"] == "provider_not_configured"
    assert error["request_id"] == response.headers["x-request-id"]


def test_routes_reject_unknown_scenario_and_request_fields(client: TestClient) -> None:
    unknown_scenario = client.post(
        "/api/missions/compile",
        json={"mission_text": "Locate a source.", "scenario_id": "not-a-scenario"},
    )
    invalid_request = client.post(
        "/api/missions/compile",
        json={"mission_text": "Locate a source.", "source": {"x": 4, "y": 5}},
    )

    assert unknown_scenario.status_code == 404
    assert unknown_scenario.json()["error"]["code"] == "scenario_not_found"
    assert invalid_request.status_code == 422
    assert invalid_request.json()["error"]["code"] == "invalid_request"


def test_latest_evaluation_is_explicitly_empty_before_a_run(client: TestClient) -> None:
    response = client.get("/api/evaluations/latest")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "evaluation_not_found"


def test_run_route_returns_actual_result_and_latest_evaluation(client: TestClient) -> None:
    response = client.post(
        "/api/simulations/run",
        json={
            "mission": default_mission_spec().model_dump(mode="json"),
            "scenario_id": "open_field",
            "seed": 42,
            "agent_mode": "off",
        },
    )

    assert response.status_code == 200
    result = response.json()
    assert result["seed"] == 42
    assert result["scenario"]["source_revealed"] is False
    assert result["frames"]
    assert result["evaluation"]["metrics"]["controller_iteration_count"] > 0
    assert result["evaluation"]["ground_truth"]["revealed"] == "after_run_only"
    assert result["request_id"] == response.headers["x-request-id"]

    latest = client.get("/api/evaluations/latest")
    assert latest.status_code == 200
    assert latest.json()["run_id"] == result["run_id"]
    assert latest.json()["evaluation"] == result["evaluation"]
    assert latest.json()["request_id"] == latest.headers["x-request-id"]


def test_live_run_without_key_returns_error_envelope(client: TestClient) -> None:
    response = client.post(
        "/api/simulations/run",
        json={
            "mission": default_mission_spec().model_dump(mode="json"),
            "scenario_id": "open_field",
            "agent_mode": "live",
        },
    )

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "provider_not_configured"
