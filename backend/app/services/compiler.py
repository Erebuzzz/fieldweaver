"""Mission compilation: live Baseten or an explicit deterministic mock.

The model returns only a JSON object that must validate as `MissionSpec`.
Application-side validation is authoritative regardless of what the model says.
"""

from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass, field
from typing import Any, Literal

from pydantic import ValidationError

from app import limits
from app.config import Settings, get_settings
from app.schemas import MissionSpec, default_mission_spec
from app.services.provider import BasetenClient, ProviderError, extract_json_object
from app.simulation.scenario import Scenario

ProviderMode = Literal["auto", "mock", "live"]


@dataclass(frozen=True)
class CompilationResult:
    spec: MissionSpec
    mode: Literal["mock", "live"]
    model: str
    latency_ms: float
    live_verified: bool
    warnings: list[str] = field(default_factory=list)
    usage: dict[str, int] = field(default_factory=dict)

    def to_public(self) -> dict[str, Any]:
        return {
            "spec": self.spec,
            "provider": {
                "mode": self.mode,
                "name": "baseten" if self.mode == "live" else "mock",
                "model": self.model,
                "latency_ms": round(self.latency_ms, 1),
                "live_verified": self.live_verified,
                "usage": self.usage,
            },
            "warnings": self.warnings,
        }


def resolve_mode(mode: ProviderMode, settings: Settings) -> Literal["mock", "live"]:
    if mode == "mock":
        return "mock"
    if mode == "live":
        if not settings.provider_configured:
            raise ProviderError(
                503,
                "provider_not_configured",
                "Live compilation was requested but BASETEN_API_KEY is not configured. "
                "Use mock mode or configure the server key.",
            )
        return "live"
    return "live" if settings.provider_configured else "mock"


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def _add_unique(items: list[str], value: str, maximum: int) -> None:
    if value and value not in items and len(items) < maximum:
        items.append(value)


_ROBOT_RE = re.compile(r"(\d+)\s*(?:robots?|drones?|agents?)", re.IGNORECASE)
_RADIUS_RE = re.compile(
    r"(?:ring|radius|circle)[^.\n]{0,50}?(\d+(?:\.\d+)?)\s*(?:m|meters?|metres?)\b",
    re.IGNORECASE,
)
_SEPARATION_RE = re.compile(
    r"(?:separation|apart|spacing)[^.\n]{0,30}?(\d+(?:\.\d+)?)\s*(?:m|meters?|metres?)\b",
    re.IGNORECASE,
)
_CLEARANCE_RE = re.compile(
    r"(?:clearance|distance from obstacles)[^.\n]{0,30}?(\d+(?:\.\d+)?)\s*(?:m|meters?|metres?)\b",
    re.IGNORECASE,
)
_SPEED_RE = re.compile(r"(\d+(?:\.\d+)?)\s*m\s*/\s*s\b", re.IGNORECASE)
_SECONDS_RE = re.compile(r"(\d+)\s*(?:seconds?|secs?)\b", re.IGNORECASE)

_UNSUPPORTED_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"\b(two|2|multiple|three|3)\s+sources?\b", re.IGNORECASE), "multiple sources"),
    (re.compile(r"\b(deliver|package|payload)\b", re.IGNORECASE), "package delivery"),
    (re.compile(r"\b(pick up|grab|grasp|lift)\b", re.IGNORECASE), "manipulation"),
    (re.compile(r"\b(map the|explore the)\b", re.IGNORECASE), "full environment mapping"),
    (re.compile(r"\b(land|take ?off|fly)\b", re.IGNORECASE), "aerial flight dynamics"),
)


