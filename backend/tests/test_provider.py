from __future__ import annotations

import json
from dataclasses import replace
from unittest.mock import AsyncMock

import httpx
import pytest

from app.config import DEFAULT_BASE_URL, EXACT_MODEL_ID, Settings
from app.services.provider import BasetenClient, ProviderError, extract_json_object


def _settings(retries: int = 0, key: str | None = "test-key") -> Settings:
    return Settings(
        baseten_api_key=key,
        baseten_base_url=DEFAULT_BASE_URL,
        baseten_model=EXACT_MODEL_ID,
        model_timeout_s=2.0,
        model_max_retries=retries,
        max_replans=2,
        max_model_calls=2,
        cors_origins=("http://localhost:3000",),
    )


def _completion(content: str = '{"ok":true}') -> httpx.Response:
    return httpx.Response(
        200,
        json={
            "model": EXACT_MODEL_ID,
            "choices": [{"message": {"content": content}}],
            "usage": {"prompt_tokens": 4, "completion_tokens": 6, "total_tokens": 10},
        },
    )


@pytest.mark.asyncio
async def test_chat_uses_baseten_v1_chat_completions_contract() -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return _completion()

    client = BasetenClient(_settings(), transport=httpx.MockTransport(handler))
    result = await client.chat([{"role": "user", "content": "hello"}])

    assert len(requests) == 1
    assert str(requests[0].url) == f"{DEFAULT_BASE_URL}/chat/completions"
    assert requests[0].headers["authorization"] == "Bearer test-key"
    assert requests[0].read().find(EXACT_MODEL_ID.encode()) >= 0
    assert "max_tokens" not in json.loads(requests[0].read())
    assert result.content == '{"ok":true}'
    assert result.usage["total_tokens"] == 10


@pytest.mark.asyncio
async def test_chat_includes_explicit_max_tokens_when_requested() -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return _completion()

    client = BasetenClient(_settings(), transport=httpx.MockTransport(handler))
    await client.chat([{"role": "user", "content": "hello"}], max_tokens=128)

    assert json.loads(requests[0].read())["max_tokens"] == 128


@pytest.mark.asyncio
async def test_public_shared_key_fails_closed_without_budget() -> None:
    client = BasetenClient(
        replace(_settings(), public_mode=True),
        transport=httpx.MockTransport(lambda _: _completion()),
    )
    with pytest.raises(ProviderError) as raised:
        await client.chat([])
    assert raised.value.code == "shared_budget_unavailable"


@pytest.mark.asyncio
async def test_byok_does_not_consume_shared_budget(monkeypatch) -> None:
    reserve = AsyncMock()
    monkeypatch.setattr("app.services.provider.reserve_shared_request", reserve)
    client = BasetenClient(
        replace(_settings(), public_mode=True, provider_is_byok=True),
        transport=httpx.MockTransport(lambda _: _completion()),
    )
    await client.chat([])
    reserve.assert_not_awaited()


@pytest.mark.asyncio
async def test_shared_retry_reserves_each_attempt(monkeypatch) -> None:
    reserve = AsyncMock()
    monkeypatch.setattr("app.services.provider.reserve_shared_request", reserve)
    responses = iter([httpx.Response(503), _completion()])
    client = BasetenClient(
        replace(_settings(retries=1), public_mode=True),
        transport=httpx.MockTransport(lambda _: next(responses)),
        retry_backoff_s=0,
    )
    await client.chat([])
    assert reserve.await_count == 2


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("status", "code"), [(429, "shared_budget_exhausted"), (503, "shared_budget_unavailable")]
)
async def test_shared_budget_denials_fail_closed(monkeypatch, status, code) -> None:
    from app.services.provider import reserve_shared_request

    class BudgetClient:
        def __init__(self, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return False

        async def post(self, url, headers):
            return httpx.Response(status)

    monkeypatch.setattr("app.services.provider.httpx.AsyncClient", BudgetClient)
    settings = replace(
        _settings(), shared_budget_url="https://budget.example", shared_budget_token="test"
    )
    with pytest.raises(ProviderError) as raised:
        await reserve_shared_request(settings)
    assert raised.value.code == code


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("status", "code"),
    [
        (401, "provider_unauthorized"),
        (403, "provider_unauthorized"),
        (429, "provider_rate_limited"),
    ],
)
async def test_chat_maps_auth_and_rate_limit_errors(status: int, code: str) -> None:
    transport = httpx.MockTransport(lambda request: httpx.Response(status))
    client = BasetenClient(_settings(), transport=transport)

    with pytest.raises(ProviderError) as raised:
        await client.chat([])

    assert raised.value.code == code


@pytest.mark.asyncio
async def test_chat_retries_a_transient_rate_limit() -> None:
    statuses = iter([429, 200])
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        status = next(statuses)
        return _completion() if status == 200 else httpx.Response(status)

    client = BasetenClient(
        _settings(retries=1),
        transport=httpx.MockTransport(handler),
        retry_backoff_s=0,
    )
    result = await client.chat([])

    assert calls == 2
    assert result.content == '{"ok":true}'


@pytest.mark.asyncio
async def test_chat_maps_timeout_and_malformed_response() -> None:
    def timeout_handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("timed out", request=request)

    timeout_client = BasetenClient(_settings(), transport=httpx.MockTransport(timeout_handler))
    with pytest.raises(ProviderError) as timeout:
        await timeout_client.chat([])
    assert timeout.value.status_code == 504
    assert timeout.value.code == "provider_timeout"

    malformed_client = BasetenClient(
        _settings(),
        transport=httpx.MockTransport(lambda request: httpx.Response(200, json={"choices": []})),
    )
    with pytest.raises(ProviderError) as malformed:
        await malformed_client.chat([])
    assert malformed.value.code == "provider_bad_response"


@pytest.mark.asyncio
async def test_chat_reports_when_reasoning_uses_the_output_budget() -> None:
    response = httpx.Response(
        200,
        json={"choices": [{"message": {"content": ""}, "finish_reason": "length"}]},
    )
    client = BasetenClient(_settings(), transport=httpx.MockTransport(lambda request: response))

    with pytest.raises(ProviderError) as raised:
        await client.chat([])

    assert raised.value.code == "provider_bad_response"
    assert "output token limit" in raised.value.message


@pytest.mark.asyncio
async def test_chat_requires_server_key_before_network_access() -> None:
    client = BasetenClient(
        _settings(key=None),
        transport=httpx.MockTransport(lambda req: _completion()),
    )

    with pytest.raises(ProviderError) as raised:
        await client.chat([])

    assert raised.value.status_code == 503
    assert raised.value.code == "provider_not_configured"


@pytest.mark.parametrize(
    ("content", "expected"),
    [
        ('{"schema_version":"1.0"}', {"schema_version": "1.0"}),
        ('```json\n{"schema_version":"1.0"}\n```', {"schema_version": "1.0"}),
    ],
)
def test_extract_json_object_accepts_object_and_fence(content: str, expected: dict) -> None:
    assert extract_json_object(content) == expected


def test_extract_json_object_rejects_non_object_json() -> None:
    with pytest.raises(ProviderError) as raised:
        extract_json_object('[{"unsafe":"value"}]')
    assert raised.value.code == "model_output_invalid"
