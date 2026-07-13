"""Hospital service — Orchestrates Hospital operations, departments, and doctors."""

from __future__ import annotations

from typing import Any
from fastapi import HTTPException
import structlog

from app.repositories import HospitalRepository
from app.schemas import (
    HospitalCreate,
    HospitalUpdate,
    HospitalResponse,
    PaginatedResponse,
    DepartmentCreate,
    DepartmentResponse,
    DoctorCreate,
    DoctorResponse,
    HospitalDashboard,
)

logger = structlog.get_logger(__name__)

class HospitalService:
    def __init__(self, hospital_repo: HospitalRepository):
        self.hospital_repo = hospital_repo

    async def register_hospital(self, data: HospitalCreate) -> HospitalResponse:
        res = await self.hospital_repo.create(data.model_dump())
        return HospitalResponse(**res)

    async def get_hospital(self, hospital_id: str) -> HospitalResponse:
        res = await self.hospital_repo.find_by_id(hospital_id)
        if not res:
            raise HTTPException(status_code=404, detail="Hospital not found.")
        return HospitalResponse(**res)

    async def update_hospital(self, hospital_id: str, data: HospitalUpdate) -> HospitalResponse:
        await self.get_hospital(hospital_id)
        res = await self.hospital_repo.update(hospital_id, data.model_dump(exclude_unset=True))
        if not res:
            raise HTTPException(status_code=404, detail="Hospital update failed.")
        return HospitalResponse(**res)

    async def delete_hospital(self, hospital_id: str) -> bool:
        await self.get_hospital(hospital_id)
        return await self.hospital_repo.delete(hospital_id)

    async def list_hospitals(self, skip: int = 0, limit: int = 20, sort_by: str = "name", sort_order: str = "asc", search: str = "") -> PaginatedResponse[HospitalResponse]:
        items, total = await self.hospital_repo.find_all(
            skip=skip, limit=limit, sort_by=sort_by, sort_order=sort_order, search=search
        )
        return PaginatedResponse(
            items=[HospitalResponse(**i) for i in items],
            total=total,
            skip=skip,
            limit=limit,
            has_more=(skip + limit) < total,
        )

    async def add_department(self, hospital_id: str, data: DepartmentCreate) -> DepartmentResponse:
        await self.get_hospital(hospital_id)
        res = await self.hospital_repo.add_department(hospital_id, data.model_dump())
        return DepartmentResponse(**res)

    async def get_departments(self, hospital_id: str, skip: int = 0, limit: int = 20) -> PaginatedResponse[DepartmentResponse]:
        await self.get_hospital(hospital_id)
        items, total = await self.hospital_repo.get_departments(hospital_id, skip=skip, limit=limit)
        return PaginatedResponse(
            items=[DepartmentResponse(**i) for i in items],
            total=total,
            skip=skip,
            limit=limit,
            has_more=(skip + limit) < total,
        )

    async def add_doctor(self, hospital_id: str, department_id: str, data: DoctorCreate) -> DoctorResponse:
        await self.get_hospital(hospital_id)
        # Verify department exists (we can fetch all departments and filter, or just run query)
        res = await self.hospital_repo.add_doctor(hospital_id, department_id, data.model_dump())
        return DoctorResponse(**res)

    async def get_doctors(self, hospital_id: str, skip: int = 0, limit: int = 20) -> PaginatedResponse[DoctorResponse]:
        await self.get_hospital(hospital_id)
        items, total = await self.hospital_repo.get_doctors(hospital_id, skip=skip, limit=limit)
        return PaginatedResponse(
            items=[DoctorResponse(**i) for i in items],
            total=total,
            skip=skip,
            limit=limit,
            has_more=(skip + limit) < total,
        )

    async def get_dashboard_data(self, hospital_id: str) -> HospitalDashboard:
        h = await self.get_hospital(hospital_id)
        data = await self.hospital_repo.get_dashboard_data(hospital_id)
        
        # Calculate bed occupancy rate
        total_beds = data.get("total_beds", 0)
        available_beds = data.get("available_beds", 0)
        occupied_beds = max(0, total_beds - available_beds)
        occupancy_rate = (occupied_beds / total_beds * 100) if total_beds > 0 else 0.0

        # Construct recent notifications placeholder/future retrieval
        # Recent notifications will be handled by API layer calling NotificationService directly

        return HospitalDashboard(
            hospital_id=hospital_id,
            hospital_name=h.name,
            total_patients_today=0,  # Computed from records or dashboard
            total_staff_present=data.get("staff_present", 0),
            available_beds=available_beds,
            total_beds=total_beds,
            bed_occupancy_rate=round(occupancy_rate, 2),
            ambulances_available=data.get("available_ambulances", 0),
            ambulances_total=data.get("total_ambulances", 0),
            low_stock_items=data.get("low_stock_items", 0),
            critical_notifications=0,
            hmi_score=0.0,  # Filled in by API using HMIService
            recent_notifications=[],
            department_summary=[],
        )
