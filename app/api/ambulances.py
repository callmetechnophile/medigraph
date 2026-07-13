"""Ambulance endpoints — dispatch management and vehicle coordination."""

from __future__ import annotations

from typing import Any
from fastapi import APIRouter, Depends, Query, Path
from neo4j import AsyncDriver

from app.database.connection import get_driver
from app.repositories import AmbulanceRepository, NotificationRepository
from app.services import AmbulanceService
from app.schemas import (
    AmbulanceCreate,
    AmbulanceUpdate,
    AmbulanceResponse,
    AmbulanceDispatchRequest,
    PaginatedResponse,
)
from app.auth.dependencies import get_current_user, require_roles

router = APIRouter(tags=["Ambulances"])

def get_ambulance_service(driver: AsyncDriver = Depends(get_driver)) -> AmbulanceService:
    amb_repo = AmbulanceRepository(driver)
    notif_repo = NotificationRepository(driver)
    return AmbulanceService(amb_repo, notif_repo)

@router.post("/hospitals/{hospital_id}/ambulances", response_model=AmbulanceResponse)
async def add_ambulance(
    data: AmbulanceCreate,
    hospital_id: str = Path(...),
    service: AmbulanceService = Depends(get_ambulance_service),
    user: dict[str, Any] = Depends(require_roles("hospital_admin", "system_admin"))
):
    """Register a new vehicle inside the hospital ambulance fleet."""
    return await service.add_ambulance(hospital_id, data)

@router.get("/hospitals/{hospital_id}/ambulances", response_model=PaginatedResponse[AmbulanceResponse])
async def list_ambulances(
    hospital_id: str = Path(...),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    status: str = Query(""),
    service: AmbulanceService = Depends(get_ambulance_service),
    user: dict[str, Any] = Depends(get_current_user)
):
    """List ambulance vehicles matching status criteria."""
    return await service.list_ambulances(hospital_id, skip=skip, limit=limit, status=status)

@router.get("/ambulances/{ambulance_id}", response_model=AmbulanceResponse)
async def get_ambulance(
    ambulance_id: str = Path(...),
    service: AmbulanceService = Depends(get_ambulance_service),
    user: dict[str, Any] = Depends(get_current_user)
):
    """Get ambulance telemetry and status details."""
    return await service.get_ambulance(ambulance_id)

@router.put("/ambulances/{ambulance_id}", response_model=AmbulanceResponse)
async def update_ambulance(
    data: AmbulanceUpdate,
    ambulance_id: str = Path(...),
    service: AmbulanceService = Depends(get_ambulance_service),
    user: dict[str, Any] = Depends(require_roles("hospital_staff", "hospital_admin", "system_admin"))
):
    """Update driver profile or geographical coordinates of ambulance."""
    return await service.update_ambulance(ambulance_id, data)

@router.post("/ambulances/{ambulance_id}/dispatch", response_model=AmbulanceResponse)
async def dispatch_ambulance(
    data: AmbulanceDispatchRequest,
    ambulance_id: str = Path(...),
    service: AmbulanceService = Depends(get_ambulance_service),
    user: dict[str, Any] = Depends(require_roles("hospital_staff", "hospital_admin", "system_admin"))
):
    """Dispatch vehicle to incident coordinates and alert staff."""
    return await service.dispatch(ambulance_id, data)

@router.post("/ambulances/{ambulance_id}/return", response_model=AmbulanceResponse)
async def mark_returned(
    ambulance_id: str = Path(...),
    service: AmbulanceService = Depends(get_ambulance_service),
    user: dict[str, Any] = Depends(require_roles("hospital_staff", "hospital_admin", "system_admin"))
):
    """Reset vehicle status back to 'available' at home base."""
    return await service.mark_returned(ambulance_id)

@router.get("/hospitals/{hospital_id}/ambulances/summary")
async def get_fleet_summary(
    hospital_id: str = Path(...),
    service: AmbulanceService = Depends(get_ambulance_service),
    user: dict[str, Any] = Depends(get_current_user)
):
    """Get total ambulance counts grouped by status."""
    return await service.get_fleet_summary(hospital_id)
