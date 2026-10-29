"""Runtime configuration. Secrets are read from the environment and never exposed."""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

from app import limits

ROOT_DIR = Path(__file__).resolve().parents[2]
load_dotenv(ROOT_DIR / ".env", override=False)

EXACT_MODEL_ID = "meta-models/muse-spark-open-1026"
DEFAULT_BASE_URL = "https://inference.baseten.co/v1"


@dataclass(frozen=True)
class Settings:
    baseten_api_key: str | None
    baseten_base_url: str
    baseten_model: str
    model_timeout_s: float
    model_max_retries: int
    max_replans: int
    max_model_calls: int
    cors_origins: tuple[str, ...]

    @property
    def provider_configured(self) -> bool:
        return bool(self.baseten_api_key)

    def public_provider(self) -> dict[str, object]:
        return {
            "name": "baseten",
            "model": self.baseten_model,
            "configured": self.provider_configured,
            "mode": "live" if self.provider_configured else "mock",
        }


def _bounded_int(name: str, default: int, low: int, high: int) -> int:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    try:
        value = int(raw)
    except ValueError:
        return default
    return max(low, min(high, value))


def _bounded_float(name: str, default: float, low: float, high: float) -> float:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    try:
        value = float(raw)
    except ValueError:
        return default
    if value != value:  # NaN
        return default
    return max(low, min(high, value))


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    key = os.getenv("BASETEN_API_KEY")
    key = key.strip() if key and key.strip() else None
    origins = os.getenv(
        "FIELDWEAVER_CORS_ORIGINS",
        "http://localhost:3000,http://127.0.0.1:3000",
    )
    return Settings(
        baseten_api_key=key,
        baseten_base_url=os.getenv("BASETEN_BASE_URL", DEFAULT_BASE_URL).rstrip("/"),
        baseten_model=os.getenv("BASETEN_MODEL", EXACT_MODEL_ID).strip() or EXACT_MODEL_ID,
        model_timeout_s=_bounded_float(
            "FIELDWEAVER_MODEL_TIMEOUT_S", limits.MODEL_TIMEOUT_S, 2.0, 120.0
        ),
        model_max_retries=_bounded_int(
            "FIELDWEAVER_MODEL_MAX_RETRIES", limits.MODEL_MAX_RETRIES, 0, 2
        ),
        max_replans=_bounded_int(
            "FIELDWEAVER_MAX_REPLANS", limits.DEFAULT_MAX_REPLANS, 0, 4
        ),
        max_model_calls=_bounded_int(
            "FIELDWEAVER_MAX_MODEL_CALLS",
            limits.DEFAULT_MAX_MODEL_CALLS,
            0,
            limits.MAX_MODEL_CALLS_CEILING,
        ),
        cors_origins=tuple(origin.strip() for origin in origins.split(",") if origin.strip()),
    )


def reset_settings_cache() -> None:
    """Test helper; forces environment re-read."""

    get_settings.cache_clear()
