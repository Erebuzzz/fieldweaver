from __future__ import annotations

import math

import pytest
from pydantic import ValidationError

from app.schemas import (
    AgentDecision,
    DecisionAction,
    Goal,
    ReasonCode,
    RequestedProfile,
    default_mission_spec,
)


def test_default_mission_spec_is_valid() -> None:
    spec = default_mission_spec()
    assert spec.goal is Goal.LOCATE_AND_ENCIRCLE_SOURCE
    assert spec.robot_count == 6
    assert spec.constraints.avoid_restricted_regions is True
    assert spec.search.target_source_count == 1
    assert spec.model_dump()["schema_version"] == "1.0"


def test_rejects_unknown_fields() -> None:
    payload = default_mission_spec().model_dump()
    payload["source_position"] = [1.0, 2.0]
    with pytest.raises(ValidationError):
        type(default_mission_spec()).model_validate(payload)


def test_rejects_unknown_goal() -> None:
    payload = default_mission_spec().model_dump()
    payload["goal"] = "deliver_package"
    with pytest.raises(ValidationError):
        type(default_mission_spec()).model_validate(payload)


def test_rejects_multi_source_request() -> None:
    payload = default_mission_spec().model_dump()
    payload["search"]["target_source_count"] = 2
    with pytest.raises(ValidationError):
        type(default_mission_spec()).model_validate(payload)


def test_rejects_out_of_range_robot_count() -> None:
    payload = default_mission_spec().model_dump()
    payload["robot_count"] = 12
    with pytest.raises(ValidationError):
        type(default_mission_spec()).model_validate(payload)


def test_rejects_unsafe_speed() -> None:
    payload = default_mission_spec().model_dump()
    payload["constraints"]["maximum_speed"] = 5.0
    with pytest.raises(ValidationError):
        type(default_mission_spec()).model_validate(payload)


def test_rejects_disabling_restricted_region_avoidance() -> None:
    payload = default_mission_spec().model_dump()
    payload["constraints"]["avoid_restricted_regions"] = False
    with pytest.raises(ValidationError):
        type(default_mission_spec()).model_validate(payload)


def test_rejects_nan_and_infinity() -> None:
    payload = default_mission_spec().model_dump()
    payload["formation"]["radius"] = math.inf
    with pytest.raises(ValidationError):
        type(default_mission_spec()).model_validate(payload)
    payload = default_mission_spec().model_dump()
    payload["search"]["max_duration_s"] = math.nan
    with pytest.raises(ValidationError):
        type(default_mission_spec()).model_validate(payload)


def test_rejects_infeasible_ring_separation_combination() -> None:
    payload = default_mission_spec().model_dump()
    payload["robot_count"] = 8
    payload["formation"]["radius"] = 0.8
    payload["constraints"]["minimum_robot_separation"] = 1.2
    with pytest.raises(ValidationError):
        type(default_mission_spec()).model_validate(payload)


def test_rejects_too_many_assumptions() -> None:
    payload = default_mission_spec().model_dump()
    payload["assumptions"] = [f"assumption {index}" for index in range(9)]
    with pytest.raises(ValidationError):
        type(default_mission_spec()).model_validate(payload)


def test_agent_decision_accepts_bounded_switch() -> None:
    decision = AgentDecision(
        schema_version="1.0",
        decision=DecisionAction.SWITCH_SEARCH_PATTERN,
        reason_code=ReasonCode.OBSTACLE_CHANGE,
        short_rationale="A barrier appeared ahead; request a route detour.",
        requested_profile=RequestedProfile.EXPLORATION,
    )
    assert decision.decision is DecisionAction.SWITCH_SEARCH_PATTERN


def test_agent_decision_rejects_unknown_action() -> None:
    with pytest.raises(ValidationError):
        AgentDecision(
            schema_version="1.0",
            decision="drive_forward",
            reason_code=ReasonCode.OBSTACLE_CHANGE,
            short_rationale="Not supported.",
        )


def test_agent_decision_rejects_arbitrary_parameters() -> None:
    with pytest.raises(ValidationError):
        AgentDecision.model_validate(
            {
                "schema_version": "1.0",
                "decision": "switch_search_pattern",
                "reason_code": "obstacle_change",
                "short_rationale": "Route around.",
                "controller_gain": 4.2,
            }
        )


def test_agent_decision_rejects_relaxing_profile() -> None:
    with pytest.raises(ValidationError):
        AgentDecision(
            schema_version="1.0",
            decision=DecisionAction.USE_CAUTIOUS_PROFILE,
            reason_code=ReasonCode.REPEATED_SAFETY_INTERVENTIONS,
            short_rationale="Use cautious mode.",
            requested_profile=RequestedProfile.EXPLORATION,
        )


def test_agent_decision_rejects_overlong_rationale() -> None:
    with pytest.raises(ValidationError):
        AgentDecision(
            schema_version="1.0",
            decision=DecisionAction.CONTINUE_CURRENT_PLAN,
            reason_code=ReasonCode.MISSION_PROGRESS_NORMAL,
            short_rationale="x" * 401,
        )
