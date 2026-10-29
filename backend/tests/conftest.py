from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.config import reset_settings_cache
from app.main import app


@pytest.fixture(autouse=True)
def clean_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("BASETEN_API_KEY", raising=False)
    monkeypatch.delenv("FIELDWEAVER_MAX_REPLANS", raising=False)
    monkeypatch.delenv("FIELDWEAVER_MAX_MODEL_CALLS", raising=False)
    reset_settings_cache()
    yield
    reset_settings_cache()


@pytest.fixture()
def client() -> TestClient:
    if hasattr(app.state, "latest_run"):
        del app.state.latest_run
    with TestClient(app) as test_client:
        yield test_client
