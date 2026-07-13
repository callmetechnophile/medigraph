"""Input validation utilities."""

from __future__ import annotations

import re
from datetime import datetime

from fastapi import HTTPException


def validate_date(value: str, field_name: str = "date") -> str:
    """Validate a YYYY-MM-DD date string."""
    if not value:
        return value
    try:
        datetime.strptime(value, "%Y-%m-%d")
        return value
    except ValueError:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid {field_name} format. Expected YYYY-MM-DD, got '{value}'.",
        )


def validate_datetime(value: str, field_name: str = "datetime") -> str:
    """Validate an ISO-8601 datetime string."""
    if not value:
        return value
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
        return value
    except ValueError:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid {field_name} format. Expected ISO-8601, got '{value}'.",
        )


def validate_email(value: str) -> str:
    """Basic email format validation."""
    if not value:
        return value
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    if not re.match(pattern, value):
        raise HTTPException(
            status_code=422,
            detail=f"Invalid email format: '{value}'.",
        )
    return value


def validate_phone(value: str) -> str:
    """Basic phone number validation (digits, +, -, spaces)."""
    if not value:
        return value
    cleaned = re.sub(r"[\s\-]", "", value)
    if not re.match(r"^\+?\d{7,15}$", cleaned):
        raise HTTPException(
            status_code=422,
            detail=f"Invalid phone number: '{value}'.",
        )
    return value


def validate_positive_int(value: int, field_name: str = "value") -> int:
    """Ensure a value is a non-negative integer."""
    if value < 0:
        raise HTTPException(
            status_code=422,
            detail=f"{field_name} must be non-negative, got {value}.",
        )
    return value


def validate_percentage(value: float, field_name: str = "value") -> float:
    """Ensure a value is between 0 and 100."""
    if not (0.0 <= value <= 100.0):
        raise HTTPException(
            status_code=422,
            detail=f"{field_name} must be between 0 and 100, got {value}.",
        )
    return value


def validate_date_range(start: str, end: str) -> tuple[str, str]:
    """Validate that start_date <= end_date."""
    if not start or not end:
        return start, end
    start_dt = datetime.strptime(start, "%Y-%m-%d")
    end_dt = datetime.strptime(end, "%Y-%m-%d")
    if start_dt > end_dt:
        raise HTTPException(
            status_code=422,
            detail=f"start_date ({start}) must not be after end_date ({end}).",
        )
    return start, end
