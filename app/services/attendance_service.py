"""Attendance service — Orchestrates Staff check-ins and absence escalations."""

from __future__ import annotations

from typing import Any
from fastapi import HTTPException
import structlog

from app.repositories import AttendanceRepository, NotificationRepository
from app.schemas import (
    AttendanceCheckIn,
    AttendanceCheckOut,
    AttendanceResponse,
    AttendanceSummary,
    PaginatedResponse,
)
from app.utils.helpers import utc_now, today_str

logger = structlog.get_logger(__name__)

class AttendanceService:
    def __init__(self, attendance_repo: AttendanceRepository, notification_repo: NotificationRepository):
        self.attendance_repo = attendance_repo
        self.notification_repo = notification_repo

    async def check_in(self, hospital_id: str, data: AttendanceCheckIn) -> AttendanceResponse:
        date = today_str()
        check_in_time = utc_now()
        
        # Check if already checked in today
        history = await self.attendance_repo.get_staff_attendance_history(data.staff_id, date, date)
        if history:
            raise HTTPException(status_code=400, detail="Staff already checked in today.")
        
        res = await self.attendance_repo.check_in(
            hospital_id=hospital_id,
            staff_id=data.staff_id,
            department_id=data.department_id,
            date=date,
            check_in_time=check_in_time,
        )
        return AttendanceResponse(**res)

    async def check_out(self, attendance_id: str, data: AttendanceCheckOut) -> AttendanceResponse:
        att = await self.attendance_repo.find_by_id(attendance_id)
        if not att:
            raise HTTPException(status_code=404, detail="Attendance record not found.")
        
        if att.get("check_out"):
            raise HTTPException(status_code=400, detail="Staff already checked out.")

        check_out_time = utc_now()
        
        # Simple hours calculation
        try:
            in_dt = datetime.fromisoformat(att["check_in"].replace("Z", "+00:00"))
            out_dt = datetime.fromisoformat(check_out_time.replace("Z", "+00:00"))
            hours_worked = (out_dt - in_dt).total_seconds() / 3600.0
        except Exception:
            hours_worked = 8.0  # fallback standard shift

        res = await self.attendance_repo.check_out(attendance_id, check_out_time, round(hours_worked, 2))
        if not res:
            raise HTTPException(status_code=404, detail="Check-out failed.")
        return AttendanceResponse(**res)

    async def list_attendance(self, hospital_id: str, date: str = "", skip: int = 0, limit: int = 20) -> PaginatedResponse[AttendanceResponse]:
        target_date = date or today_str()
        items, total = await self.attendance_repo.get_by_hospital(hospital_id, target_date, skip=skip, limit=limit)
        return PaginatedResponse(
            items=[AttendanceResponse(**i) for i in items],
            total=total,
            skip=skip,
            limit=limit,
            has_more=(skip + limit) < total,
        )

    async def get_daily_summary(self, hospital_id: str, date: str = "") -> AttendanceSummary:
        target_date = date or today_str()
        res = await self.attendance_repo.get_daily_summary(hospital_id, target_date)
        return AttendanceSummary(**res)

    async def get_staff_history(self, staff_id: str, start_date: str, end_date: str) -> list[AttendanceResponse]:
        items = await self.attendance_repo.get_staff_attendance_history(staff_id, start_date, end_date)
        return [AttendanceResponse(**i) for i in items]

    async def escalate_absences(self, hospital_id: str, date: str = "") -> dict[str, Any]:
        target_date = date or today_str()
        absent_staff = await self.attendance_repo.get_absent_staff(hospital_id, target_date)
        
        escalated_count = 0
        for staff in absent_staff:
            # Generate critical notification
            alert_data = {
                "recipient_id": hospital_id,
                "recipient_type": "hospital",
                "title": f"Staff Absence Alert: {staff['name']}",
                "message": f"Doctor {staff['name']} ({staff.get('specialization', 'General')}) has not checked in today ({target_date}). Please verify attendance.",
                "priority": "warning",
                "source": "attendance",
                "metadata": {
                    "staff_id": staff["id"],
                    "staff_name": staff["name"],
                    "date": target_date,
                    "department_name": staff.get("department_name", ""),
                }
            }
            await self.notification_repo.create(alert_data)
            escalated_count += 1

        logger.info("attendance.absences_escalated", hospital_id=hospital_id, count=escalated_count)
        return {"message": f"Escalated {escalated_count} absences.", "success": True, "count": escalated_count}

from datetime import datetime
