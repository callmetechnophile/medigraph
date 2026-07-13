"""Recommendations endpoints — retrieve AI operational suggestions."""

from __future__ import annotations

from typing import Any
from fastapi import APIRouter, Depends, Query, Path
from neo4j import AsyncDriver

from app.database.connection import get_driver
from app.repositories import RecommendationRepository, InventoryRepository, AttendanceRepository, AmbulanceRepository, EquipmentRepository
from app.services import RecommendationService, HMIService
from app.schemas import (
    RecommendationResponse,
    RecommendationActionRequest,
    PaginatedResponse,
)
from app.auth.dependencies import get_current_user, require_roles

router = APIRouter(tags=["Recommendations"])

def get_recommendation_service(driver: AsyncDriver = Depends(get_driver)) -> RecommendationService:
    repo = RecommendationRepository(driver)
    return RecommendationService(repo)

@router.get("/hospitals/{hospital_id}/recommendations", response_model=PaginatedResponse[RecommendationResponse])
async def list_recommendations(
    hospital_id: str = Path(...),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    status: str = Query(""),
    priority: str = Query(""),
    service: RecommendationService = Depends(get_recommendation_service),
    user: dict[str, Any] = Depends(get_current_user)
):
    """List AI operational recommendations for a hospital."""
    return await service.list_recommendations(hospital_id, skip=skip, limit=limit, status=status, priority=priority)

@router.get("/recommendations/{recommendation_id}", response_model=RecommendationResponse)
async def get_recommendation(
    recommendation_id: str = Path(...),
    service: RecommendationService = Depends(get_recommendation_service),
    user: dict[str, Any] = Depends(get_current_user)
):
    """Get recommendation details."""
    return await service.get_recommendation(recommendation_id)

@router.post("/recommendations/{recommendation_id}/action", response_model=RecommendationResponse)
async def act_on_recommendation(
    data: RecommendationActionRequest,
    recommendation_id: str = Path(...),
    service: RecommendationService = Depends(get_recommendation_service),
    user: dict[str, Any] = Depends(require_roles("hospital_admin", "system_admin"))
):
    """Accept or dismiss an operational recommendation."""
    if data.action.lower() == "accept":
        return await service.accept_recommendation(recommendation_id, user["user_id"])
    return await service.dismiss_recommendation(recommendation_id, user["user_id"])

@router.post("/hospitals/{hospital_id}/recommendations/generate")
async def trigger_recommendation_generation(
    hospital_id: str = Path(...),
    driver: AsyncDriver = Depends(get_driver),
    user: dict[str, Any] = Depends(require_roles("hospital_admin", "system_admin"))
):
    """Trigger the AI Recommendation Engine calculation for a hospital."""
    # Instantiates the full stack of forecasters and runs HMI score to generate suggestions
    # We call HMIService to run calculation which automatically creates recommendations on low scores
    hmi_repo = HMIRepository(driver)
    inv_repo = InventoryRepository(driver)
    att_repo = AttendanceRepository(driver)
    amb_repo = AmbulanceRepository(driver)
    eq_repo = EquipmentRepository(driver)
    
    hmi_service = HMIService(hmi_repo, inv_repo, att_repo, amb_repo, eq_repo)
    score = await hmi_service.calculate_hmi(hospital_id)
    return {"message": "AI recommendations computed and updated.", "hmi_score": score.overall_score}
