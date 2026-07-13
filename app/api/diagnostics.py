"""Diagnostics endpoints — Equipment status, Lab reports, and Imaging reports."""

from __future__ import annotations

from typing import Any
from fastapi import APIRouter, Depends, Query, Path
from neo4j import AsyncDriver

from app.database.connection import get_driver
from app.repositories import EquipmentRepository, LabReportRepository, ImagingReportRepository, NotificationRepository
from app.services import DiagnosticsService
from app.schemas import (
    EquipmentCreate,
    EquipmentUpdate,
    EquipmentResponse,
    PaginatedResponse,
    LabReportCreate,
    LabReportResponse,
    ImagingReportCreate,
    ImagingReportResponse,
)
from app.auth.dependencies import get_current_user, require_roles

router = APIRouter(tags=["Diagnostics"])

def get_diagnostics_service(driver: AsyncDriver = Depends(get_driver)) -> DiagnosticsService:
    eq_repo = EquipmentRepository(driver)
    lab_repo = LabReportRepository(driver)
    img_repo = ImagingReportRepository(driver)
    notif_repo = NotificationRepository(driver)
    return DiagnosticsService(eq_repo, lab_repo, img_repo, notif_repo)

# --- Equipment ---
@router.post("/hospitals/{hospital_id}/equipment", response_model=EquipmentResponse)
async def add_equipment(
    data: EquipmentCreate,
    hospital_id: str = Path(...),
    service: DiagnosticsService = Depends(get_diagnostics_service),
    user: dict[str, Any] = Depends(require_roles("hospital_admin", "system_admin"))
):
    """Register diagnostic hardware device."""
    return await service.add_equipment(hospital_id, data)

@router.get("/hospitals/{hospital_id}/equipment", response_model=PaginatedResponse[EquipmentResponse])
async def list_equipment(
    hospital_id: str = Path(...),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    status: str = Query(""),
    service: DiagnosticsService = Depends(get_diagnostics_service),
    user: dict[str, Any] = Depends(get_current_user)
):
    """List hardware devices matching status filters."""
    return await service.list_equipment(hospital_id, skip=skip, limit=limit, status=status)

@router.get("/equipment/{equipment_id}", response_model=EquipmentResponse)
async def get_equipment(
    equipment_id: str = Path(...),
    service: DiagnosticsService = Depends(get_diagnostics_service),
    user: dict[str, Any] = Depends(get_current_user)
):
    """Get equipment specifications."""
    return await service.get_equipment(equipment_id)

@router.put("/equipment/{equipment_id}", response_model=EquipmentResponse)
async def update_equipment(
    data: EquipmentUpdate,
    equipment_id: str = Path(...),
    service: DiagnosticsService = Depends(get_diagnostics_service),
    user: dict[str, Any] = Depends(require_roles("hospital_staff", "hospital_admin", "system_admin"))
):
    """Update maintenance or status coordinates of equipment."""
    return await service.update_equipment(equipment_id, data)

@router.get("/hospitals/{hospital_id}/equipment/maintenance-due", response_model=list[EquipmentResponse])
async def get_maintenance_due(
    hospital_id: str = Path(...),
    service: DiagnosticsService = Depends(get_diagnostics_service),
    user: dict[str, Any] = Depends(require_roles("hospital_staff", "hospital_admin", "system_admin"))
):
    """List hardware units that require scheduled maintenance checkups."""
    return await service.get_maintenance_due(hospital_id)

# --- Laboratory Reports ---
@router.post("/hospitals/{hospital_id}/lab-reports", response_model=LabReportResponse)
async def add_lab_report(
    data: LabReportCreate,
    hospital_id: str = Path(...),
    service: DiagnosticsService = Depends(get_diagnostics_service),
    user: dict[str, Any] = Depends(require_roles("doctor", "system_admin"))
):
    """Upload lab test report results and generate alerts if abnormal."""
    return await service.add_lab_report(hospital_id, data)

@router.get("/patients/{patient_id}/lab-reports", response_model=PaginatedResponse[LabReportResponse])
async def get_lab_reports(
    patient_id: str = Path(...),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    service: DiagnosticsService = Depends(get_diagnostics_service),
    user: dict[str, Any] = Depends(get_current_user)
):
    """List laboratory report records matching patient ID."""
    return await service.get_lab_reports(patient_id, skip=skip, limit=limit)

# --- Imaging Reports ---
@router.post("/hospitals/{hospital_id}/imaging-reports", response_model=ImagingReportResponse)
async def add_imaging_report(
    data: ImagingReportCreate,
    hospital_id: str = Path(...),
    service: DiagnosticsService = Depends(get_diagnostics_service),
    user: dict[str, Any] = Depends(require_roles("doctor", "system_admin"))
):
    """Upload diagnostic imaging scan impression reports."""
    return await service.add_imaging_report(hospital_id, data)

@router.get("/patients/{patient_id}/imaging-reports", response_model=PaginatedResponse[ImagingReportResponse])
async def get_imaging_reports(
    patient_id: str = Path(...),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    service: DiagnosticsService = Depends(get_diagnostics_service),
    user: dict[str, Any] = Depends(get_current_user)
):
    """List imaging reports matching patient ID."""
    return await service.get_imaging_reports(patient_id, skip=skip, limit=limit)
