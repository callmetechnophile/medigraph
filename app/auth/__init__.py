"""Authentication package."""

from app.auth.clerk_auth import verify_clerk_token, extract_user_id, extract_user_role
from app.auth.dependencies import (
    get_current_user,
    get_current_user_id,
    RoleChecker,
    require_roles,
    require_patient,
    require_doctor,
    require_hospital_staff,
    require_hospital_admin,
    require_district_admin,
    require_system_admin,
)

__all__ = [
    "verify_clerk_token",
    "extract_user_id",
    "extract_user_role",
    "get_current_user",
    "get_current_user_id",
    "RoleChecker",
    "require_roles",
    "require_patient",
    "require_doctor",
    "require_hospital_staff",
    "require_hospital_admin",
    "require_district_admin",
    "require_system_admin",
]
