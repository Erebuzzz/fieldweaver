from __future__ import annotations

import json
from dataclasses import asdict

from app.evaluation.evaluator import evaluate_run
from app.schemas import default_mission_spec
from app.simulation.engine import SimulationSession
from app.simulation.geometry import Vec2
from app.simulation.scenario import get_scenario


def _run(scenario_id: str, seed: int = 42):  # type: ignore[no-untyped-def]
    scenario = get_scenario(scenario_id)
    mission = default_mission_spec()
    session = SimulationSession(mission, scenario, seed=seed).run_to_completion()
    result = evaluate_run(
        scenario=scenario,
        mission=mission,
        frames=session.frames,
        interventions=session.interventions,
        world_events=session.world_events,
        termination_reason=session.termination_reason or "unknown",
        wall_clock_ms=1.0,
        seed=seed,
        controller_name=session.controller.name,
    )
    return scenario, mission, session, result


def test_open_field_converges_and_passes_all_checks() -> None:
    _, _, session, result = _run("open_field")
    assert session.termination_reason == "nominal_convergence"
    assert result.success
    assert result.metrics["localization_error_m"] <= 0.05
    assert result.metrics["formation_error_m"] <= 0.25
    assert result.metrics["robot_collision_count"] == 0
    assert all(check["passed"] for check in result.checks)


def test_noisy_open_converges_with_seeded_noise() -> None:
    _, _, session, result = _run("noisy_open")
    assert session.termination_reason == "nominal_convergence"
    assert result.success
    assert result.metrics["localization_error_m"] <= 0.1


def test_same_seed_reproduces_identical_trajectory() -> None:
    _, _, first, _ = _run("open_field", seed=7)
    _, _, second, _ = _run("open_field", seed=7)
    assert [frame.to_public() for frame in first.frames] == [
        frame.to_public() for frame in second.frames
    ]
    assert first.termination_reason == second.termination_reason


def test_baseline_controller_selects_weighted_centroid_estimator() -> None:
    scenario = get_scenario("open_field")
    session = SimulationSession(
        default_mission_spec(), scenario, seed=42, controller_kind="baseline"
    )

    assert session.controller.estimator_kind == "weighted_centroid"


def test_different_seed_changes_initial_conditions() -> None:
    _, _, first, _ = _run("open_field", seed=7)
    _, _, second, _ = _run("open_field", seed=8)
    first_positions = [(robot.x, robot.y) for robot in first.frames[0].robots]
    second_positions = [(robot.x, robot.y) for robot in second.frames[0].robots]
    assert first_positions != second_positions


def test_infeasible_enclosure_fails_without_claiming_success() -> None:
    _, _, session, result = _run("infeasible_enclosure")
    assert not result.success
    assert session.termination_reason == "timeout"
    assert result.failure_reason == "timeout_before_convergence"


def test_dynamic_barrier_records_public_event_without_safety_abort() -> None:
    scenario, _, session, _ = _run("disturbed_corridor")
    assert session.termination_reason != "safety_abort"
    assert len(session.world_events) == 1
    event = session.world_events[0]
    assert event.event_type == "obstacle_change"
    assert event.time_s == 6.0
    wall = scenario.regions[0]
    assert wall.active_from_s == 6.0
    for frame in session.frames:
        for robot in frame.robots:
            if frame.time_s >= 6.0:
                assert wall.clearance(Vec2(robot.x, robot.y)) >= 0.2 - 1e-6


def test_observations_expose_no_ground_truth_coordinates() -> None:
    _, _, session, _ = _run("open_field")
    observation = session.current_observation
    payload = asdict(observation)
    serialized = json.dumps(payload)
    assert "source" not in serialized
    robot_fields = set(asdict(observation.robots[0]))
    assert robot_fields == {"robot_id", "step", "time_s", "x", "y", "heading", "measurement"}

    public_frame = json.dumps(session.frames[-1].to_public())
    assert "source" not in public_frame
    assert "ground_truth" not in public_frame
