from __future__ import annotations

import math

import pytest
from pydantic import ValidationError

from app import limits
from app.safety.validator import SafetyFilter, validate_state, validate_transition
from app.schemas import default_mission_spec
from app.simulation.dynamics import integrate_state
from app.simulation.geometry import RegionKind, Vec2
from app.simulation.scenario import (
    INFEASIBLE_ENCLOSURE,
    OPEN_FIELD,
    RESTRICTED_CORRIDOR,
    get_scenario,
)
from app.simulation.types import RobotCommand, RobotState

MISSION = default_mission_spec()


def _states(count: int) -> list[RobotState]:
    return [
        RobotState(robot_id=index, x=2.0 + index * 1.5, y=2.0, heading=0.0)
        for index in range(count)
    ]


def _mission_with_separation(separation: float):  # type: ignore[no-untyped-def]
    payload = default_mission_spec().model_dump()
    payload["constraints"]["minimum_robot_separation"] = separation
    return type(default_mission_spec()).model_validate(payload)


def test_validator_detects_robot_separation_violation() -> None:
    states = [
        RobotState(robot_id=0, x=5.0, y=5.0),
        RobotState(robot_id=1, x=5.1, y=5.0),
        RobotState(robot_id=2, x=8.0, y=8.0),
    ]
    issues = validate_state(states, MISSION, 10.0, 10.0, (), 0.0)
    assert any(issue.kind == "robot_separation" for issue in issues)


def test_validator_detects_obstacle_and_restricted_clearance() -> None:
    region = RESTRICTED_CORRIDOR.regions[0]
    states = [
        RobotState(robot_id=0, x=4.9, y=3.0),
        RobotState(robot_id=1, x=8.0, y=8.0),
        RobotState(robot_id=2, x=8.5, y=8.0),
    ]
    issues = validate_state(states, MISSION, 10.0, 10.0, (region,), 0.0)
    assert any(issue.kind == "obstacle_clearance" for issue in issues)


def test_validator_detects_boundary_violation() -> None:
    states = [
        RobotState(robot_id=0, x=0.05, y=5.0),
        RobotState(robot_id=1, x=8.0, y=8.0),
        RobotState(robot_id=2, x=8.5, y=8.0),
    ]
    issues = validate_state(states, MISSION, 10.0, 10.0, (), 0.0)
    assert any(issue.kind == "arena_boundary" for issue in issues)


def test_validator_detects_speed_limit_violation() -> None:
    previous = [
        RobotState(robot_id=0, x=5.0, y=5.0),
        RobotState(robot_id=1, x=8.0, y=8.0),
        RobotState(robot_id=2, x=8.5, y=8.0),
    ]
    current = [
        RobotState(robot_id=0, x=6.0, y=5.0),
        RobotState(robot_id=1, x=8.0, y=8.0),
        RobotState(robot_id=2, x=8.5, y=8.0),
    ]
    issues = validate_transition(previous, current, MISSION, 10.0, 10.0, (), 0.1, 0.1)
    assert any(issue.kind == "speed_limit" for issue in issues)


def test_validator_detects_non_finite_state() -> None:
    bogus = RobotState(robot_id=0, x=5.0, y=5.0)
    object.__setattr__(bogus, "x", math.nan)
    states = [bogus, RobotState(robot_id=1, x=8.0, y=8.0)]
    issues = validate_state(states, MISSION, 10.0, 10.0, (), 0.0)
    assert any(issue.kind == "non_finite_state" for issue in issues)


def test_validator_ignores_inactive_regions() -> None:
    region = next(
        item for item in get_scenario("disturbed_corridor").regions if item.active_from_s > 0
    )
    states = [
        RobotState(robot_id=0, x=5.8, y=3.0),
        RobotState(robot_id=1, x=8.0, y=8.0),
        RobotState(robot_id=2, x=8.5, y=8.0),
    ]
    assert validate_state(states, MISSION, 10.0, 10.0, (region,), 5.0) == []
    assert validate_state(states, MISSION, 10.0, 10.0, (region,), 6.0)


def test_filter_scales_only_offending_robots() -> None:
    states = (
        RobotState(robot_id=0, x=5.0, y=5.0),
        RobotState(robot_id=1, x=5.0, y=5.4),
        RobotState(robot_id=2, x=8.0, y=8.0),
        RobotState(robot_id=3, x=8.8, y=8.0),
        RobotState(robot_id=4, x=2.0, y=2.0),
        RobotState(robot_id=5, x=2.8, y=2.0),
    )
    commands = (
        RobotCommand(0.0, 0.6),
        RobotCommand(0.0, -0.6),
        RobotCommand(0.5, 0.0),
        RobotCommand(0.0, 0.0),
        RobotCommand(0.0, 0.0),
        RobotCommand(0.0, 0.0),
    )
    result = SafetyFilter().apply(
        states=states,
        commands=commands,
        mission=MISSION,
        width=10.0,
        height=10.0,
        regions=(),
        time_s=0.0,
        step=0,
        dt=limits.DT_S,
    )
    assert result.commands[2].speed() == pytest.approx(0.5)
    assert result.commands[0].speed() < 0.6
    assert result.commands[1].speed() < 0.6


def test_filter_holds_when_current_state_already_unsafe() -> None:
    states = (
        RobotState(robot_id=0, x=5.0, y=5.0),
        RobotState(robot_id=1, x=5.05, y=5.0),
        RobotState(robot_id=2, x=8.0, y=8.0),
    )
    commands = tuple(RobotCommand(0.5, 0.5) for _ in states)
    result = SafetyFilter().apply(
        states=states,
        commands=commands,
        mission=MISSION,
        width=10.0,
        height=10.0,
        regions=(),
        time_s=0.0,
        step=0,
        dt=limits.DT_S,
    )
    assert all(command.speed() == 0.0 for command in result.commands)
    assert result.interventions[0].kind == "unsafe_current_state"


def test_integration_advances_state_without_exceeding_speed() -> None:
    state = RobotState(robot_id=0, x=5.0, y=5.0)
    command = RobotCommand(0.3, 0.4)
    next_state = integrate_state(state, command, 0.1)
    assert next_state.x == pytest.approx(5.03)
    assert next_state.y == pytest.approx(5.04)
    assert math.hypot(next_state.x - state.x, next_state.y - state.y) / 0.1 == pytest.approx(0.5)


def test_mission_rejects_unsafe_filter_scope() -> None:
    assert MISSION.constraints.minimum_robot_separation >= limits.MIN_SEPARATION_M
    assert MISSION.constraints.minimum_obstacle_clearance >= limits.MIN_CLEARANCE_M
    with pytest.raises(ValidationError):
        _mission_with_separation(0.01)


def test_open_field_scenario_starts_without_safety_issues() -> None:
    from app.simulation.engine import SimulationSession

    session = SimulationSession(MISSION, OPEN_FIELD, seed=3)
    assert session.states
    assert (
        validate_state(
            session.states,
            MISSION,
            OPEN_FIELD.width,
            OPEN_FIELD.height,
            (),
            0.0,
        )
        == []
    )


def test_region_kind_values_are_stable() -> None:
    assert RegionKind.OBSTACLE.value == "obstacle"
    assert Vec2(0.0, 0.0).distance_to(Vec2(3.0, 4.0)) == 5.0
    assert INFEASIBLE_ENCLOSURE.regions
