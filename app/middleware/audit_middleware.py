"""Audit trail middleware — logs write operations to Neo4j."""

from __future__ import annotations

import structlog
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.utils.helpers import generate_id, utc_now

logger = structlog.get_logger("audit")

# HTTP methods that mutate data
_WRITE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}


class AuditMiddleware(BaseHTTPMiddleware):
    """Record an audit log entry for every write operation.

    Audit entries are logged via structlog (can be shipped to any sink).
    For high-volume production use, consider writing to a dedicated
    audit log store asynchronously.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        response: Response = await call_next(request)

        if request.method in _WRITE_METHODS:
            user_id = ""
            role = ""
            if hasattr(request.state, "user"):
                user_id = getattr(request.state, "user", {}).get("user_id", "")
                role = getattr(request.state, "user", {}).get("role", "")

            logger.info(
                "audit.write_operation",
                audit_id=generate_id(),
                timestamp=utc_now(),
                user_id=user_id,
                role=role,
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                request_id=getattr(request.state, "request_id", ""),
                client=request.client.host if request.client else "unknown",
            )

        return response
