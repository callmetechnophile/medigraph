"""HMI endpoints — current score and historical trends."""

from __future__ import annotations

from typing import Any
from fastapi import APIRouter, Depends, Path, Query
from neo4j import AsyncDriver

from app.database.connection import get_driver
from app.repositories import (
    HMIRepository,
    InventoryRepository,
    AttendanceRepository,
    AmbulanceRepository,
    EquipmentRepository,
)
from app.services import HMIService
from app.schemas import HMIScoreResponse, HMITrendResponse
from app.auth.dependencies import get_current_user, require_roles

router = APIRouter(tags=["HMI"])

def get_hmi_service(driver: AsyncDriver = Depends(get_driver)) -> HMIService:
    hmi_repo = HMIRepository(driver)
    inv_repo = InventoryRepository(driver)
    att_repo = AttendanceRepository(driver)
    amb_repo = AmbulanceRepository(driver)
    eq_repo = EquipmentRepository(driver)
    return HMIService(hmi_repo, inv_repo, att_repo, amb_repo, eq_repo)

@router.get("/hospitals/{hospital_id}/hmi", response_model=HMIScoreResponse)
async def get_current_hmi(
    hospital_id: str = Path(...),
    service: HMIService = Depends(get_hmi_service),
    user: dict[str, Any] = Depends(get_current_user)
):
    """Get the current daily HMI score for a hospital."""
    return await service.get_current_score(hospital_id)

@router.get("/hospitals/{hospital_id}/hmi/history", response_model=HMITrendResponse)
async def get_hmi_history(
    hospital_id: str = Path(...),
    limit: int = Query(30, ge=1, le=100),
    service: HMIService = Depends(get_hmi_service),
    user: dict[str, Any] = Depends(get_current_user)
):
    """Get historical trend parameters of HMI scores."""
    return await service.get_history(hospital_id, limit)

@router.post("/hospitals/{hospital_id}/hmi/calculate", response_model=HMIScoreResponse)
async def trigger_recalculation(
    hospital_id: str = Path(...),
    service: HMIService = Depends(get_hmi_service),
    user: dict[str, Any] = Depends(require_roles("hospital_admin", "district_admin", "system_admin"))
):
    """Trigger HMI score recalculation based on live inventory, attendance, and diagnostics metrics."""
    return await service.calculate_hmi(hospital_id)
