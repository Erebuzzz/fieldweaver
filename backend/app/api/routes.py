from __future__ import annotations

from fastapi import APIRouter, Request

from app import limits
from app.api.schemas import (
    HealthResponse,
    LatestEvaluationResponse,
    MissionCompileRequest,
    MissionCompileResponse,
    ProviderPublic,
    RootResponse,
    SafetyEnvelopePublic,
    ScenarioListResponse,
    SimulationInfo,
    SimulationRunRequest,
    SimulationRunResponse,
)
from app.config import get_settings
from app.errors import FieldWeaverError
from app.services.compiler import compile_mission
from app.services.provider import ProviderError
from app.services.runner import (
    RunOutcome,
    default_seed_bounds,
    run_limits,
    run_scenario,
)
from app.simulation.scenario import get_scenario, list_public_scenarios

router = APIRouter()


@router.get("/", response_model=RootResponse)
def root() -> RootResponse:
    return RootResponse(
        name="FieldWeaver",
        version=limits.APP_VERSION,
        documentation="/docs",
    )


@router.get("/api/health", response_model=HealthResponse)
def health(request: Request) -> HealthResponse:
    settings = get_settings()
    provider = ProviderPublic(**settings.public_provider())
    return HealthResponse(
        status="ok",
        api_version="v1",
        app_version=limits.APP_VERSION,
        mode="live_configured" if settings.provider_configured else "offline_mock",
        provider=provider,
        simulation=SimulationInfo(
            dt_s=limits.DT_S,
            arena_width_m=limits.ARENA_WIDTH_M,
            arena_height_m=limits.ARENA_HEIGHT_M,
            min_robots=limits.MIN_ROBOTS,
            max_robots=limits.MAX_ROBOTS,
            mission_schema_version=limits.SCHEMA_VERSION,
        ),
        safety=SafetyEnvelopePublic(
            max_speed_mps=limits.MAX_SPEED_MPS,
            min_robot_separation_m=limits.MIN_SEPARATION_M,
            min_obstacle_clearance_m=limits.MIN_CLEARANCE_M,
            max_duration_s=limits.MAX_DURATION_S,
            min_ring_radius_m=limits.MIN_RING_RADIUS_M,
            max_ring_radius_m=limits.MAX_RING_RADIUS_M,
            boundary_margin_m=limits.BOUNDARY_MARGIN_M,
            max_replans=settings.max_replans,
            max_model_calls=settings.max_model_calls,
        ),
        live_provider_verified=False,
        request_id=request.state.request_id,
    )


@router.get("/api/scenarios", response_model=ScenarioListResponse)
def scenarios(request: Request) -> ScenarioListResponse:
    return ScenarioListResponse(
        scenarios=list_public_scenarios(),
        seed=default_seed_bounds(),
        limits=run_limits(),
        request_id=request.state.request_id,
    )


@router.post("/api/missions/compile", response_model=MissionCompileResponse)
async def compile_mission_route(
    body: MissionCompileRequest, request: Request
) -> MissionCompileResponse:
    try:
        scenario = get_scenario(body.scenario_id)
    except KeyError as exc:
        raise FieldWeaverError(
            404,
            "scenario_not_found",
            f"Unknown scenario '{body.scenario_id}'.",
        ) from exc

    try:
        result = await compile_mission(
            body.mission_text,
            scenario,
            mode=body.mode,
            settings=get_settings(),
        )
    except ProviderError as exc:
        raise FieldWeaverError(
            exc.status_code, exc.code, exc.message, exc.details
        ) from exc

    public = result.to_public()
    return MissionCompileResponse(
        spec=public["spec"],
        provider=public["provider"],
        warnings=public["warnings"],
        request_id=request.state.request_id,
    )


@router.post("/api/simulations/run", response_model=SimulationRunResponse)
async def run_simulation_route(
    body: SimulationRunRequest, request: Request
) -> SimulationRunResponse:
    try:
        scenario = get_scenario(body.scenario_id)
    except KeyError as exc:
        raise FieldWeaverError(
            404,
            "scenario_not_found",
            f"Unknown scenario '{body.scenario_id}'.",
        ) from exc

    try:
        outcome = await run_scenario(
            scenario=scenario,
            mission=body.mission,
            seed=body.seed,
            controller=body.controller,
            agent_mode=body.agent_mode,
            settings=get_settings(),
        )
    except ProviderError as exc:
        raise FieldWeaverError(
            exc.status_code, exc.code, exc.message, exc.details
        ) from exc

    request.app.state.latest_run = outcome
    return SimulationRunResponse.model_validate(outcome.to_public(request.state.request_id))


@router.get("/api/evaluations/latest", response_model=LatestEvaluationResponse)
def latest_evaluation(request: Request) -> LatestEvaluationResponse:
    outcome: RunOutcome | None = getattr(request.app.state, "latest_run", None)
    if outcome is None:
        raise FieldWeaverError(
            404,
            "evaluation_not_found",
            "No simulation evaluation is available in this backend process yet.",
        )
    return LatestEvaluationResponse(
        run_id=outcome.run_id,
        scenario_id=outcome.scenario.id,
        scenario_name=outcome.scenario.name,
        seed=outcome.seed,
        controller=outcome.controller,
        evaluation=outcome.evaluation.to_public(),
        agent=outcome.agent,
        request_id=request.state.request_id,
    )


@router.post("/api/scenes/segment")
def segment_scene() -> None:
    """Optional SAM integration is disabled until a verified endpoint exists."""

    raise FieldWeaverError(
        503,
        "perception_disabled",
        (
            "Scene segmentation is disabled in this build. No supported SAM 3.1 "
            "endpoint or credential has been verified. Use a built-in scenario."
        ),
    )
