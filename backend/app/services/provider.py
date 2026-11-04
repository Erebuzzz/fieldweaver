"""Baseten OpenAI-compatible client with explicit error mapping.

This module is the only place that reads the API key or performs live HTTP
calls. It never logs headers, keys, or raw prompt content. Every failure is
mapped to an application error code so callers can decide whether to abort.
"""

from __future__ import annotations

import asyncio
import json
import time
from dataclasses import dataclass, field
from typing import Any

import httpx

from app.config import Settings, get_settings


class ProviderError(Exception):
    def __init__(
        self,
        status_code: int,
        code: str,
        message: str,
        details: Any | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message
        self.details = details


@dataclass(frozen=True)
class ChatResult:
    content: str
    latency_ms: float
    model: str
    usage: dict[str, int] = field(default_factory=dict)
    upstream_request_id: str | None = None


class BasetenClient:
    """Thin async client for the documented /v1/chat/completions endpoint."""

    def __init__(
        self,
        settings: Settings | None = None,
        transport: httpx.AsyncBaseTransport | None = None,
        retry_backoff_s: float = 0.2,
    ) -> None:
        self.settings = settings or get_settings()
        self._transport = transport
        self._retry_backoff_s = retry_backoff_s

    @property
    def configured(self) -> bool:
        return self.settings.provider_configured

    async def chat(
        self,
        messages: list[dict[str, str]],
        *,
        max_tokens: int | None = None,
        temperature: float = 0.1,
    ) -> ChatResult:
        if not self.settings.baseten_api_key:
            raise ProviderError(
                503,
                "provider_not_configured",
                "Live inference requires BASETEN_API_KEY on the server. "
                "Use the explicit offline mock or configure the key.",
            )

        payload = {
            "model": self.settings.baseten_model,
            "messages": messages,
            "temperature": temperature,
        }
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens
        headers = {
            "Authorization": f"Bearer {self.settings.baseten_api_key}",
            "Content-Type": "application/json",
        }
        attempts = self.settings.model_max_retries + 1
        started = time.perf_counter()

        async with httpx.AsyncClient(
            base_url=f"{self.settings.baseten_base_url.rstrip('/')}/",
            timeout=self.settings.model_timeout_s,
            transport=self._transport,
        ) as client:
            for attempt in range(attempts):
                if self.settings.public_mode and not self.settings.provider_is_byok:
                    await reserve_shared_request(self.settings)
                try:
                    response = await client.post("chat/completions", json=payload, headers=headers)
                except httpx.TimeoutException as exc:
                    if attempt < attempts - 1:
                        await asyncio.sleep(self._retry_backoff_s * (attempt + 1))
                        continue
                    raise ProviderError(
                        504,
                        "provider_timeout",
                        "The live model request timed out. The run was not started.",
                    ) from exc
                except httpx.HTTPError as exc:
                    raise ProviderError(
                        502,
                        "provider_unreachable",
                        "The live model endpoint could not be reached.",
                    ) from exc

                if response.status_code in {429, 500, 502, 503, 504} and attempt < attempts - 1:
                    await asyncio.sleep(self._retry_backoff_s * (attempt + 1))
                    continue
                if response.status_code == 401 or response.status_code == 403:
                    raise ProviderError(
                        502,
                        "provider_unauthorized",
                        "The live model endpoint rejected the configured credentials.",
                    )
                if response.status_code == 429:
                    raise ProviderError(
                        502,
                        "provider_rate_limited",
                        "The live model endpoint rate-limited the request.",
                    )
                if response.status_code >= 400:
                    raise ProviderError(
                        502,
                        "provider_error",
                        f"The live model endpoint returned HTTP {response.status_code}.",
                    )

                try:
                    body = response.json()
                    choice = body["choices"][0]
                    content = choice["message"]["content"]
                    finish_reason = choice.get("finish_reason")
                except (ValueError, KeyError, IndexError, TypeError) as exc:
                    raise ProviderError(
                        502,
                        "provider_bad_response",
                        "The live model response did not match the Chat Completions shape.",
                    ) from exc
                if not isinstance(content, str) or not content.strip():
                    message = (
                        "The live model reached its output token limit before returning content."
                        if finish_reason == "length"
                        else "The live model returned empty content."
                    )
                    raise ProviderError(
                        502,
                        "provider_bad_response",
                        message,
                    )

                usage_raw = body.get("usage") if isinstance(body, dict) else None
                usage: dict[str, int] = {}
                if isinstance(usage_raw, dict):
                    for key in ("prompt_tokens", "completion_tokens", "total_tokens"):
                        value = usage_raw.get(key)
                        if isinstance(value, int):
                            usage[key] = value

                latency_ms = (time.perf_counter() - started) * 1000.0
                upstream_id = response.headers.get("x-request-id")
                return ChatResult(
                    content=content,
                    latency_ms=latency_ms,
                    model=str(body.get("model") or self.settings.baseten_model),
                    usage=usage,
                    upstream_request_id=upstream_id,
                )

        raise ProviderError(502, "provider_error", "The live model request failed.")


async def reserve_shared_request(settings: Settings) -> None:
    unavailable = "The shared model is temporarily unavailable. Use your own key or offline mode."
    if not settings.shared_budget_url or not settings.shared_budget_token:
        raise ProviderError(
            503,
            "shared_budget_unavailable",
            unavailable,
        )
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(
                settings.shared_budget_url,
                headers={"Authorization": f"Bearer {settings.shared_budget_token}"},
            )
    except httpx.HTTPError as exc:
        raise ProviderError(
            503,
            "shared_budget_unavailable",
            unavailable,
        ) from exc
    if response.status_code == 429:
        raise ProviderError(
            429,
            "shared_budget_exhausted",
            "The daily shared model request limit has been reached. "
            "Use your own key or offline mode.",
        )
    if response.status_code != 200:
        raise ProviderError(
            503,
            "shared_budget_unavailable",
            unavailable,
        )


def extract_json_object(content: str) -> dict[str, Any]:
    """Parse a JSON object from model text, tolerating code fences.

    This is intentionally strict about the result being a single object. It does
    not attempt to repair content or execute anything the model returned.
    """

    text = content.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines).strip()

    candidates = [text]
    first = text.find("{")
    last = text.rfind("}")
    if first != -1 and last > first:
        candidates.append(text[first : last + 1])

    for candidate in candidates:
        try:
            parsed = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict):
            return parsed
        raise ProviderError(
            502,
            "model_output_invalid",
            "The model returned JSON that is not an object.",
        )
    raise ProviderError(
        502,
        "model_output_invalid",
        "The model response did not contain a parseable JSON object.",
    )
