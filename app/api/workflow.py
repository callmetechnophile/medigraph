"""Workflow endpoints — manually trigger backend workflows."""

from __future__ import annotations

from typing import Any
from fastapi import APIRouter, Depends
from neo4j import AsyncDriver

from app.database.connection import get_driver
from app.repositories import (
    InventoryRepository,
    AttendanceRepository,
    HMIRepository,
    ReportRepository,
    NotificationRepository,
    RecommendationRepository,
    AmbulanceRepository,
    EquipmentRepository,
)
from app.services import (
    WorkflowService,
    InventoryService,
    AttendanceService,
    HMIService,
    ReportService,
    NotificationService,
    RecommendationService,
)
from app.schemas import WorkflowTriggerRequest, WorkflowStatusResponse
from app.auth.dependencies import require_roles
from app.config import get_settings

router = APIRouter(prefix="/workflows", tags=["Workflow"])

def get_workflow_service(driver: AsyncDriver = Depends(get_driver)) -> WorkflowService:
    settings = get_settings()
    
    # Repos
    inv_repo = InventoryRepository(driver)
    notif_repo = NotificationRepository(driver)
    att_repo = AttendanceRepository(driver)
    hmi_repo = HMIRepository(driver)
    amb_repo = AmbulanceRepository(driver)
    eq_repo = EquipmentRepository(driver)
    rep_repo = ReportRepository(driver)
    rec_repo = RecommendationRepository(driver)

    # Services
    inventory_service = InventoryService(inv_repo, notif_repo)
    attendance_service = AttendanceService(att_repo, notif_repo)
    hmi_service = HMIService(hmi_repo, inv_repo, att_repo, amb_repo, eq_repo)
    report_service = ReportService(
        rep_repo, settings.supabase_url, settings.supabase_key, settings.supabase_bucket, settings.report_temp_dir
    )
    notification_service = NotificationService(
        notif_repo, settings.brevo_api_key, settings.brevo_sender_email, settings.brevo_sender_name
    )
    recommendation_service = RecommendationService(rec_repo)

    return WorkflowService(
        inventory_service,
        attendance_service,
        hmi_service,
        report_service,
        notification_service,
        recommendation_service,
    )

@router.post("/trigger", response_model=WorkflowStatusResponse)
async def trigger_workflow(
    data: WorkflowTriggerRequest,
    service: WorkflowService = Depends(get_workflow_service),
    user: dict[str, Any] = Depends(require_roles("hospital_admin", "district_admin", "system_admin"))
):
    """Manually trigger background workflow (e.g. inventory checks, analytics computation)."""
    return await service.trigger_workflow(data.workflow_type, data.hospital_id, data.parameters)
