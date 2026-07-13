"""FastAPI dependencies for authentication and role-based access control."""

from __future__ import annotations

from typing import Any

import jwt
import structlog
from fastapi import Depends, HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.auth.clerk_auth import (
    extract_user_id,
    extract_user_metadata,
    extract_user_role,
    verify_clerk_token,
)

logger = structlog.get_logger(__name__)

# ---------------------------------------------------------------------------
# Bearer token extractor
# ---------------------------------------------------------------------------
_bearer_scheme = HTTPBearer(auto_error=False)


# ---------------------------------------------------------------------------
# Core dependency — get_current_user
# ---------------------------------------------------------------------------
async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Security(_bearer_scheme),
) -> dict[str, Any]:
    """Verify Clerk JWT and return user metadata.

    This is the primary authentication dependency. Attach it to any route
    that requires a logged-in user.
    """
    if credentials is None:
        raise HTTPException(status_code=401, detail="Missing authorization token.")

    token = credentials.credentials
    try:
        payload = verify_clerk_token(token)
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired.")
    except jwt.InvalidTokenError as exc:
        logger.warning("auth.invalid_token", error=str(exc))
        raise HTTPException(status_code=401, detail="Invalid authentication token.")
    except Exception as exc:
        logger.error("auth.verification_failed", error=str(exc))
        raise HTTPException(status_code=401, detail="Authentication failed.")

    return extract_user_metadata(payload)


async def get_current_user_id(
    user: dict[str, Any] = Depends(get_current_user),
) -> str:
    """Convenience dependency that returns only the user ID."""
    return user["user_id"]


# ---------------------------------------------------------------------------
# Role-based access control
# ---------------------------------------------------------------------------
class RoleChecker:
    """Callable dependency that enforces role-based access.

    Usage::

        allow_admins = RoleChecker("hospital_admin", "system_admin")

        @router.get("/admin")
        async def admin_route(user=Depends(allow_admins)):
            ...
    """

    def __init__(self, *allowed_roles: str):
        self.allowed_roles = set(allowed_roles)

    async def __call__(
        self,
        user: dict[str, Any] = Depends(get_current_user),
    ) -> dict[str, Any]:
        role = user.get("role", "")
        if role not in self.allowed_roles:
            logger.warning(
                "auth.insufficient_role",
                user_id=user.get("user_id"),
                role=role,
                required=list(self.allowed_roles),
            )
            raise HTTPException(
                status_code=403,
                detail=f"Insufficient permissions. Required roles: {', '.join(sorted(self.allowed_roles))}",
            )
        return user


def require_roles(*roles: str):
    """Factory that creates a Depends-compatible role checker.

    Usage::

        @router.get("/admin")
        async def admin_route(user=Depends(require_roles("system_admin"))):
            ...
    """
    checker = RoleChecker(*roles)
    return Depends(checker)


# ---------------------------------------------------------------------------
# Pre-built role dependencies
# ---------------------------------------------------------------------------
require_patient = RoleChecker(
    "patient", "doctor", "hospital_staff", "hospital_admin", "district_admin", "system_admin"
)
require_doctor = RoleChecker(
    "doctor", "hospital_admin", "system_admin"
)
require_hospital_staff = RoleChecker(
    "hospital_staff", "hospital_admin", "system_admin"
)
require_hospital_admin = RoleChecker(
    "hospital_admin", "system_admin"
)
require_district_admin = RoleChecker(
    "district_admin", "system_admin"
)
require_system_admin = RoleChecker(
    "system_admin"
)
