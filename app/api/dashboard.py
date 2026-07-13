"""Dashboard endpoints — Hospital and District summaries."""

from __future__ import annotations

from typing import Any
from fastapi import APIRouter, Depends, Path
from neo4j import AsyncDriver

from app.database.connection import get_driver
from app.repositories import (
    HospitalRepository,
    HMIRepository,
    InventoryRepository,
    AttendanceRepository,
    AmbulanceRepository,
    EquipmentRepository,
    DistrictRepository,
    NotificationRepository,
)
from app.services import HospitalService, HMIService, NotificationService
from app.schemas import HospitalDashboard, DistrictDashboard, NotificationResponse
from app.auth.dependencies import get_current_user, require_roles
from app.config import get_settings

router = APIRouter(tags=["Dashboard"])

def get_dashboard_services(driver: AsyncDriver = Depends(get_driver)):
    settings = get_settings()
    h_repo = HospitalRepository(driver)
    hmi_repo = HMIRepository(driver)
    inv_repo = InventoryRepository(driver)
    att_repo = AttendanceRepository(driver)
    amb_repo = AmbulanceRepository(driver)
    eq_repo = EquipmentRepository(driver)
    dist_repo = DistrictRepository(driver)
    notif_repo = NotificationRepository(driver)

    h_service = HospitalService(h_repo)
    hmi_service = HMIService(hmi_repo, inv_repo, att_repo, amb_repo, eq_repo)
    notif_service = NotificationService(
        notif_repo, settings.brevo_api_key, settings.brevo_sender_email, settings.brevo_sender_name
    )

    return h_service, hmi_service, notif_service, dist_repo

@router.get("/hospitals/{hospital_id}/dashboard", response_model=HospitalDashboard)
async def get_hospital_dashboard(
    hospital_id: str = Path(...),
    deps: tuple = Depends(get_dashboard_services),
    user: dict[str, Any] = Depends(get_current_user)
):
    """Retrieve aggregated data for the Hospital Operations dashboard."""
    h_service, hmi_service, notif_service, _ = deps

    # 1. Fetch base dashboard details (beds, staff, ambulances counts)
    dash = await h_service.get_dashboard_data(hospital_id)
    
    # 2. Add HMI Score
    hmi = await hmi_service.get_current_score(hospital_id)
    dash.hmi_score = hmi.overall_score

    # 3. Add recent notifications
    notifications_page = await notif_service.list_notifications(hospital_id, skip=0, limit=5)
    dash.recent_notifications = notifications_page.items

    return dash

@router.get("/districts/{district_id}/dashboard", response_model=DistrictDashboard)
async def get_district_dashboard(
    district_id: str = Path(...),
    deps: tuple = Depends(get_dashboard_services),
    user: dict[str, Any] = Depends(require_roles("district_admin", "system_admin"))
):
    """Retrieve district-wide metric aggregations for the District Health Intelligence portal."""
    _, _, _, dist_repo = deps
    
    # Get District base details
    dist = await dist_repo.find_by_id(district_id)
    dist_name = dist.get("name", "District Dashboard") if dist else "District Dashboard"

    # Aggregated metrics
    stats = await dist_repo.get_aggregated_stats(district_id)
    
    return DistrictDashboard(
        district_id=district_id,
        district_name=dist_name,
        total_hospitals=stats["total_hospitals"],
        total_patients_today=stats["total_beds"] - stats["available_beds"], # dummy calculation
        average_hmi_score=stats["average_hmi_score"],
        hospitals_below_threshold=0,
        total_ambulances=0,
        total_available_beds=stats["available_beds"],
        disease_trends=[],
        hospital_rankings=[],
    )
