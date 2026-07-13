"""Diagnostics service — Orchestrates equipment status, lab and imaging reports."""

from __future__ import annotations

from typing import Any
from fastapi import HTTPException
import structlog

from app.repositories import EquipmentRepository, LabReportRepository, ImagingReportRepository, NotificationRepository
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

logger = structlog.get_logger(__name__)

class DiagnosticsService:
    def __init__(
        self,
        equipment_repo: EquipmentRepository,
        lab_repo: LabReportRepository,
        imaging_repo: ImagingReportRepository,
        notification_repo: NotificationRepository,
    ):
        self.equipment_repo = equipment_repo
        self.lab_repo = lab_repo
        self.imaging_repo = imaging_repo
        self.notification_repo = notification_repo

    # --- Equipment ---
    async def add_equipment(self, hospital_id: str, data: EquipmentCreate) -> EquipmentResponse:
        item_dict = data.model_dump()
        item_dict["hospital_id"] = hospital_id
        res = await self.equipment_repo.create(item_dict)
        return EquipmentResponse(**res)

    async def get_equipment(self, equipment_id: str) -> EquipmentResponse:
        res = await self.equipment_repo.find_by_id(equipment_id)
        if not res:
            raise HTTPException(status_code=404, detail="Equipment not found.")
        return EquipmentResponse(**res)

    async def update_equipment(self, equipment_id: str, data: EquipmentUpdate) -> EquipmentResponse:
        await self.get_equipment(equipment_id)
        res = await self.equipment_repo.update(equipment_id, data.model_dump(exclude_unset=True))
        if not res:
            raise HTTPException(status_code=404, detail="Equipment update failed.")
        return EquipmentResponse(**res)

    async def list_equipment(self, hospital_id: str, skip: int = 0, limit: int = 20, status: str = "") -> PaginatedResponse[EquipmentResponse]:
        items, total = await self.equipment_repo.get_by_hospital(hospital_id, skip=skip, limit=limit, status_filter=status)
        return PaginatedResponse(
            items=[EquipmentResponse(**i) for i in items],
            total=total,
            skip=skip,
            limit=limit,
            has_more=(skip + limit) < total,
        )

    async def get_maintenance_due(self, hospital_id: str) -> list[EquipmentResponse]:
        items = await self.equipment_repo.get_maintenance_due(hospital_id)
        return [EquipmentResponse(**i) for i in items]

    # --- Lab Reports ---
    async def add_lab_report(self, hospital_id: str, data: LabReportCreate) -> LabReportResponse:
        report_dict = data.model_dump()
        report_dict["hospital_id"] = hospital_id
        res = await self.lab_repo.create_for_patient(hospital_id, report_dict)
        
        # Check if abnormal and trigger notification
        if data.is_abnormal:
            await self._trigger_abnormal_report_alert(
                hospital_id, data.patient_id, f"Lab Report: {data.test_name}", "lab"
            )

        return LabReportResponse(**res)

    async def get_lab_reports(self, patient_id: str, skip: int = 0, limit: int = 20) -> PaginatedResponse[LabReportResponse]:
        items, total = await self.lab_repo.get_by_patient(patient_id, skip=skip, limit=limit)
        return PaginatedResponse(
            items=[LabReportResponse(**i) for i in items],
            total=total,
            skip=skip,
            limit=limit,
            has_more=(skip + limit) < total,
        )

    # --- Imaging Reports ---
    async def add_imaging_report(self, hospital_id: str, data: ImagingReportCreate) -> ImagingReportResponse:
        report_dict = data.model_dump()
        report_dict["hospital_id"] = hospital_id
        res = await self.imaging_repo.create_for_patient(hospital_id, report_dict)
        return ImagingReportResponse(**res)

    async def get_imaging_reports(self, patient_id: str, skip: int = 0, limit: int = 20) -> PaginatedResponse[ImagingReportResponse]:
        items, total = await self.imaging_repo.get_by_patient(patient_id, skip=skip, limit=limit)
        return PaginatedResponse(
            items=[ImagingReportResponse(**i) for i in items],
            total=total,
            skip=skip,
            limit=limit,
            has_more=(skip + limit) < total,
        )

    async def _trigger_abnormal_report_alert(self, hospital_id: str, patient_id: str, title: str, report_type: str) -> None:
        alert_data = {
            "recipient_id": hospital_id,
            "recipient_type": "hospital",
            "title": f"Abnormal {title}",
            "message": f"Critical abnormal result detected for Patient ID: {patient_id}. Prompt review required.",
            "priority": "critical",
            "source": "diagnostics",
            "metadata": {
                "patient_id": patient_id,
                "report_type": report_type,
            }
        }
        await self.notification_repo.create(alert_data)
        logger.info("diagnostics.abnormal_report.alert_created", hospital_id=hospital_id, patient_id=patient_id)
