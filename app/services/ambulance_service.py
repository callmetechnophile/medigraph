"""Ambulance service — Fleet coordination and dispatch routing."""

from __future__ import annotations

from typing import Any
from fastapi import HTTPException
import structlog

from app.repositories import AmbulanceRepository, NotificationRepository
from app.schemas import (
    AmbulanceCreate,
    AmbulanceUpdate,
    AmbulanceResponse,
    AmbulanceDispatchRequest,
    PaginatedResponse,
)

logger = structlog.get_logger(__name__)

class AmbulanceService:
    def __init__(self, ambulance_repo: AmbulanceRepository, notification_repo: NotificationRepository):
        self.ambulance_repo = ambulance_repo
        self.notification_repo = notification_repo

    async def add_ambulance(self, hospital_id: str, data: AmbulanceCreate) -> AmbulanceResponse:
        res = await self.ambulance_repo.create_for_hospital(hospital_id, data.model_dump())
        return AmbulanceResponse(**res)

    async def get_ambulance(self, ambulance_id: str) -> AmbulanceResponse:
        res = await self.ambulance_repo.find_by_id(ambulance_id)
        if not res:
            raise HTTPException(status_code=404, detail="Ambulance not found.")
        return AmbulanceResponse(**res)

    async def update_ambulance(self, ambulance_id: str, data: AmbulanceUpdate) -> AmbulanceResponse:
        await self.get_ambulance(ambulance_id)
        res = await self.ambulance_repo.update(ambulance_id, data.model_dump(exclude_unset=True))
        if not res:
            raise HTTPException(status_code=404, detail="Ambulance update failed.")
        return AmbulanceResponse(**res)

    async def list_ambulances(self, hospital_id: str, skip: int = 0, limit: int = 20, status: str = "") -> PaginatedResponse[AmbulanceResponse]:
        items, total = await self.ambulance_repo.get_by_hospital(hospital_id, skip=skip, limit=limit, status_filter=status)
        return PaginatedResponse(
            items=[AmbulanceResponse(**i) for i in items],
            total=total,
            skip=skip,
            limit=limit,
            has_more=(skip + limit) < total,
        )

    async def dispatch(self, ambulance_id: str, data: AmbulanceDispatchRequest) -> AmbulanceResponse:
        amb = await self.get_ambulance(ambulance_id)
        if amb.status != "available":
            raise HTTPException(status_code=400, detail=f"Ambulance is not available. Current status: {amb.status}")

        res = await self.ambulance_repo.dispatch(
            ambulance_id=ambulance_id,
            destination=data.destination,
            patient_id=data.patient_id,
            latitude=data.latitude,
            longitude=data.longitude,
        )
        if not res:
            raise HTTPException(status_code=500, detail="Dispatch failed.")

        # Create critical notification for dispatch
        alert_data = {
            "recipient_id": amb.hospital_id,
            "recipient_type": "hospital",
            "title": f"Ambulance Dispatched: {amb.vehicle_number}",
            "message": f"Ambulance {amb.vehicle_number} has been dispatched to {data.destination}. Emergency type: {data.emergency_type}",
            "priority": "critical",
            "source": "workflow",
            "metadata": {
                "ambulance_id": ambulance_id,
                "vehicle_number": amb.vehicle_number,
                "destination": data.destination,
                "emergency_type": data.emergency_type,
            }
        }
        await self.notification_repo.create(alert_data)
        logger.info("ambulance.dispatched", ambulance_id=ambulance_id, destination=data.destination)

        return AmbulanceResponse(**res)

    async def mark_returned(self, ambulance_id: str) -> AmbulanceResponse:
        await self.get_ambulance(ambulance_id)
        res = await self.ambulance_repo.mark_returned(ambulance_id)
        if not res:
            raise HTTPException(status_code=500, detail="Failed to mark ambulance as returned.")
        logger.info("ambulance.returned", ambulance_id=ambulance_id)
        return AmbulanceResponse(**res)

    async def get_fleet_summary(self, hospital_id: str) -> dict[str, int]:
        return await self.ambulance_repo.get_fleet_summary(hospital_id)

    async def get_available_count(self, hospital_id: str) -> int:
        res = await self.ambulance_repo.get_available(hospital_id)
        return len(res)
