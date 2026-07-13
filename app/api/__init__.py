"""API Route Sub-routers gateway index."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.health import router as health_router
from app.api.patients import router as patients_router
from app.api.hospitals import router as hospitals_router
from app.api.inventory import router as inventory_router
from app.api.attendance import router as attendance_router
from app.api.diagnostics import router as diagnostics_router
from app.api.ambulances import router as ambulances_router
from app.api.reports import router as reports_router
from app.api.notifications import router as notifications_router
from app.api.recommendations import router as recommendations_router
from app.api.voice import router as voice_router
from app.api.workflow import router as workflow_router
from app.api.hmi import router as hmi_router
from app.api.dashboard import router as dashboard_router

api_router = APIRouter(prefix="/api/v1")

# Include subrouters
api_router.include_router(health_router)
api_router.include_router(patients_router)
api_router.include_router(hospitals_router)
api_router.include_router(inventory_router)
api_router.include_router(attendance_router)
api_router.include_router(diagnostics_router)
api_router.include_router(ambulances_router)
api_router.include_router(reports_router)
api_router.include_router(notifications_router)
api_router.include_router(recommendations_router)
api_router.include_router(voice_router)
api_router.include_router(workflow_router)
api_router.include_router(hmi_router)
api_router.include_router(dashboard_router)
