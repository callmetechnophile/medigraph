"""Clerk JWT token verification and user extraction."""

from __future__ import annotations

from typing import Any

import jwt
from jwt import PyJWKClient

import structlog

from app.config import get_settings

logger = structlog.get_logger(__name__)

# ---------------------------------------------------------------------------
# JWKS Client (cached, thread-safe)
# ---------------------------------------------------------------------------
_jwks_client: PyJWKClient | None = None


def _get_jwks_client() -> PyJWKClient:
    """Lazily initialise and return the JWKS client."""
    global _jwks_client
    if _jwks_client is None:
        settings = get_settings()
        if not settings.clerk_jwks_url:
            raise RuntimeError("CLERK_JWKS_URL is not configured.")
        _jwks_client = PyJWKClient(settings.clerk_jwks_url, cache_keys=True)
    return _jwks_client


def verify_clerk_token(token: str) -> dict[str, Any]:
    """Verify a Clerk-issued JWT and return the decoded payload.

    Raises:
        jwt.ExpiredSignatureError: Token has expired.
        jwt.InvalidTokenError: Token is invalid or tampered.
        ValueError: JWKS URL not configured.
    """
    client = _get_jwks_client()
    signing_key = client.get_signing_key_from_jwt(token)

    payload = jwt.decode(
        token,
        signing_key.key,
        algorithms=["RS256"],
        options={
            "verify_exp": True,
            "verify_nbf": True,
            "verify_aud": False,  # Clerk doesn't always set aud
        },
    )
    logger.debug("clerk.token.verified", user_id=payload.get("sub"))
    return payload


def extract_user_id(payload: dict[str, Any]) -> str:
    """Extract the Clerk user ID from a decoded token payload."""
    return payload.get("sub", "")


def extract_user_role(payload: dict[str, Any]) -> str:
    """Extract the user role from token metadata.

    Clerk stores custom data in `metadata` (via JWT Templates)
    or `org_role` (via Organizations).
    """
    # Check custom metadata first
    metadata = payload.get("metadata", {})
    if isinstance(metadata, dict) and "role" in metadata:
        return metadata["role"]

    # Fall back to org_role
    org_role = payload.get("org_role", "")
    if org_role:
        return org_role

    return "patient"  # default role


def extract_user_metadata(payload: dict[str, Any]) -> dict[str, Any]:
    """Extract all user metadata from the token."""
    return {
        "user_id": payload.get("sub", ""),
        "role": extract_user_role(payload),
        "org_id": payload.get("org_id", ""),
        "org_role": payload.get("org_role", ""),
        "metadata": payload.get("metadata", {}),
        "issuer": payload.get("iss", ""),
        "issued_at": payload.get("iat"),
        "expires_at": payload.get("exp"),
    }
