"""Run orchestration service shared by HTTP routes, scripts, and tests."""

from __future__ import annotations

import math
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Literal

from app import limits
from app.config import Settings, get_settings
from app.evaluation.evaluator import EvaluationResult, evaluate_run
from app.schemas import MissionSpec
from app.services.agent import (
    BasetenDecisionProvider,
    MockDecisionProvider,
    OrchestrationResult,
    run_with_agent,
)
from app.services.provider import BasetenClient, ProviderError
from app.simulation.engine import SimulationSession, SimulationSetupError
from app.simulation.scenario import Scenario

AgentMode = Literal["off", "auto", "mock", "live"]
ControllerKind = Literal["quadratic", "baseline"]


@dataclass
class RunOutcome:
    run_id: str
    scenario: Scenario
    mission: MissionSpec
    seed: int
    controller: str
    frames: list[dict[str, Any]]
    evaluation: EvaluationResult
    agent: dict[str, Any]
    world_events: list[dict[str, Any]]
    safety: dict[str, Any]
    duration_s: float
    wall_clock_ms: float
    warnings: list[str] = field(default_factory=list)

    def to_public(self, request_id: str) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "scenario": self.scenario.to_public(),
            "mission": self.mission,
            "seed": self.seed,
            "controller": self.controller,
            "agent": self.agent,
            "frames": self.frames,
            "world_events": self.world_events,
            "safety": self.safety,
            "evaluation": self.evaluation.to_public(),
            "duration_s": round(self.duration_s, 3),
            "wall_clock_ms": round(self.wall_clock_ms, 1),
            "warnings": self.warnings,
            "request_id": request_id,
        }


def _downsample_frames(
    frames: list[Any], maximum: int = 420
) -> list[dict[str, Any]]:
    if len(frames) <= maximum:
        return [frame.to_public() for frame in frames]
    stride = max(1, math.ceil(len(frames) / maximum))
    selected = frames[::stride]
    if selected[-1] is not frames[-1]:
        selected.append(frames[-1])
    return [frame.to_public() for frame in selected]


def _safety_summary(interventions: list[Any]) -> dict[str, Any]:
    counts: dict[str, int] = {}
    for item in interventions:
        counts[item.kind] = counts.get(item.kind, 0) + 1
    if len(interventions) <= 120:
        listed = [item.to_public() for item in interventions]
    else:
        listed = [item.to_public() for item in interventions[:40]] + [
            item.to_public() for item in interventions[-80:]
        ]
    return {
        "total": len(interventions),
        "counts_by_kind": counts,
        "interventions": listed,
        "truncated": len(interventions) > len(listed),
    }


def resolve_agent_mode(mode: AgentMode, settings: Settings) -> Literal["off", "mock", "live"]:
    if mode == "off":
        return "off"
    if mode == "mock":
        return "mock"
    if mode == "live":
        if not settings.provider_configured:
            raise ProviderError(
                503,
                "provider_not_configured",
                "Live agent decisions were requested but BASETEN_API_KEY is not configured.",
            )
        return "live"
    return "live" if settings.provider_configured else "mock"


async def run_scenario(
    scenario: Scenario,
    mission: MissionSpec,
    seed: int,
    controller: ControllerKind = "quadratic",
    agent_mode: AgentMode = "auto",
    settings: Settings | None = None,
    transport: Any | None = None,
) -> RunOutcome:
    settings = settings or get_settings()
    resolved = resolve_agent_mode(agent_mode, settings)
    warnings: list[str] = []
    if agent_mode == "auto" and resolved == "mock":
        warnings.append(
            "BASETEN_API_KEY is not configured; agent decisions came from the "
            "deterministic offline mock, not live model inference."
        )

    try:
        session = SimulationSession(
            mission=mission,
            scenario=scenario,
            seed=seed,
            controller_kind=controller,
        )
    except SimulationSetupError as exc:
        details = [issue.to_public() for issue in exc.issues]
        raise ProviderError(
            422,
            "simulation_setup_invalid",
            str(exc),
            details,
        ) from exc
    except ValueError as exc:
        raise ProviderError(422, "simulation_setup_invalid", str(exc)) from exc

    started = time.perf_counter()
    if resolved == "off":
        session.run_to_completion()
        orchestration = OrchestrationResult(
            session=session,
            provider_mode="off",
            provider_model="none",
        )
    else:
        if resolved == "mock":
            provider = MockDecisionProvider()
        else:
            provider = BasetenDecisionProvider(
                settings=settings,
                client=BasetenClient(settings, transport=transport),
            )
        orchestration = await run_with_agent(
            session,
            scenario,
            provider,
            max_decisions=settings.max_model_calls,
            max_replans=settings.max_replans,
        )
    wall_clock_ms = (time.perf_counter() - started) * 1000.0

    if not session.frames:
        raise ProviderError(500, "simulation_empty", "The simulation produced no frames.")
    if not session.termination_reason:
        raise ProviderError(500, "simulation_unfinished", "The simulation did not terminate.")

    evaluation = evaluate_run(
        scenario=scenario,
        mission=mission,
        frames=session.frames,
        interventions=session.interventions,
        world_events=session.world_events,
        termination_reason=session.termination_reason,
        wall_clock_ms=wall_clock_ms,
        seed=seed,
        controller_name=session.controller.name,
    )

    provider_mode = orchestration.provider_mode
    if provider_mode == "live" and not orchestration.live_verified:
        warnings.append("No live decision call succeeded during this run.")

    agent_summary = {
        "mode": provider_mode,
        "model": orchestration.provider_model,
        "decision_calls": orchestration.decision_calls,
        "replans": orchestration.replans,
        "live_calls": orchestration.live_calls,
        "live_verified": orchestration.live_verified,
        "max_decisions": settings.max_model_calls,
        "max_replans": settings.max_replans,
        "termination_detail": orchestration.termination_detail,
        "trace": orchestration.trace,
    }

    return RunOutcome(
        run_id=uuid.uuid4().hex,
        scenario=scenario,
        mission=mission,
        seed=seed,
        controller=controller,
        frames=_downsample_frames(session.frames),
        evaluation=evaluation,
        agent=agent_summary,
        world_events=[event.to_public() for event in session.world_events],
        safety=_safety_summary(session.interventions),
        duration_s=session.time_s,
        wall_clock_ms=wall_clock_ms,
        warnings=warnings,
    )


def default_seed_bounds() -> dict[str, int]:
    return {"min": 0, "max": 2**31 - 1, "default": 42}


def run_limits() -> dict[str, float | int]:
    return {
        "max_steps": limits.MAX_SIM_STEPS,
        "dt_s": limits.DT_S,
    }
