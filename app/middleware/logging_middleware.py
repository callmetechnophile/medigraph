"""Structured request/response logging middleware using structlog."""

from __future__ import annotations

import time
import uuid

import structlog
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = structlog.get_logger("api")


class LoggingMiddleware(BaseHTTPMiddleware):
    """Log every HTTP request with timing, status code, and a correlation ID."""

    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = str(uuid.uuid4())[:8]
        request.state.request_id = request_id

        start = time.perf_counter()

        log = logger.bind(
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            query=str(request.query_params),
            client=request.client.host if request.client else "unknown",
        )
        log.info("request.start")

        try:
            response: Response = await call_next(request)
        except Exception as exc:
            duration_ms = (time.perf_counter() - start) * 1000
            log.error(
                "request.error",
                duration_ms=round(duration_ms, 2),
                error=str(exc),
            )
            raise

        duration_ms = (time.perf_counter() - start) * 1000
        log.info(
            "request.complete",
            status_code=response.status_code,
            duration_ms=round(duration_ms, 2),
        )

        response.headers["X-Request-ID"] = request_id
        return response
