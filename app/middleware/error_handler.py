"""Global exception handlers for consistent error responses."""

from __future__ import annotations

import structlog
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from neo4j.exceptions import (
    AuthError,
    ServiceUnavailable,
)

from app.utils.helpers import utc_now

logger = structlog.get_logger("error")


def register_exception_handlers(app: FastAPI) -> None:
    """Register all global exception handlers on the FastAPI app."""

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "detail": exc.detail,
                "error_code": f"HTTP_{exc.status_code}",
                "timestamp": utc_now(),
            },
        )

    @app.exception_handler(ServiceUnavailable)
    async def neo4j_unavailable_handler(request: Request, exc: ServiceUnavailable):
        logger.error("neo4j.service_unavailable", error=str(exc))
        return JSONResponse(
            status_code=503,
            content={
                "detail": "Database service is temporarily unavailable. Please retry.",
                "error_code": "DATABASE_UNAVAILABLE",
                "timestamp": utc_now(),
            },
        )

    @app.exception_handler(AuthError)
    async def neo4j_auth_handler(request: Request, exc: AuthError):
        logger.error("neo4j.auth_error", error=str(exc))
        return JSONResponse(
            status_code=503,
            content={
                "detail": "Database authentication error.",
                "error_code": "DATABASE_AUTH_ERROR",
                "timestamp": utc_now(),
            },
        )

    @app.exception_handler(ValueError)
    async def value_error_handler(request: Request, exc: ValueError):
        logger.warning("validation.error", error=str(exc))
        return JSONResponse(
            status_code=422,
            content={
                "detail": str(exc),
                "error_code": "VALIDATION_ERROR",
                "timestamp": utc_now(),
            },
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception):
        logger.error(
            "unhandled_exception",
            error=str(exc),
            error_type=type(exc).__name__,
            path=request.url.path,
        )
        return JSONResponse(
            status_code=500,
            content={
                "detail": "An internal server error occurred.",
                "error_code": "INTERNAL_ERROR",
                "timestamp": utc_now(),
            },
        )
