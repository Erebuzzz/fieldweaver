from __future__ import annotations

import logging
import time
import uuid
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import get_settings

logger = logging.getLogger("fieldweaver")


class FieldWeaverError(Exception):
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


def _request_id(request: Request) -> str:
    return getattr(request.state, "request_id", "unknown")


def error_response(
    request: Request,
    status_code: int,
    code: str,
    message: str,
    details: Any | None = None,
) -> JSONResponse:
    request_id = _request_id(request)
    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "code": code,
                "message": message,
                "details": details,
                "request_id": request_id,
            }
        },
        headers={"X-Request-ID": request_id},
    )


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):  # type: ignore[no-untyped-def]
        request_id = uuid.uuid4().hex
        request.state.request_id = request_id
        started = time.perf_counter()
        response = await call_next(request)
        elapsed_ms = (time.perf_counter() - started) * 1000.0
        response.headers["X-Request-ID"] = request_id
        logger.info(
            "request method=%s path=%s status=%s duration_ms=%.1f request_id=%s",
            request.method,
            request.url.path,
            response.status_code,
            elapsed_ms,
            request_id,
        )
        return response


def install_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(FieldWeaverError)
    async def handle_app_error(request: Request, exc: FieldWeaverError) -> JSONResponse:
        return error_response(request, exc.status_code, exc.code, exc.message, exc.details)

    @app.exception_handler(StarletteHTTPException)
    async def handle_http_error(
        request: Request, exc: StarletteHTTPException
    ) -> JSONResponse:
        code = "not_found" if exc.status_code == 404 else "http_error"
        message = str(exc.detail) if exc.detail else "HTTP request failed."
        return error_response(request, exc.status_code, code, message)

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        details = [
            {
                "loc": list(item.get("loc", [])),
                "msg": item.get("msg", "invalid value"),
                "type": item.get("type", "value_error"),
            }
            for item in exc.errors()
        ]
        return error_response(
            request,
            422,
            "invalid_request",
            "Request validation failed.",
            details,
        )

    @app.exception_handler(Exception)
    async def handle_unexpected(request: Request, exc: Exception) -> JSONResponse:
        logger.exception(
            "unhandled_error request_id=%s path=%s",
            _request_id(request),
            request.url.path,
        )
        return error_response(
            request,
            500,
            "internal_error",
            "An unexpected server error occurred. Check the server log with the request ID.",
        )


def configure_middleware(app: FastAPI) -> None:
    settings = get_settings()
    app.add_middleware(RequestContextMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.cors_origins),
        allow_credentials=False,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Content-Type", "X-Request-ID"],
        expose_headers=["X-Request-ID"],
    )
