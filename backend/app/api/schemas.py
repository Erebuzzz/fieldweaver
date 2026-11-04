from __future__ import annotations

from typing import Annotated, Any, Literal

from pydantic import Field, SecretStr, StringConstraints

from app.schemas import MissionSpec, StrictModel

MissionText = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=2_000),
]


class ProviderPublic(StrictModel):
    name: Literal["baseten", "mock"]
    model: str
    configured: bool
    mode: Literal["live", "mock"]


class SimulationInfo(StrictModel):
    dt_s: float
    arena_width_m: float
    arena_height_m: float
    min_robots: int
    max_robots: int
    mission_schema_version: str


class SafetyEnvelopePublic(StrictModel):
    max_speed_mps: float
    min_robot_separation_m: float
    min_obstacle_clearance_m: float
    max_duration_s: float
    min_ring_radius_m: float
    max_ring_radius_m: float
    boundary_margin_m: float
    max_replans: int
    max_model_calls: int


class HealthResponse(StrictModel):
    status: Literal["ok"]
    api_version: str
    app_version: str
    mode: Literal["offline_mock", "live_configured"]
    provider: ProviderPublic
    simulation: SimulationInfo
    safety: SafetyEnvelopePublic
    live_provider_verified: bool = False
    request_id: str


class RootResponse(StrictModel):
    name: Literal["FieldWeaver"]
    version: str
    documentation: str


class ProviderSelection(StrictModel):
    name: Literal["baseten", "meta", "fireworks"]
    model: str = Field(min_length=1, max_length=200, pattern=r"^[A-Za-z0-9._/-]+$")
    api_key: SecretStr = Field(min_length=1, max_length=4096)


class MissionCompileRequest(StrictModel):
    mission_text: MissionText
    scenario_id: str = Field(default="open_field", min_length=1, max_length=80)
    mode: Literal["auto", "mock", "live"] = "auto"
    provider: ProviderSelection | None = None


class ScenarioPublic(StrictModel):
    id: str
    name: str
    description: str
    arena: dict[str, float]
    sensor: dict[str, Any]
    initial_regions: list[dict[str, Any]]
    scheduled_event_count: int
    default_robot_count: int
    recommended_mission: str
    tags: list[str]
    source_revealed: Literal[False]


class ScenarioListResponse(StrictModel):
    scenarios: list[ScenarioPublic]
    seed: dict[str, int]
    limits: dict[str, float | int]
    request_id: str


class CompileProviderMetadata(StrictModel):
    mode: Literal["mock", "live"]
    name: Literal["mock", "baseten", "meta", "fireworks"]
    model: str
    latency_ms: float = Field(ge=0)
    live_verified: bool
    usage: dict[str, int]


class MissionCompileResponse(StrictModel):
    spec: MissionSpec
    provider: CompileProviderMetadata
    warnings: list[str]
    request_id: str


class SimulationRunRequest(StrictModel):
    mission: MissionSpec
    scenario_id: str = Field(min_length=1, max_length=80)
    seed: int = Field(default=42, ge=0, le=2**31 - 1)
    controller: Literal["quadratic", "baseline"] = "quadratic"
    agent_mode: Literal["off", "auto", "mock", "live"] = "auto"
    provider: ProviderSelection | None = None


class SimulationRunResponse(StrictModel):
    run_id: str
    scenario: ScenarioPublic
    mission: MissionSpec
    seed: int
    controller: Literal["quadratic", "baseline"]
    agent: dict[str, Any]
    frames: list[dict[str, Any]]
    world_events: list[dict[str, Any]]
    safety: dict[str, Any]
    evaluation: dict[str, Any]
    duration_s: float
    wall_clock_ms: float
    warnings: list[str]
    request_id: str


class LatestEvaluationResponse(StrictModel):
    run_id: str
    scenario_id: str
    scenario_name: str
    seed: int
    controller: Literal["quadratic", "baseline"]
    evaluation: dict[str, Any]
    agent: dict[str, Any]
    request_id: str
