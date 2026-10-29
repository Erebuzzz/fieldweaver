from __future__ import annotations

import math

import pytest

from app.evaluation.evaluator import evaluate_run
from app.schemas import default_mission_spec
from app.simulation.scenario import OPEN_FIELD
from app.simulation.types import Frame, FrameRobot, SourceEstimate


def _frame(
    step: int,
    time_s: float,
    positions: list[tuple[float, float]],
    estimate: SourceEstimate,
) -> Frame:
    return Frame(
        step=step,
        time_s=time_s,
        robots=tuple(
            FrameRobot(
                robot_id=index,
                x=x,
                y=y,
                heading=0.0,
                measurement=0.0,
            )
            for index, (x, y) in enumerate(positions)
        ),
        estimate=estimate,
        formation_error_estimate=0.0,
        obstacle_version=0,
    )


def _ring(center: tuple[float, float], radius: float, count: int = 6) -> list[tuple[float, float]]:
    return [
        (
            center[0] + radius * math.cos(2.0 * math.pi * index / count),
            center[1] + radius * math.sin(2.0 * math.pi * index / count),
        )
        for index in range(count)
    ]


def _evaluate(
    positions: list[tuple[float, float]],
    estimate_x: float,
    estimate_y: float,
    termination_reason: str = "nominal_convergence",
):  # type: ignore[no-untyped-def]
    mission = default_mission_spec()
    estimate = SourceEstimate(
        x=estimate_x,
        y=estimate_y,
        confidence=1.0,
        samples=100,
        valid=True,
    )
    frames = [
        _frame(0, 0.0, positions, estimate),
        _frame(1, 0.1, positions, estimate),
    ]
    return evaluate_run(
        scenario=OPEN_FIELD,
        mission=mission,
        frames=frames,
        interventions=[],
        world_events=[],
        termination_reason=termination_reason,
        wall_clock_ms=12.5,
        seed=42,
        controller_name="test",
    )


def test_evaluator_computes_success_from_perfect_trajectory() -> None:
    result = _evaluate(_ring((7.0, 5.0), 1.5), 7.0, 5.0)
    assert result.success
    assert result.failure_reason is None
    assert result.metrics["localization_error_m"] == 0.0
    assert result.metrics["formation_error_m"] == pytest.approx(0.0, abs=1e-9)
    assert result.metrics["minimum_robot_separation_m"] > 0.25
    assert result.metrics["wall_clock_ms"] == 12.5


def test_evaluator_reports_localization_tolerance_failure() -> None:
    result = _evaluate(_ring((7.0, 5.0), 1.5), 7.5, 5.0)
    assert not result.success
    assert result.failure_reason == "localization_tolerance_not_met"
    assert result.metrics["localization_error_m"] == 0.5


def test_evaluator_reports_formation_tolerance_failure() -> None:
    result = _evaluate(_ring((7.0, 5.0), 2.0), 7.0, 5.0)
    assert not result.success
    assert result.failure_reason == "formation_tolerance_not_met"
    assert result.metrics["formation_error_m"] == 0.5


def test_evaluator_reports_timeout_before_convergence() -> None:
    result = _evaluate(_ring((7.0, 5.0), 1.5), 7.0, 5.0, termination_reason="timeout")
    assert not result.success
    assert result.failure_reason == "timeout_before_convergence"


@pytest.mark.parametrize("reason", ["route_infeasible", "invalid_decision"])
def test_evaluator_preserves_specific_agent_termination_reason(reason: str) -> None:
    result = _evaluate(
        _ring((7.0, 5.0), 1.5), 7.0, 5.0, termination_reason=reason
    )

    assert not result.success
    assert result.failure_reason == reason


def test_evaluator_detects_seeded_separation_violation() -> None:
    positions = _ring((7.0, 5.0), 1.5)
    positions[1] = (positions[0][0] + 0.05, positions[0][1])
    result = _evaluate(positions, 7.0, 5.0)
    assert not result.success
    assert result.failure_reason == "robot_separation_violation"
    assert result.metrics["robot_collision_count"] > 0


def test_evaluator_detects_unsafe_termination() -> None:
    result = _evaluate(
        _ring((7.0, 5.0), 1.5), 7.0, 5.0, termination_reason="safety_abort"
    )
    assert not result.success
    assert result.failure_reason == "safety_abort"


def test_ground_truth_is_flagged_as_post_run_only() -> None:
    result = _evaluate(_ring((7.0, 5.0), 1.5), 7.0, 5.0)
    assert result.ground_truth["revealed"] == "after_run_only"
    assert result.ground_truth["x"] == 7.0
    assert result.ground_truth["y"] == 5.0
