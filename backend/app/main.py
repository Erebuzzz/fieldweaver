from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app import limits
from app.api.routes import router
from app.config import get_settings
from app.errors import configure_middleware, install_error_handlers

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger("fieldweaver")


@asynccontextmanager
async def lifespan(app: FastAPI):  # type: ignore[no-untyped-def]
    settings = get_settings()
    logger.info(
        "startup version=%s provider_configured=%s model=%s",
        limits.APP_VERSION,
        settings.provider_configured,
        settings.baseten_model,
    )
    yield


app = FastAPI(
    title="FieldWeaver API",
    version=limits.APP_VERSION,
    description=(
        "Mission compilation, deterministic swarm simulation, independent safety "
        "validation, and evaluation. Simulation only."
    ),
    lifespan=lifespan,
)

configure_middleware(app)
install_error_handlers(app)
app.include_router(router)
