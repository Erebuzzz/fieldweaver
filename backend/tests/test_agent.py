from __future__ import annotations

import json

import httpx
import pytest

from app.config import DEFAULT_BASE_URL, EXACT_MODEL_ID, Settings
from app.schemas import AgentDecision, DecisionAction, ReasonCode, default_mission_spec
from app.services.agent import (
    AgentEstimate,
    AgentObservation,
    BasetenDecisionProvider,
    BoundedOrchestrator,
    MockDecisionProvider,
    Trigger,
    run_with_agent,
)
from app.services.provider import BasetenClient, ProviderError
from app.simulation.engine import SimulationSession
from app.simulation.scenario import DISTURBED_CORRIDOR, OPEN_FIELD


def _settings() -> Settings:
    return Settings(
        baseten_api_key="test-key",
        baseten_base_url=DEFAULT_BASE_URL,
        baseten_model=EXACT_MODEL_ID,
        model_timeout_s=2.0,
        model_max_retries=0,
        max_replans=2,
        max_model_calls=2,
        cors_origins=("http://localhost:3000",),
    )


def _observation() -> AgentObservation:
    return AgentObservation(
        event_id="test-event",
        reason_code=ReasonCode.OBSTACLE_CHANGE,
        step=10,
        time_s=1.0,
        robot_count=6,
        formation_radius_m=1.5,
        estimate=AgentEstimate(x=6.0, y=4.5, confidence=0.5, valid=True),
        team_centroid_x=1.5,
        team_centroid_y=5.0,
        mean_distance_to_estimate_m=4.8,
        active_region_ids=["wall-dynamic"],
        recent_safety_interventions=0,
        recent_intervention_kinds=[],
        maximum_speed_mps=0.5,
        minimum_separation_m=0.35,
        minimum_clearance_m=0.2,
        remaining_duration_s=80.0,
        allowed_actions=list(DecisionAction),
        policy_notes=["Ground truth is withheld."],
    )


class FixedProvider:
    mode = "mock"
    model = "fixed-test-provider"

    def __init__(self, decision: AgentDecision) -> None:
        self.decision = decision
        self.calls = 0

    async def decide(self, observation: AgentObservation) -> AgentDecision:
        self.calls += 1
        return self.decision


@pytest.mark.asyncio
async def test_live_decision_provider_validates_model_output() -> None:
    decision = AgentDecision(
        schema_version="1.0",
        decision=DecisionAction.SWITCH_SEARCH_PATTERN,
        reason_code=ReasonCode.OBSTACLE_CHANGE,
        short_rationale="Use the validated deterministic detour.",
    )
    captured: list[dict] = []

    def handler(request: httpx.Request) -> httpx.Response:
        captured.append(json.loads(request.read()))
        return httpx.Response(
            200,
            json={"choices": [{"message": {"content": decision.model_dump_json()}}]},
        )

    settings = _settings()
    client = BasetenClient(settings, transport=httpx.MockTransport(handler))
    provider = BasetenDecisionProvider(settings, client)
    result = await provider.decide(_observation())

    assert result.decision is DecisionAction.SWITCH_SEARCH_PATTERN
    prompt = captured[0]["messages"][1]["content"]
    assert "ground_truth" not in prompt
    assert '"source"' not in prompt


@pytest.mark.asyncio
async def test_live_decision_provider_rejects_unsafe_fields() -> None:
    response = {
        "schema_version": "1.0",
        "decision": "switch_search_pattern",
        "reason_code": "obstacle_change",
        "short_rationale": "try a route",
        "controller_gains": {"speed": 100},
    }
    client = BasetenClient(
        _settings(),
        transport=httpx.MockTransport(
            lambda request: httpx.Response(
                200,
                json={"choices": [{"message": {"content": json.dumps(response)}}]},
            )
        ),
    )

    with pytest.raises(ProviderError) as raised:
        await BasetenDecisionProvider(_settings(), client).decide(_observation())
    assert raised.value.code == "model_output_invalid"


@pytest.mark.asyncio
async def test_obstacle_event_runs_a_bounded_detour_and_records_real_trace() -> None:
    session = SimulationSession(
        mission=default_mission_spec(),
        scenario=DISTURBED_CORRIDOR,
        seed=42,
    )
    result = await run_with_agent(
        session,
        DISTURBED_CORRIDOR,
        MockDecisionProvider(),
        max_decisions=2,
        max_replans=2,
    )

    phases = [entry["phase"] for entry in result.trace]
    assert result.decision_calls <= 2
    assert result.replans <= 2
    assert "event" in phases
    assert "decision" in phases
    assert "applied" in phases or "terminated" in phases
    assert [entry["seq"] for entry in result.trace] == list(
        range(1, len(result.trace) + 1)
    )
    assert any(entry.get("reason_code") == "obstacle_change" for entry in result.trace)


@pytest.mark.asyncio
async def test_decision_budget_exhaustion_stops_at_first_event() -> None:
    session = SimulationSession(
        mission=default_mission_spec(), scenario=DISTURBED_CORRIDOR, seed=42
    )
    provider = MockDecisionProvider()
    result = await run_with_agent(
        session, DISTURBED_CORRIDOR, provider, max_decisions=0, max_replans=0
    )

    assert result.decision_calls == 0
    assert session.termination_reason == "replan_budget_exhausted"
    assert result.trace[-1]["phase"] == "terminated"


@pytest.mark.asyncio
async def test_abort_action_stops_and_is_recorded() -> None:
    session = SimulationSession(
        mission=default_mission_spec(), scenario=DISTURBED_CORRIDOR, seed=42
    )
    provider = FixedProvider(
        AgentDecision(
            schema_version="1.0",
            decision=DecisionAction.ABORT_MISSION,
            reason_code=ReasonCode.OBSTACLE_CHANGE,
            short_rationale="Stop for operator review.",
        )
    )
    result = await run_with_agent(
        session, DISTURBED_CORRIDOR, provider, max_decisions=1, max_replans=1
    )

    assert provider.calls == 1
    assert session.termination_reason == "user_abort"
    assert [entry["phase"] for entry in result.trace][-2:] == ["decision", "terminated"]


def test_agent_observation_schema_has_no_truth_or_source_fields() -> None:
    session = SimulationSession(
        mission=default_mission_spec(), scenario=OPEN_FIELD, seed=42
    )
    orchestrator = BoundedOrchestrator(
        session, OPEN_FIELD, MockDecisionProvider(), max_decisions=1, max_replans=1
    )
    observation = orchestrator._build_observation(
        Trigger(ReasonCode.BLOCKED_PROGRESS, "blocked:test", "test event")
    )
    payload = observation.model_dump()

    assert "ground_truth" not in payload
    assert "source" not in payload
    assert "source_x" not in payload
    assert "source_y" not in payload
