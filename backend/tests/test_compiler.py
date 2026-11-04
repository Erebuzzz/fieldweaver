from __future__ import annotations

import json
from dataclasses import replace

import httpx
import pytest

from app.config import DEFAULT_BASE_URL, EXACT_MODEL_ID, Settings
from app.schemas import default_mission_spec
from app.services.compiler import compile_live, compile_mission, compile_mock, resolve_mode
from app.services.provider import BasetenClient, ProviderError
from app.simulation.scenario import OPEN_FIELD


def _settings(key: str | None = "test-key") -> Settings:
    return Settings(
        baseten_api_key=key,
        baseten_base_url=DEFAULT_BASE_URL,
        baseten_model=EXACT_MODEL_ID,
        model_timeout_s=2.0,
        model_max_retries=0,
        max_replans=2,
        max_model_calls=2,
        cors_origins=("http://localhost:3000",),
    )


def _response(content: str) -> httpx.Response:
    return httpx.Response(
        200,
        json={
            "model": EXACT_MODEL_ID,
            "choices": [{"message": {"content": content}}],
            "usage": {"prompt_tokens": 9, "completion_tokens": 12, "total_tokens": 21},
        },
    )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "name,url",
    [
        ("meta", "https://api.meta.ai/v1"),
        ("fireworks", "https://api.fireworks.ai/inference/v1"),
    ],
)
async def test_alternative_provider_chat_contract(name: str, url: str) -> None:
    requests = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return _response(default_mission_spec().model_dump_json())

    settings = replace(
        _settings(), provider_name=name, baseten_base_url=url, baseten_model="test-model"
    )
    result = await compile_live(
        "Locate one source.",
        OPEN_FIELD,
        settings,
        BasetenClient(settings, transport=httpx.MockTransport(handler)),
    )
    assert str(requests[0].url) == f"{url}/chat/completions"
    assert requests[0].headers["authorization"] == "Bearer test-key"
    assert json.loads(requests[0].content)["model"] == "test-model"
    assert result.to_public()["provider"]["name"] == name


def test_mock_compiler_clamps_values_and_reports_unsupported_work() -> None:
    result = compile_mock(
        "Find two sources with 99 robots in a ring radius of 5 m after 1000 seconds.",
        OPEN_FIELD,
    )

    assert result.mode == "mock"
    assert result.live_verified is False
    assert result.spec.robot_count == 8
    assert result.spec.formation.radius == 2.5
    assert result.spec.search.max_duration_s == 180
    assert result.spec.unsupported_requirements == ["multiple sources"]
    assert result.spec.clarifying_questions
    assert result.warnings


def test_mock_mode_does_not_claim_live_when_key_is_present() -> None:
    result = compile_mock("Locate one source with a safe ring.", OPEN_FIELD)

    assert result.mode == "mock"
    assert result.model == "deterministic-keyword-mock"
    assert result.to_public()["provider"]["name"] == "mock"


def test_resolve_live_mode_requires_key() -> None:
    with pytest.raises(ProviderError) as raised:
        resolve_mode("live", _settings(key=None))
    assert raised.value.code == "provider_not_configured"


@pytest.mark.asyncio
async def test_live_compiler_validates_output_and_sends_public_scene_only() -> None:
    payload = default_mission_spec().model_dump(mode="json")
    seen: list[dict] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(json.loads(request.read()))
        return _response(json.dumps(payload))

    settings = _settings()
    client = BasetenClient(settings, transport=httpx.MockTransport(handler))
    result = await compile_live("Locate one source safely.", OPEN_FIELD, settings, client)

    assert result.mode == "live"
    assert result.live_verified is True
    assert result.model == EXACT_MODEL_ID
    assert result.usage["total_tokens"] == 21
    assert seen[0]["max_tokens"] == 4096
    serialized = json.dumps(seen[0]["messages"])
    assert '"source":' not in serialized
    assert "7.0" not in serialized
    assert "5.0" not in serialized


@pytest.mark.asyncio
async def test_live_compiler_rejects_unknown_model_fields() -> None:
    payload = default_mission_spec().model_dump(mode="json")
    payload["controller_gains"] = {"speed": 100}
    settings = _settings()
    client = BasetenClient(
        settings,
        transport=httpx.MockTransport(lambda request: _response(json.dumps(payload))),
    )

    with pytest.raises(ProviderError) as raised:
        await compile_live("Locate one source.", OPEN_FIELD, settings, client)

    assert raised.value.status_code == 502
    assert raised.value.code == "model_output_invalid"


@pytest.mark.asyncio
async def test_auto_mode_uses_explicit_mock_without_key() -> None:
    result = await compile_mission(
        "Locate one source.", OPEN_FIELD, mode="auto", settings=_settings(key=None)
    )
    assert result.mode == "mock"
    assert result.live_verified is False


@pytest.mark.parametrize(
    "mission_text",
    [
        "Find one source with separation of 1.4 m.",
        "Find one source with obstacle clearance of 1.0 m.",
        "Find one source with maximum speed of 0.05 m/s.",
        "Find one source with 8 robots, ring radius of 0.8 m and separation of 1.0 m.",
    ],
)
def test_mock_compiler_rejects_requests_that_would_relax_safety(mission_text: str) -> None:
    with pytest.raises(ProviderError) as raised:
        compile_mock(mission_text, OPEN_FIELD)
    assert raised.value.code in {"mission_constraint_not_met", "mission_infeasible"}


@pytest.mark.asyncio
async def test_live_compiler_rejects_weaker_explicit_safety_constraint() -> None:
    payload = default_mission_spec().model_dump(mode="json")
    settings = _settings()
    client = BasetenClient(
        settings,
        transport=httpx.MockTransport(lambda request: _response(json.dumps(payload))),
    )
    with pytest.raises(ProviderError) as raised:
        await compile_live(
            "Locate one source with separation of 0.8 m.", OPEN_FIELD, settings, client
        )
    assert raised.value.code == "mission_constraint_not_met"
