"""Deterministic simulation session.

The model provider is not imported here. A step performs only local math:
sample scalar measurements, ask the controller for a command, pass it through
the independent safety filter, integrate, and record the resulting frame.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass

from app import limits
from app.safety.validator import (
    SafetyFilter,
    ValidationIssue,
    validate_state,
    validate_transition,
)
from app.schemas import MissionSpec
from app.simulation.controller import FormationController
from app.simulation.dynamics import integrate_state
from app.simulation.geometry import Region, Vec2
from app.simulation.scenario import Scenario
from app.simulation.types import (
    Frame,
    FrameRobot,
    RobotObservation,
    RobotState,
    SafetyIntervention,
    TeamObservation,
    WorldEvent,
)


class SimulationSetupError(ValueError):
    def __init__(self, message: str, issues: tuple[ValidationIssue, ...] = ()) -> None:
        super().__init__(message)
        self.issues = issues


@dataclass(frozen=True)
class StepOutcome:
    activated_events: tuple[WorldEvent, ...]
    interventions: tuple[SafetyIntervention, ...]
    issues: tuple[ValidationIssue, ...]
    finished: bool
    termination_reason: str | None


@dataclass
class SimulationSession:
    mission: MissionSpec
    scenario: Scenario
    seed: int
    controller_kind: str = "quadratic"
    dt: float = limits.DT_S
    max_steps: int = limits.MAX_SIM_STEPS

    def __post_init__(self) -> None:
        if not 0 <= self.seed <= 2**31 - 1:
            raise ValueError("seed must be a non-negative 31-bit integer")
        if self.dt <= 0 or not math.isfinite(self.dt):
            raise ValueError("dt must be positive and finite")
        self.rng = random.Random(self.seed)
        self.states: tuple[RobotState, ...] = self.scenario.initial_states(
            self.mission.robot_count,
            self.mission.constraints.minimum_robot_separation,
            self.rng,
        )
        self.controller = FormationController(
            mission=self.mission,
            arena_width=self.scenario.width,
            arena_height=self.scenario.height,
            estimator_kind=(
                "weighted_centroid" if self.controller_kind == "baseline" else self.controller_kind
            ),
            dt=self.dt,
        )
        self.safety_filter = SafetyFilter()
        self.step_index = 0
        self.time_s = 0.0
        self.frames: list[Frame] = []
        self.interventions: list[SafetyIntervention] = []
        self.world_events: list[WorldEvent] = []
        self.finished = False
        self.termination_reason: str | None = None
        self.safety_failure = False
        self._scheduled_seen: set[str] = set()
        self._active_ids: tuple[str, ...] = ()
        self._recent_step_outcome: StepOutcome | None = None

        initial_issues = validate_state(
            self.states,
            self.mission,
            self.scenario.width,
            self.scenario.height,
            self.scenario.active_regions(self.time_s),
            self.time_s,
        )
        if initial_issues:
            raise SimulationSetupError(
                "initial robot state violates safety constraints",
                tuple(initial_issues),
            )

        self._sync_active_regions()
        self.current_observation = self._sample_observation(
            self.states, self.step_index, self.time_s
        )
        self.controller.update(self.current_observation)
        self.frames.append(self._make_frame(self.states, self.current_observation))

    @property
    def active_regions(self) -> tuple[Region, ...]:
        return self.scenario.active_regions(self.time_s)

    @property
    def current_estimate(self):  # type: ignore[no-untyped-def]
        return self.controller.estimate

    def _sync_active_regions(self) -> None:
        self._active_ids = tuple(
            region.id for region in self.scenario.active_regions(self.time_s)
        )

    def _sample_observation(
        self,
        states: tuple[RobotState, ...],
        step: int,
        time_s: float,
    ) -> TeamObservation:
        observations = tuple(
            RobotObservation(
                robot_id=state.robot_id,
                step=step,
                time_s=time_s,
                x=state.x,
                y=state.y,
                heading=state.heading,
                measurement=self.scenario.truth_field.measure(Vec2(state.x, state.y), self.rng),
            )
            for state in states
        )
        return TeamObservation(step=step, time_s=time_s, robots=observations)

    def _make_frame(
        self,
        states: tuple[RobotState, ...],
        observation: TeamObservation,
    ) -> Frame:
        measurements = {robot.robot_id: robot.measurement for robot in observation.robots}
        return Frame(
            step=self.step_index,
            time_s=self.time_s,
            robots=tuple(
                FrameRobot(
                    robot_id=state.robot_id,
                    x=state.x,
                    y=state.y,
                    heading=state.heading,
                    measurement=measurements[state.robot_id],
                )
                for state in states
            ),
            estimate=self.controller.estimate,
            formation_error_estimate=self.controller.formation_error_estimate,
            obstacle_version=len(self._active_ids),
            active_region_ids=self._active_ids,
        )

    def _activate_due(self, next_time_s: float) -> tuple[WorldEvent, ...]:
        events: list[WorldEvent] = []
        for region in sorted(
            self.scenario.scheduled_regions(), key=lambda item: (item.active_from_s, item.id)
        ):
            if region.active_from_s <= next_time_s + 1e-9 and region.id not in self._scheduled_seen:
                self._scheduled_seen.add(region.id)
                event = WorldEvent(
                    time_s=region.active_from_s,
                    event_type="obstacle_change",
                    regions=(region,),
                    detail=f"{region.label or region.id} activated on the public map",
                )
                events.append(event)
                self.world_events.append(event)
        return tuple(events)

    def step(self) -> StepOutcome:
        if self.finished:
            raise RuntimeError("simulation already finished")

        activated = self._activate_due(self.time_s + self.dt)
        self._sync_active_regions()

        proposed_commands = self.controller.propose(
            self.current_observation,
            self.scenario.active_regions(self.time_s),
            self.time_s,
        )
        filter_result = self.safety_filter.apply(
            states=self.states,
            commands=proposed_commands,
            mission=self.mission,
            width=self.scenario.width,
            height=self.scenario.height,
            regions=self.scenario.regions,
            time_s=self.time_s,
            step=self.step_index,
            dt=self.dt,
        )
        for intervention in filter_result.interventions:
            self.interventions.append(intervention)

        candidate_states = tuple(
            integrate_state(state, command, self.dt)
            for state, command in zip(self.states, filter_result.commands, strict=True)
        )
        next_time = self.time_s + self.dt
        post_issues = validate_transition(
            self.states,
            candidate_states,
            self.mission,
            self.scenario.width,
            self.scenario.height,
            self.scenario.regions,
            next_time,
            self.dt,
        )

        if post_issues:
            self.safety_failure = True
            candidate_states = self.states
            self.interventions.append(
                SafetyIntervention(
                    step=self.step_index,
                    time_s=self.time_s,
                    kind="post_step_revert",
                    robot_id=None,
                    detail="post-step validator rejected the transition; previous state retained",
                )
            )

        self.step_index += 1
        self.time_s = next_time
        self.states = candidate_states
        self.current_observation = self._sample_observation(
            self.states, self.step_index, self.time_s
        )
        self.controller.update(self.current_observation)
        self._sync_active_regions()
        self.frames.append(self._make_frame(self.states, self.current_observation))

        issues = tuple(filter_result.issues) + tuple(post_issues)
        if self.safety_failure:
            self.finished = True
            self.termination_reason = "safety_abort"
        elif self.time_s >= self.mission.search.max_duration_s - 1e-9:
            self.finished = True
            self.termination_reason = "timeout"
        elif self._nominal_convergence():
            self.finished = True
            self.termination_reason = "nominal_convergence"
        elif self.step_index >= self.max_steps:
            self.finished = True
            self.termination_reason = "timeout"

        outcome = StepOutcome(
            activated_events=activated,
            interventions=tuple(filter_result.interventions),
            issues=issues,
            finished=self.finished,
            termination_reason=self.termination_reason,
        )
        self._recent_step_outcome = outcome
        return outcome

    def _nominal_convergence(self) -> bool:
        if not self.controller.estimate.valid:
            return False
        if self.time_s < 8.0:
            return False
        tolerance = self.mission.termination.formation_tolerance
        settled_threshold = max(0.03, min(tolerance, tolerance * 0.6))
        if not self.controller.formation_settled(
            limits.FORMATION_DWELL_S, settled_threshold
        ):
            return False
        return self.controller.estimate_stable(limits.ESTIMATE_STABILITY_WINDOW_S)

    def run_to_completion(self) -> SimulationSession:
        while not self.finished:
            self.step()
        return self

    @property
    def simulated_duration_s(self) -> float:
        return self.frames[-1].time_s if self.frames else 0.0
