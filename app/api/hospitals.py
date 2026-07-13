"""Hospital endpoints — hospital management, departments, and doctors."""

from __future__ import annotations

from typing import Any
from fastapi import APIRouter, Depends, Query, Path
from neo4j import AsyncDriver

from app.database.connection import get_driver
from app.repositories import HospitalRepository
from app.services import HospitalService
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
from app.auth.dependencies import get_current_user, require_roles

router = APIRouter(prefix="/hospitals", tags=["Hospitals"])

def get_hospital_service(driver: AsyncDriver = Depends(get_driver)) -> HospitalService:
    repo = HospitalRepository(driver)
    return HospitalService(repo)

@router.post("", response_model=HospitalResponse)
async def register_hospital(
    data: HospitalCreate,
    service: HospitalService = Depends(get_hospital_service),
    user: dict[str, Any] = Depends(require_roles("district_admin", "system_admin"))
):
    """Register a new hospital. Restricted to district and system administrators."""
    return await service.register_hospital(data)

@router.get("", response_model=PaginatedResponse[HospitalResponse])
async def list_hospitals(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    search: str = Query(""),
    service: HospitalService = Depends(get_hospital_service),
    user: dict[str, Any] = Depends(get_current_user)
):
    """List and search hospitals."""
    return await service.list_hospitals(skip=skip, limit=limit, search=search)

@router.get("/{hospital_id}", response_model=HospitalResponse)
async def get_hospital(
    hospital_id: str = Path(...),
    service: HospitalService = Depends(get_hospital_service),
    user: dict[str, Any] = Depends(get_current_user)
):
    """Get hospital details by ID."""
    return await service.get_hospital(hospital_id)

@router.put("/{hospital_id}", response_model=HospitalResponse)
async def update_hospital(
    data: HospitalUpdate,
    hospital_id: str = Path(...),
    service: HospitalService = Depends(get_hospital_service),
    user: dict[str, Any] = Depends(require_roles("hospital_admin", "system_admin"))
):
    """Update hospital details."""
    return await service.update_hospital(hospital_id, data)

@router.delete("/{hospital_id}")
async def delete_hospital(
    hospital_id: str = Path(...),
    service: HospitalService = Depends(get_hospital_service),
    user: dict[str, Any] = Depends(require_roles("system_admin"))
):
    """Delete a hospital. Restricted to system administrators."""
    success = await service.delete_hospital(hospital_id)
    return {"success": success, "message": "Hospital deleted successfully."}

@router.post("/{hospital_id}/departments", response_model=DepartmentResponse)
async def add_department(
    data: DepartmentCreate,
    hospital_id: str = Path(...),
    service: HospitalService = Depends(get_hospital_service),
    user: dict[str, Any] = Depends(require_roles("hospital_admin", "system_admin"))
):
    """Add a department to a hospital."""
    return await service.add_department(hospital_id, data)

@router.get("/{hospital_id}/departments", response_model=PaginatedResponse[DepartmentResponse])
async def list_departments(
    hospital_id: str = Path(...),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    service: HospitalService = Depends(get_hospital_service),
    user: dict[str, Any] = Depends(get_current_user)
):
    """List departments in a hospital."""
    return await service.list_departments(hospital_id, skip=skip, limit=limit)

@router.post("/{hospital_id}/departments/{dept_id}/doctors", response_model=DoctorResponse)
async def add_doctor(
    data: DoctorCreate,
    hospital_id: str = Path(...),
    dept_id: str = Path(...),
    service: HospitalService = Depends(get_hospital_service),
    user: dict[str, Any] = Depends(require_roles("hospital_admin", "system_admin"))
):
    """Register a doctor inside a hospital department."""
    return await service.add_doctor(hospital_id, dept_id, data)

@router.get("/{hospital_id}/doctors", response_model=PaginatedResponse[DoctorResponse])
async def list_doctors(
    hospital_id: str = Path(...),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    service: HospitalService = Depends(get_hospital_service),
    user: dict[str, Any] = Depends(get_current_user)
):
    """List all doctors in a hospital."""
    return await service.list_doctors(hospital_id, skip=skip, limit=limit)
