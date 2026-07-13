"""Attendance endpoints — Staff check-in, check-out, summaries."""

from __future__ import annotations

from typing import Any
from fastapi import APIRouter, Depends, Query, Path
from neo4j import AsyncDriver

from app.database.connection import get_driver
from app.repositories import AttendanceRepository, NotificationRepository
from app.services import AttendanceService
from app.schemas import (
    AttendanceCheckIn,
    AttendanceCheckOut,
    AttendanceResponse,
    AttendanceSummary,
    PaginatedResponse,
)
from app.auth.dependencies import require_roles

router = APIRouter(tags=["Attendance"])

def get_attendance_service(driver: AsyncDriver = Depends(get_driver)) -> AttendanceService:
    att_repo = AttendanceRepository(driver)
    notif_repo = NotificationRepository(driver)
    return AttendanceService(att_repo, notif_repo)

@router.post("/hospitals/{hospital_id}/attendance/check-in", response_model=AttendanceResponse)
async def check_in(
    data: AttendanceCheckIn,
    hospital_id: str = Path(...),
    service: AttendanceService = Depends(get_attendance_service),
    user: dict[str, Any] = Depends(require_roles("hospital_staff", "hospital_admin", "system_admin"))
):
    """Mark staff presence with a check-in timestamp today."""
    return await service.check_in(hospital_id, data)

@router.patch("/attendance/{attendance_id}/check-out", response_model=AttendanceResponse)
async def check_out(
    data: AttendanceCheckOut,
    attendance_id: str = Path(...),
    service: AttendanceService = Depends(get_attendance_service),
    user: dict[str, Any] = Depends(require_roles("hospital_staff", "hospital_admin", "system_admin"))
):
    """Mark staff checkout timestamp and compute total hours worked."""
    return await service.check_out(attendance_id, data)

@router.get("/hospitals/{hospital_id}/attendance", response_model=PaginatedResponse[AttendanceResponse])
async def list_attendance(
    hospital_id: str = Path(...),
    date: str = Query("", description="YYYY-MM-DD format (defaults to today)"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    service: AttendanceService = Depends(get_attendance_service),
    user: dict[str, Any] = Depends(require_roles("hospital_staff", "hospital_admin", "system_admin"))
):
    """Fetch attendance records list for a specific day."""
    return await service.list_attendance(hospital_id, date, skip=skip, limit=limit)

@router.get("/hospitals/{hospital_id}/attendance/summary", response_model=AttendanceSummary)
async def get_daily_summary(
    hospital_id: str = Path(...),
    date: str = Query(""),
    service: AttendanceService = Depends(get_attendance_service),
    user: dict[str, Any] = Depends(require_roles("hospital_staff", "hospital_admin", "system_admin"))
):
    """Get aggregated attendance ratios (present, late, absent counts)."""
    return await service.get_daily_summary(hospital_id, date)
