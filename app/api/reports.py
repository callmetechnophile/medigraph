"""Report endpoints — generation and download routing."""

from __future__ import annotations

from typing import Any
from fastapi import APIRouter, Depends, Query, Path
from neo4j import AsyncDriver

from app.database.connection import get_driver
from app.repositories import ReportRepository
from app.services import ReportService
from app.schemas import (
    ReportGenerateRequest,
    ReportResponse,
    PaginatedResponse,
)
from app.auth.dependencies import get_current_user, require_roles
from app.config import get_settings

router = APIRouter(tags=["Reports"])

def get_report_service(driver: AsyncDriver = Depends(get_driver)) -> ReportService:
    repo = ReportRepository(driver)
    settings = get_settings()
    return ReportService(
        repo,
        supabase_url=settings.supabase_url,
        supabase_key=settings.supabase_key,
        supabase_bucket=settings.supabase_bucket,
        temp_dir=settings.report_temp_dir
    )

@router.post("/reports/generate", response_model=ReportResponse)
async def generate_report(
    data: ReportGenerateRequest,
    service: ReportService = Depends(get_report_service),
    user: dict[str, Any] = Depends(require_roles("hospital_admin", "district_admin", "system_admin"))
):
    """Trigger report compilation and upload to Supabase Storage."""
    return await service.generate_report(user["user_id"], data)

@router.get("/hospitals/{hospital_id}/reports", response_model=PaginatedResponse[ReportResponse])
async def list_reports(
    hospital_id: str = Path(...),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    report_type: str = Query(""),
    service: ReportService = Depends(get_report_service),
    user: dict[str, Any] = Depends(require_roles("hospital_admin", "district_admin", "system_admin"))
):
    """List compiled reports generated for a hospital."""
    return await service.list_reports(hospital_id, skip=skip, limit=limit, report_type=report_type)

@router.get("/reports/{report_id}", response_model=ReportResponse)
async def get_report(
    report_id: str = Path(...),
    service: ReportService = Depends(get_report_service),
    user: dict[str, Any] = Depends(require_roles("hospital_admin", "district_admin", "system_admin"))
):
    """Get metadata for a generated report."""
    return await service.get_report(report_id)
