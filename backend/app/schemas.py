"""Strict application contracts for missions and bounded agent decisions.

These schemas are owned by FieldWeaver, not by the model provider. Every model
response is validated against them before it can influence simulation behaviour.
"""

from __future__ import annotations

import math
from enum import StrEnum
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

from app import limits

ShortText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=300)]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)


class Goal(StrEnum):
    LOCATE_AND_ENCIRCLE_SOURCE = "locate_and_encircle_source"


class FormationType(StrEnum):
    RING = "ring"


class SearchStrategy(StrEnum):
    SCALAR_FIELD_SOURCE_SEEKING = "scalar_field_source_seeking"


class FormationSpec(StrictModel):
    type: FormationType = FormationType.RING
    radius: float = Field(
        ge=limits.MIN_RING_RADIUS_M,
        le=limits.MAX_RING_RADIUS_M,
        description="Desired ring radius around the estimated source, in metres.",
    )


class SearchSpec(StrictModel):
    strategy: SearchStrategy = SearchStrategy.SCALAR_FIELD_SOURCE_SEEKING
    max_duration_s: float = Field(
        ge=limits.MIN_DURATION_S,
        le=limits.MAX_DURATION_S,
        description="Hard simulation duration limit, in seconds.",
    )
    target_source_count: Literal[1] = 1


class ConstraintsSpec(StrictModel):
    minimum_robot_separation: float = Field(
        ge=limits.MIN_SEPARATION_M, le=limits.MAX_SEPARATION_M
    )
    minimum_obstacle_clearance: float = Field(
        ge=limits.MIN_CLEARANCE_M, le=limits.MAX_CLEARANCE_M
    )
    maximum_speed: float = Field(ge=limits.MIN_SPEED_MPS, le=limits.MAX_SPEED_MPS)
    avoid_restricted_regions: Literal[True] = True


class TerminationSpec(StrictModel):
    localization_tolerance: float = Field(
        ge=limits.MIN_LOCALIZATION_TOLERANCE_M,
        le=limits.MAX_LOCALIZATION_TOLERANCE_M,
    )
    formation_tolerance: float = Field(
        ge=limits.MIN_FORMATION_TOLERANCE_M,
        le=limits.MAX_FORMATION_TOLERANCE_M,
    )


class MissionSpec(StrictModel):
    """Versioned mission contract. Units are metres and seconds."""

    schema_version: Literal["1.0"]
    goal: Goal
    robot_count: int = Field(ge=limits.MIN_ROBOTS, le=limits.MAX_ROBOTS)
    formation: FormationSpec
    search: SearchSpec
    constraints: ConstraintsSpec
    termination: TerminationSpec
    assumptions: list[ShortText] = Field(default_factory=list, max_length=8)
    clarifying_questions: list[ShortText] = Field(default_factory=list, max_length=5)
    unsupported_requirements: list[ShortText] = Field(default_factory=list, max_length=8)

    @model_validator(mode="after")
    def check_feasible_ring(self) -> MissionSpec:
        count = self.robot_count
        radius = self.formation.radius
        separation = self.constraints.minimum_robot_separation
        slot_arc = 2.0 * radius * math.sin(math.pi / count)
        if separation > slot_arc * 0.95:
            raise ValueError(
                "minimum_robot_separation is incompatible with the requested ring radius "
                f"and robot count: slot arc is {slot_arc:.3f} m, separation is {separation:.3f} m"
            )
        return self


class DecisionAction(StrEnum):
    CONTINUE_CURRENT_PLAN = "continue_current_plan"
    SWITCH_SEARCH_PATTERN = "switch_search_pattern"
    USE_CAUTIOUS_PROFILE = "use_cautious_profile"
    REQUEST_USER_CLARIFICATION = "request_user_clarification"
    ABORT_MISSION = "abort_mission"


class ReasonCode(StrEnum):
    BLOCKED_PROGRESS = "blocked_progress"
    OBSTACLE_CHANGE = "obstacle_change"
    REPEATED_SAFETY_INTERVENTIONS = "repeated_safety_interventions"
    ROUTE_INFEASIBLE = "route_infeasible"
    MISSION_PROGRESS_NORMAL = "mission_progress_normal"


class RequestedProfile(StrEnum):
    CAUTIOUS = "cautious"
    EXPLORATION = "exploration"


class AgentDecision(StrictModel):
    """Bounded high-level decision. No code, gains, or actuator commands are allowed."""

    schema_version: Literal["1.0"]
    decision: DecisionAction
    reason_code: ReasonCode
    short_rationale: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=1, max_length=400)
    ]
    requested_profile: RequestedProfile | None = None

    @model_validator(mode="after")
    def check_profile(self) -> AgentDecision:
        if self.decision is DecisionAction.USE_CAUTIOUS_PROFILE:
            if self.requested_profile not in (None, RequestedProfile.CAUTIOUS):
                raise ValueError("use_cautious_profile may only request the cautious profile")
        elif self.decision is DecisionAction.SWITCH_SEARCH_PATTERN:
            if self.requested_profile not in (None, RequestedProfile.EXPLORATION):
                raise ValueError("switch_search_pattern may only request the exploration profile")
        elif self.requested_profile is not None:
            raise ValueError("requested_profile is only valid for profile-changing decisions")
        return self


def default_mission_spec() -> MissionSpec:
    """Safe default used by the offline compiler and the UI example."""

    return MissionSpec(
        schema_version="1.0",
        goal=Goal.LOCATE_AND_ENCIRCLE_SOURCE,
        robot_count=limits.DEFAULT_ROBOTS,
        formation=FormationSpec(radius=limits.DEFAULT_RING_RADIUS_M),
        search=SearchSpec(max_duration_s=limits.DEFAULT_DURATION_S),
        constraints=ConstraintsSpec(
            minimum_robot_separation=limits.DEFAULT_SEPARATION_M,
            minimum_obstacle_clearance=limits.DEFAULT_CLEARANCE_M,
            maximum_speed=limits.DEFAULT_SPEED_MPS,
            avoid_restricted_regions=True,
        ),
        termination=TerminationSpec(
            localization_tolerance=limits.DEFAULT_LOCALIZATION_TOLERANCE_M,
            formation_tolerance=limits.DEFAULT_FORMATION_TOLERANCE_M,
        ),
    )