def compile_mock(mission_text: str, scenario: Scenario) -> CompilationResult:
    """Deterministic keyword compiler used when no live key is configured.

    It intentionally implements a small, predictable subset. It is labelled as a
    mock everywhere and is not presented as model inference.
    """

    payload = default_mission_spec().model_dump()
    assumptions: list[str] = [
        "Compiled by the deterministic offline mock, not live model inference."
    ]
    warnings: list[str] = []
    unsupported: list[str] = []

    robot_match = _ROBOT_RE.search(mission_text)
    if robot_match:
        requested = int(robot_match.group(1))
        clamped = int(_clamp(requested, limits.MIN_ROBOTS, limits.MAX_ROBOTS))
        if clamped != requested:
            warnings.append(
                f"Robot count {requested} is outside the supported envelope; using {clamped}."
            )
        payload["robot_count"] = clamped
    else:
        payload["robot_count"] = scenario.default_robot_count
        _add_unique(assumptions, "Robot count not stated; using the scenario default.", 7)

    radius_match = _RADIUS_RE.search(mission_text)
    if radius_match:
        requested_radius = float(radius_match.group(1))
        radius = _clamp(
            requested_radius, limits.MIN_RING_RADIUS_M, limits.MAX_RING_RADIUS_M
        )
        if radius != requested_radius:
            warnings.append(
                f"Ring radius {requested_radius:.2f} m is outside the supported envelope; "
                f"using {radius:.2f} m."
            )
        payload["formation"]["radius"] = radius
    elif re.search(r"\b(tight|compact|small)\b", mission_text, re.IGNORECASE):
        payload["formation"]["radius"] = 1.0
        _add_unique(assumptions, "Compact ring selected from wording; radius set to 1.0 m.", 7)
    elif re.search(r"\b(wide|broad|large)\b", mission_text, re.IGNORECASE):
        payload["formation"]["radius"] = 2.0
        _add_unique(assumptions, "Wide ring selected from wording; radius set to 2.0 m.", 7)

    speed_match = _SPEED_RE.search(mission_text)
    if speed_match:
        requested_speed = float(speed_match.group(1))
        speed = _clamp(requested_speed, limits.MIN_SPEED_MPS, limits.MAX_SPEED_MPS)
        if speed != requested_speed:
            warnings.append(
                f"Requested speed {requested_speed:.2f} m/s was clamped to the safe envelope "
                f"of {speed:.2f} m/s."
            )
        payload["constraints"]["maximum_speed"] = speed
    elif re.search(r"\b(cautious|slow|gentle)\b", mission_text, re.IGNORECASE):
        payload["constraints"]["maximum_speed"] = 0.35
        _add_unique(assumptions, "Cautious wording detected; speed set to 0.35 m/s.", 7)

    separation_match = _SEPARATION_RE.search(mission_text)
    if separation_match:
        requested_separation = float(separation_match.group(1))
        separation = _clamp(
            requested_separation, limits.MIN_SEPARATION_M, limits.MAX_SEPARATION_M
        )
        if separation != requested_separation:
            warnings.append(
                f"Separation {requested_separation:.2f} m was clamped to the safe envelope."
            )
        payload["constraints"]["minimum_robot_separation"] = separation

    clearance_match = _CLEARANCE_RE.search(mission_text)
    if clearance_match:
        requested_clearance = float(clearance_match.group(1))
        clearance = _clamp(
            requested_clearance, limits.MIN_CLEARANCE_M, limits.MAX_CLEARANCE_M
        )
        if clearance != requested_clearance:
            warnings.append(
                f"Obstacle clearance {requested_clearance:.2f} m was clamped to the safe envelope."
            )
        payload["constraints"]["minimum_obstacle_clearance"] = clearance

    duration_match = _SECONDS_RE.search(mission_text)
    if duration_match:
        requested_duration = float(duration_match.group(1))
        duration = _clamp(requested_duration, limits.MIN_DURATION_S, limits.MAX_DURATION_S)
        if duration != requested_duration:
            warnings.append(
                f"Duration {requested_duration:.0f} s was clamped to the supported range."
            )
        payload["search"]["max_duration_s"] = duration

    if re.search(r"\b(locali[sz]e|locate|find)\b", mission_text, re.IGNORECASE):
        _add_unique(assumptions, "Objective interpreted as single-source localization.", 7)

    for pattern, label in _UNSUPPORTED_PATTERNS:
        if pattern.search(mission_text):
            _add_unique(unsupported, label, 8)
    if unsupported:
        warnings.append(
            "Some requested capabilities are unsupported and were not included in the mission."
        )

    count = int(payload["robot_count"])
    radius = float(payload["formation"]["radius"])
    separation = float(payload["constraints"]["minimum_robot_separation"])
    slot_arc = 2.0 * radius * math.sin(math.pi / count)
    max_separation = slot_arc * 0.9
    if separation > max_separation:
        payload["constraints"]["minimum_robot_separation"] = round(
            max(limits.MIN_SEPARATION_M, max_separation), 3
        )
        _add_unique(
            assumptions,
            f"Separation reduced to fit the ring geometry (slot arc {slot_arc:.2f} m).",
            7,
        )

    payload["assumptions"] = assumptions[:8]
    payload["unsupported_requirements"] = unsupported
    if unsupported:
        payload["clarifying_questions"] = [
            "Remove the unsupported request before approving this single-source mission."
        ]
    if not duration_match:
        payload["search"]["max_duration_s"] = limits.DEFAULT_DURATION_S

    try:
        spec = MissionSpec.model_validate(payload)
    except ValidationError as exc:
        raise ProviderError(
            422,
            "mission_infeasible",
            "The requested mission cannot be expressed within the supported envelope.",
            [
                {"loc": list(error["loc"]), "msg": error["msg"]}
                for error in exc.errors()
            ],
        ) from exc

    return CompilationResult(
        spec=spec,
        mode="mock",
        model="deterministic-keyword-mock",
        latency_ms=0.0,
        live_verified=False,
        warnings=warnings,
    )


