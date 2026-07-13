"""Recommendation service — Orchestrates AI recommendations lifecycle."""

from __future__ import annotations

from typing import Any
from fastapi import HTTPException
import structlog

from app.repositories import RecommendationRepository
from app.schemas import (
    RecommendationResponse,
    PaginatedResponse,
)

logger = structlog.get_logger(__name__)

class RecommendationService:
    def __init__(self, recommendation_repo: RecommendationRepository):
        self.recommendation_repo = recommendation_repo

    async def list_recommendations(self, hospital_id: str, skip: int = 0, limit: int = 20, status: str = "", priority: str = "") -> PaginatedResponse[RecommendationResponse]:
        items, total = await self.recommendation_repo.get_by_hospital(
            hospital_id, skip=skip, limit=limit, status_filter=status, priority_filter=priority
        )
        return PaginatedResponse(
            items=[RecommendationResponse(**i) for i in items],
            total=total,
            skip=skip,
            limit=limit,
            has_more=(skip + limit) < total,
        )

    async def get_recommendation(self, recommendation_id: str) -> RecommendationResponse:
        res = await self.recommendation_repo.find_by_id(recommendation_id)
        if not res:
            raise HTTPException(status_code=404, detail="Recommendation not found.")
        return RecommendationResponse(**res)

    async def accept_recommendation(self, recommendation_id: str, user_id: str) -> RecommendationResponse:
        await self.get_recommendation(recommendation_id)
        res = await self.recommendation_repo.accept(recommendation_id, user_id)
        if not res:
            raise HTTPException(status_code=404, detail="Failed to accept recommendation.")
        return RecommendationResponse(**res)

    async def dismiss_recommendation(self, recommendation_id: str, user_id: str) -> RecommendationResponse:
        await self.get_recommendation(recommendation_id)
        res = await self.recommendation_repo.dismiss(recommendation_id, user_id)
        if not res:
            raise HTTPException(status_code=404, detail="Failed to dismiss recommendation.")
        return RecommendationResponse(**res)

    async def create_recommendation(self, hospital_id: str, data: dict[str, Any]) -> RecommendationResponse:
        res = await self.recommendation_repo.create_for_hospital(hospital_id, data)
        return RecommendationResponse(**res)

    async def get_pending_count(self, hospital_id: str) -> int:
        res = await self.recommendation_repo.get_pending(hospital_id)
        return len(res)
