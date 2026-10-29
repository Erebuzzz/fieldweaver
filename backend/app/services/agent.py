"""Bounded event-driven agent layer.

The model is consulted only when a monitor trigger fires. It receives a small
public observation with no ground-truth source data and may return only a
schema-validated `AgentDecision`. The application maps the chosen action to a
deterministic, already-implemented behaviour and the independent safety layer
still has final authority.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Literal, Protocol

from pydantic import Field, ValidationError

from app import limits
from app.config import Settings, get_settings
from app.schemas import (
    AgentDecision,
    DecisionAction,
    ReasonCode,
    RequestedProfile,
    StrictModel,
)
from app.services.provider import BasetenClient, ProviderError, extract_json_object
from app.simulation.engine import SimulationSession, StepOutcome
from app.simulation.geometry import Vec2
from app.simulation.planner import plan_detour_path, validate_path
from app.simulation.scenario import Scenario
from app.simulation.types import SafetyIntervention


class AgentEstimate(StrictModel):
    x: float
    y: float
    confidence: float
    valid: bool


class AgentObservation(StrictModel):
    """Public event summary. Contains no hidden source coordinates."""

    schema_version: Literal["1.0"] = "1.0"
    event_id: str
    reason_code: ReasonCode
    step: int = Field(ge=0)
    time_s: float = Field(ge=0)
    objective: Literal["locate_and_encircle_source"] = "locate_and_encircle_source"
    robot_count: int
    formation_radius_m: float
    estimate: AgentEstimate
    team_centroid_x: float
    team_centroid_y: float
    mean_distance_to_estimate_m: float
    active_region_ids: list[str]
    recent_safety_interventions: int
    recent_intervention_kinds: list[str]
    maximum_speed_mps: float
    minimum_separation_m: float
    minimum_clearance_m: float
    remaining_duration_s: float
    allowed_actions: list[DecisionAction]
    policy_notes: list[str]


@dataclass(frozen=True)
class Trigger:
    reason: ReasonCode
    event_id: str
    detail: str


class EventMonitor:
    """Deterministic monitor for obstacle changes, safety bursts, and blocked progress."""

    def __init__(
        self,
        cooldown_s: float = 5.0,
        blocked_window_s: float = 10.0,
        safety_stall_s: float = 4.0,
        safety_window_s: float = limits.SAFETY_EVENT_WINDOW_S,
        safety_threshold: int = 14,
    ) -> None:
        self.cooldown_s = cooldown_s
        self.blocked_window_s = blocked_window_s
        self.safety_stall_s = safety_stall_s
        self.safety_window_s = safety_window_s
        self.safety_threshold = safety_threshold
        self.best_formation: float | None = None
        self.last_progress_s = 0.0
        self.last_decision_s = -math.inf
        self._handled_events: set[str] = set()
        self._safety_triggers = 0

    def mark_decision(self, now_s: float) -> None:
        self.last_decision_s = now_s
        self.best_formation = None
        self.last_progress_s = now_s

    def observe(self, session: SimulationSession, outcome: StepOutcome) -> Trigger | None:
        now = session.time_s
        if outcome.activated_events:
            event = outcome.activated_events[0]
            key = f"{event.event_type}:{event.time_s}:{event.regions[0].id}"
            if key not in self._handled_events:
                self._handled_events.add(key)
                return Trigger(
                    reason=ReasonCode.OBSTACLE_CHANGE,
                    event_id=key,
                    detail=event.detail,
                )

        if session.controller.detour is not None:
            self.best_formation = None
            self.last_progress_s = now
            return None

        if now - self.last_decision_s < self.cooldown_s:
            return None

        if not session.controller.estimate.valid or now < 8.0:
            return None

        formation = session.controller.formation_error_estimate
        if not math.isfinite(formation):
            return None
        if self.best_formation is None or formation < self.best_formation - 0.02:
            self.best_formation = formation
            self.last_progress_s = now
            return None

        tolerance = session.mission.termination.formation_tolerance
        if formation <= tolerance + 0.08:
            return None

        stalled_for = now - self.last_progress_s
        recent = [
            item
            for item in session.interventions
            if item.time_s >= now - self.safety_window_s
        ]
        if (
            self._safety_triggers < 1
            and stalled_for >= self.safety_stall_s
            and len(recent) >= self.safety_threshold
        ):
            self._safety_triggers += 1
            return Trigger(
                reason=ReasonCode.REPEATED_SAFETY_INTERVENTIONS,
                event_id=f"safety:{int(now * 10)}",
                detail=f"{len(recent)} safety interventions while formation progress "
                f"stalled for {stalled_for:.1f} s",
            )

        if stalled_for >= self.blocked_window_s:
            return Trigger(
                reason=ReasonCode.BLOCKED_PROGRESS,
                event_id=f"blocked:{int(now * 10)}",
                detail=(
                    f"formation error has not improved for {stalled_for:.1f} s "
                    f"(still {formation:.2f} m against a tolerance of {tolerance:.2f} m)"
                ),
            )
        return None


class DecisionProvider(Protocol):
    mode: Literal["mock", "live"]
    model: str

    async def decide(self, observation: AgentObservation) -> AgentDecision: ...


class MockDecisionProvider:
    mode: Literal["mock"] = "mock"
    model = "deterministic-rule-mock"

    async def decide(self, observation: AgentObservation) -> AgentDecision:
        if observation.reason_code is ReasonCode.OBSTACLE_CHANGE:
            return AgentDecision(
                schema_version="1.0",
                decision=DecisionAction.SWITCH_SEARCH_PATTERN,
                reason_code=observation.reason_code,
                short_rationale=(
                    "A public obstacle change blocks the direct route; request a "
                    "deterministic detour."
                ),
                requested_profile=RequestedProfile.EXPLORATION,
            )
        if observation.reason_code is ReasonCode.BLOCKED_PROGRESS:
            return AgentDecision(
                schema_version="1.0",
                decision=DecisionAction.SWITCH_SEARCH_PATTERN,
                reason_code=observation.reason_code,
                short_rationale=(
                    "Team progress toward the estimate has stalled; request the "
                    "approved detour action."
                ),
                requested_profile=RequestedProfile.EXPLORATION,
            )
        if observation.reason_code is ReasonCode.REPEATED_SAFETY_INTERVENTIONS:
            return AgentDecision(
                schema_version="1.0",
                decision=DecisionAction.USE_CAUTIOUS_PROFILE,
                reason_code=observation.reason_code,
                short_rationale=(
                    "Repeated safety filtering indicates tight clearances; slow the team."
                ),
                requested_profile=RequestedProfile.CAUTIOUS,
            )
        return AgentDecision(
            schema_version="1.0",
            decision=DecisionAction.CONTINUE_CURRENT_PLAN,
            reason_code=ReasonCode.MISSION_PROGRESS_NORMAL,
            short_rationale="No supported intervention is required for this event.",
        )


_DECISION_SYSTEM_PROMPT = """You are FieldWeaver's bounded mission agent.
You receive one JSON event summary. Return exactly one JSON AgentDecision object.
No prose, no markdown fences, no code. Unknown fields are errors.
Allowed decisions, exactly:
- continue_current_plan
- switch_search_pattern
- use_cautious_profile
- request_user_clarification
- abort_mission
Rules:
- Use only the listed actions. Do not request controller gains, raw velocities,
  routes, code, or new limits.