_SYSTEM_PROMPT = """You are FieldWeaver's mission compiler.
Return exactly one JSON object. No prose, no markdown fences, no code.
The object must match the FieldWeaver MissionSpec schema exactly. Unknown fields are errors.
Never include source coordinates, field parameters, controller gains, code, shell
commands, or actuator values.
Never invent measurements or claim capabilities beyond the schema.
If the request is impossible or unsupported, still return a valid conservative
mission and list the unsupported requirement in unsupported_requirements.
Values must respect the stated bounds. Prefer conservative, safe values when the
request is ambiguous.

MissionSpec schema:
{
  "schema_version": "1.0",
  "goal": "locate_and_encircle_source",
  "robot_count": integer 3..8,
  "formation": {"type": "ring", "radius": number 0.8..2.5},
  "search": {
    "strategy": "scalar_field_source_seeking",
    "max_duration_s": number 20..180,
    "target_source_count": 1
  },
  "constraints": {
    "minimum_robot_separation": number 0.25..1.2,
    "minimum_obstacle_clearance": number 0.05..0.8,
    "maximum_speed": number 0.1..0.6,
    "avoid_restricted_regions": true
  },
  "termination": {
    "localization_tolerance": number 0.1..1.0,
    "formation_tolerance": number 0.05..0.6
  },
  "assumptions": [string, max 8, each <=300 chars],
  "clarifying_questions": [string, max 5, each <=300 chars],
  "unsupported_requirements": [string, max 8, each <=300 chars]
}
All numeric values must be finite. Do not output nulls for required fields."""


def _live_messages(mission_text: str, scenario: Scenario) -> list[dict[str, str]]:
    scene = scenario.to_public()
    user_payload = {
        "mission_text": mission_text,
        "public_scene": scene,
        "notes": [
            "The hidden source position is not available and must never be requested.",
            "Ground-truth coordinates are excluded from this prompt by construction.",
            "Only the schema above is accepted.",
        ],
    }
    return [
        {"role": "system", "content": _SYSTEM_PROMPT},
        {
            "role": "user",
            "content": "Compile this mission:\n"
            + json.dumps(user_payload, ensure_ascii=True, separators=(",", ":")),
        },
    ]


async def compile_live(
    mission_text: str,
    scenario: Scenario,
    settings: Settings | None = None,
    client: BasetenClient | None = None,
) -> CompilationResult:
    settings = settings or get_settings()
    client = client or BasetenClient(settings)
    if not settings.provider_configured:
        raise ProviderError(
            503,
            "provider_not_configured",
            "Live compilation requires BASETEN_API_KEY on the server.",
        )
    result = await client.chat(
        _live_messages(mission_text, scenario),
        temperature=0.1,
    )
    payload = extract_json_object(result.content)
    try:
        spec = MissionSpec.model_validate(payload)
    except ValidationError as exc:
        raise ProviderError(
            502,
            "model_output_invalid",
            "The live model returned a mission that failed strict schema validation.",
            [
                {"loc": list(error["loc"]), "msg": error["msg"]}
                for error in exc.errors()[:8]
            ],
        ) from exc
    return CompilationResult(
        spec=spec,
        mode="live",
        model=settings.baseten_model,
        latency_ms=result.latency_ms,
        live_verified=True,
        warnings=[],
        usage=result.usage,
    )


async def compile_mission(
    mission_text: str,
    scenario: Scenario,
    mode: ProviderMode = "auto",
    settings: Settings | None = None,
    client: BasetenClient | None = None,
) -> CompilationResult:
    settings = settings or get_settings()
    resolved = resolve_mode(mode, settings)
    if resolved == "mock":
        return compile_mock(mission_text, scenario)
    return await compile_live(mission_text, scenario, settings, client)
