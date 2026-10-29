from __future__ import annotations

from fastapi.testclient import TestClient


def test_health_returns_versioned_secret_free_payload(client: TestClient) -> None:
    response = client.get("/api/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["api_version"] == "v1"
    assert body["mode"] == "offline_mock"
    assert body["provider"]["name"] == "baseten"
    assert body["provider"]["model"] == "meta-models/muse-spark-open-1026"
    assert body["provider"]["configured"] is False
    assert body["provider"]["mode"] == "mock"
    assert body["simulation"]["dt_s"] == 0.1
    assert body["live_provider_verified"] is False
    assert body["request_id"]
    assert body["request_id"] == response.headers["x-request-id"]
    serialized = response.text.lower()
    assert "api_key" not in serialized
    assert "authorization" not in serialized
    assert "bearer" not in serialized


def test_health_reflects_configured_key_without_leaking_it(
    client: TestClient, monkeypatch
) -> None:
    from app.config import reset_settings_cache
    from app.main import app

    monkeypatch.setenv("BASETEN_API_KEY", "test-placeholder-value")
    reset_settings_cache()
    with TestClient(app) as local_client:
        response = local_client.get("/api/health")
    assert response.status_code == 200
    body = response.json()
    assert body["mode"] == "live_configured"
    assert body["provider"]["configured"] is True
    assert body["provider"]["mode"] == "live"
    assert "test-placeholder-value" not in response.text
    assert body["live_provider_verified"] is False
    reset_settings_cache()


def test_root_route(client: TestClient) -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["name"] == "FieldWeaver"
    assert response.json()["version"]


def test_perception_disabled_is_explicit(client: TestClient) -> None:
    response = client.post("/api/scenes/segment")
    assert response.status_code == 503
    error = response.json()["error"]
    assert error["code"] == "perception_disabled"
    assert error["request_id"] == response.headers["x-request-id"]
    assert "do not" not in response.text.lower()


def test_unknown_route_uses_error_envelope(client: TestClient) -> None:
    response = client.get("/api/does-not-exist")
    assert response.status_code == 404
    error = response.json()["error"]
    assert error["code"] == "not_found"
    assert error["request_id"] == response.headers["x-request-id"]