- requested_profile may be "exploration" only for switch_search_pattern,
  "cautious" only for use_cautious_profile, otherwise omit it.
- reason_code must be one of: blocked_progress, obstacle_change,
  repeated_safety_interventions, route_infeasible, mission_progress_normal.
- short_rationale must be <=400 characters.
- The safety layer can veto any action and has final authority.
- Never ask for or invent a source coordinate.
Return shape:
{"schema_version":"1.0","decision":"switch_search_pattern","reason_code":"obstacle_change","short_rationale":"...","requested_profile":"exploration"}"""


class BasetenDecisionProvider:
    mode: Literal["live"] = "live"

    def __init__(
        self,
        settings: Settings | None = None,
        client: BasetenClient | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.model = self.settings.baseten_model
        self.client = client or BasetenClient(self.settings)

    async def decide(self, observation: AgentObservation) -> AgentDecision:
        messages = [
            {"role": "system", "content": _DECISION_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": observation.model_dump_json(indent=2),
            },
        ]
        result = await self.client.chat(messages, temperature=0.1)
        payload = extract_json_object(result.content)
        try:
            return AgentDecision.model_validate(payload)
        except ValidationError as exc:
            raise ProviderError(
                502,
                "model_output_invalid",
                "The live model returned an agent decision that failed strict validation.",
                [
                    {"loc": list(error["loc"]), "msg": error["msg"]}
                    for error in exc.errors()[:8]
                ],
            ) from exc


@dataclass
class OrchestrationResult:
    session: SimulationSession
    trace: list[dict[str, object]] = field(default_factory=list)
    decision_calls: int = 0
    replans: int = 0
    provider_mode: Literal["off", "mock", "live"] = "off"
    provider_model: str = "none"
    live_calls: int = 0
    live_verified: bool = False
    termination_detail: str | None = None


class BoundedOrchestrator:
    def __init__(
        self,
        session: SimulationSession,
        scenario: Scenario,
        provider: DecisionProvider,
        max_decisions: int = limits.DEFAULT_MAX_MODEL_CALLS,
        max_replans: int = limits.DEFAULT_MAX_REPLANS,
        monitor: EventMonitor | None = None,
    ) -> None:
        self.session = session
        self.scenario = scenario
        self.provider = provider
        self.max_decisions = max(0, max_decisions)
        self.max_replans = max(0, max_replans)
        self.monitor = monitor or EventMonitor()
        self.result = OrchestrationResult(
            session=session,
            provider_mode=provider.mode,
            provider_model=provider.model,
        )

    async def run(self) -> OrchestrationResult:
        session = self.session
        while not session.finished:
            outcome = session.step()
            if session.finished:
                break
            trigger = self.monitor.observe(session, outcome)
            if trigger is None:
                continue
            await self._handle(trigger)
        return self.result

    def _trace(
        self,
        phase: str,
        detail: str,
        *,
        reason: ReasonCode | None = None,
        decision: AgentDecision | None = None,
        extra: dict[str, object] | None = None,
    ) -> None:
        entry: dict[str, object] = {
            "seq": len(self.result.trace) + 1,
            "t": round(self.session.time_s, 3),
            "phase": phase,
            "detail": detail,
            "provider_mode": self.provider.mode,
        }
        if reason is not None:
            entry["reason_code"] = reason.value
        if decision is not None:
            entry["decision"] = decision.decision.value
            entry["rationale"] = decision.short_rationale
        if extra:
            entry.update(extra)
        self.result.trace.append(entry)

    def _terminate(self, reason: str, detail: str) -> None:
        self.session.finished = True
        self.session.termination_reason = reason
        self.result.termination_detail = detail
        self._trace("terminated", detail)

    async def _handle(self, trigger: Trigger) -> None:
        if self.result.decision_calls >= self.max_decisions:
            self._terminate(
                "replan_budget_exhausted",
                f"Decision budget of {self.max_decisions} is exhausted.",
            )
            return
        needs_replan = trigger.reason in {
            ReasonCode.OBSTACLE_CHANGE,
            ReasonCode.BLOCKED_PROGRESS,
            ReasonCode.ROUTE_INFEASIBLE,
        }
        if needs_replan and self.result.replans >= self.max_replans:
            self._terminate(
                "replan_budget_exhausted",
                f"Replan budget of {self.max_replans} is exhausted.",
            )
            return

        observation = self._build_observation(trigger)
        self._trace(
            "event",
            trigger.detail,
            reason=trigger.reason,
            extra={"event_id": trigger.event_id},
        )
        self.result.decision_calls += 1
        if self.provider.mode == "live":
            self.result.live_calls += 1

        try:
            decision = await self.provider.decide(observation)
        except ProviderError as exc:
            self._trace("rejected", f"Provider failure: {exc.code}")
            self._terminate("provider_failure", f"Provider failure: {exc.code}")
            return
        except Exception:
            self._trace("rejected", "Provider raised an unexpected error")
            self._terminate("provider_failure", "Provider raised an unexpected error")
            return

        if self.provider.mode == "live":
            self.result.live_verified = True
        self._trace("decision", decision.short_rationale, reason=trigger.reason, decision=decision)
        self._apply(decision)
        self.monitor.mark_decision(self.session.time_s)

    def _apply(self, decision: AgentDecision) -> None:
        action = decision.decision
        if action is DecisionAction.CONTINUE_CURRENT_PLAN:
            self._trace("applied", "Continuing the current deterministic plan.")
            return
        if action is DecisionAction.USE_CAUTIOUS_PROFILE:
            self.session.controller.set_cautious()
            self._trace("applied", "Cautious profile enabled: speed capped at 60 percent.")
            return
        if action is DecisionAction.SWITCH_SEARCH_PATTERN:
            self.result.replans += 1
            self._apply_detour()
            return
        if action is DecisionAction.REQUEST_USER_CLARIFICATION:
            self._terminate(
                "user_clarification_required",
                "The agent requested operator clarification; the run stopped safely.",
            )
            return
        if action is DecisionAction.ABORT_MISSION:
            self._terminate("user_abort", "The agent requested a mission abort; the run stopped.")
            return
        self._trace("rejected", "Unsupported decision action was rejected.")
        self._terminate("invalid_decision", "Unsupported decision action was rejected.")

    def _apply_detour(self) -> None:
        session = self.session
        estimate = session.controller.estimate
        if not estimate.valid:
            self._trace("rejected", "Detour rejected: no valid source estimate to stage around.")
            return
        active = self.scenario.active_regions(session.time_s)
        clearance = session.mission.constraints.minimum_obstacle_clearance + 0.05
        positions = {
            robot.robot_id: Vec2(robot.x, robot.y) for robot in session.states
        }
        goals = session.controller.ring_slot_targets(positions, estimate.x, estimate.y)

        routes: dict[int, tuple[Vec2, ...]] = {}
        expanded = 0
        total_length = 0.0
        for robot in session.states:
            goal = goals.get(robot.robot_id)
            if goal is None:
                self._trace(
                    "rejected",
                    f"Detour rejected: no ring slot for robot {robot.robot_id}.",
                )
                self._terminate(
                    "route_infeasible",
                    f"No ring slot exists for robot {robot.robot_id}.",
                )
                return
            plan = plan_detour_path(
                start=positions[robot.robot_id],
                goal=goal,
                width=self.scenario.width,
                height=self.scenario.height,
                regions=active,
                clearance=clearance,
                margin=limits.BOUNDARY_MARGIN_M,
                cell_size=0.25,
            )
            if not plan.path:
                self._trace(
                    "rejected",
                    f"Detour rejected for robot {robot.robot_id}: {plan.reason}.",
                )
                self._terminate(
                    "route_infeasible",
                    f"No safe route exists for robot {robot.robot_id}: {plan.reason}.",
                )
                return
            endpoint_error = plan.path[-1].distance_to(goal)
            if plan.path[-1] != goal:
                self._trace(
                    "rejected",
                    f"Detour rejected for robot {robot.robot_id}: the route cannot reach "
                    f"its ring slot ({endpoint_error:.2f} m shifted).",
                )
                self._terminate(
                    "route_infeasible",
                    f"No safe route reaches the ring slot for robot {robot.robot_id}; "
                    f"the formation position is blocked.",
                )
                return
            validation = validate_path(
                plan.path,
                self.scenario.width,
                self.scenario.height,
                active,
                clearance,
                margin=limits.BOUNDARY_MARGIN_M,
            )
            if validation is not None:
                self._trace(
                    "rejected",
                    f"Detour rejected for robot {robot.robot_id}: {validation}.",
                )
                self._terminate(
                    "route_infeasible",
                    f"No safe route passed validation for robot {robot.robot_id}: {validation}.",
                )
                return
            routes[robot.robot_id] = plan.path
            expanded += plan.expanded_nodes
            total_length += sum(
                plan.path[index].distance_to(plan.path[index + 1])
                for index in range(len(plan.path) - 1)
            )

        session.controller.set_detour(routes, session.time_s, max_duration_s=45.0)
        lengths = ", ".join(
            f"{robot_id}:{session.controller.detour.lengths[robot_id]:.1f} m"
            for robot_id in sorted(routes)
        )
        self._trace(
            "applied",
            f"Per-robot detour applied: {len(routes)} validated routes, "
            f"{total_length:.1f} m total ({lengths}), {expanded} expanded nodes.",
        )

    def _build_observation(self, trigger: Trigger) -> AgentObservation:
        session = self.session
        estimate = session.controller.estimate
        centroid_x = sum(robot.x for robot in session.states) / len(session.states)
        centroid_y = sum(robot.y for robot in session.states) / len(session.states)
        mean_distance = sum(
            math.hypot(robot.x - estimate.x, robot.y - estimate.y)
            for robot in session.states
        ) / len(session.states)
        recent = [
            item
            for item in session.interventions
            if item.time_s >= session.time_s - limits.SAFETY_EVENT_WINDOW_S
        ]
        return AgentObservation(
            event_id=trigger.event_id,
            reason_code=trigger.reason,
            step=session.step_index,
            time_s=session.time_s,
            robot_count=session.mission.robot_count,
            formation_radius_m=session.mission.formation.radius,
            estimate=AgentEstimate(
                x=estimate.x,
                y=estimate.y,
                confidence=estimate.confidence,
                valid=estimate.valid,
            ),
            team_centroid_x=centroid_x,
            team_centroid_y=centroid_y,
            mean_distance_to_estimate_m=mean_distance,
            active_region_ids=[region.id for region in session.active_regions],
            recent_safety_interventions=len(recent),
            recent_intervention_kinds=sorted({item.kind for item in recent}),
            maximum_speed_mps=session.mission.constraints.maximum_speed,
            minimum_separation_m=session.mission.constraints.minimum_robot_separation,
            minimum_clearance_m=session.mission.constraints.minimum_obstacle_clearance,
            remaining_duration_s=max(
                0.0, session.mission.search.max_duration_s - session.time_s
            ),
            allowed_actions=list(DecisionAction),
            policy_notes=[
                "The safety layer can veto any action and has final authority.",
                "Only listed actions are valid; no code, gains, or actuator values are accepted.",
                "The hidden source position is not available to this observation.",
            ],
        )


async def run_with_agent(
    session: SimulationSession,
    scenario: Scenario,
    provider: DecisionProvider,
    max_decisions: int,
    max_replans: int,
) -> OrchestrationResult:
    orchestrator = BoundedOrchestrator(
        session,
        scenario,
        provider,
        max_decisions=max_decisions,
        max_replans=max_replans,
    )
    return await orchestrator.run()


def safe_stop_summary(interventions: list[SafetyIntervention]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in interventions:
        counts[item.kind] = counts.get(item.kind, 0) + 1
    return counts
