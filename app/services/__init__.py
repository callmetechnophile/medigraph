"""Services Package."""

from app.services.patient_service import PatientService
from app.services.hospital_service import HospitalService
from app.services.inventory_service import InventoryService
from app.services.attendance_service import AttendanceService
from app.services.diagnostics_service import DiagnosticsService
from app.services.ambulance_service import AmbulanceService
from app.services.report_service import ReportService
from app.services.notification_service import NotificationService
from app.services.recommendation_service import RecommendationService
from app.services.hmi_service import HMIService
from app.services.voice_service import VoiceService
from app.services.workflow_service import WorkflowService

__all__ = [
    "PatientService",
    "HospitalService",
    "InventoryService",
    "AttendanceService",
    "DiagnosticsService",
    "AmbulanceService",
    "ReportService",
    "NotificationService",
    "RecommendationService",
    "HMIService",
    "VoiceService",
    "WorkflowService",
]
