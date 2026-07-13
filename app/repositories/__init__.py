"""Repositories Package."""

from app.repositories.base_repository import BaseRepository
from app.repositories.patient_repository import PatientRepository
from app.repositories.hospital_repository import HospitalRepository
from app.repositories.inventory_repository import InventoryRepository
from app.repositories.attendance_repository import AttendanceRepository
from app.repositories.diagnostics_repository import (
    EquipmentRepository,
    LabReportRepository,
    ImagingReportRepository,
)
from app.repositories.ambulance_repository import AmbulanceRepository
from app.repositories.report_repository import ReportRepository
from app.repositories.recommendation_repository import RecommendationRepository
from app.repositories.notification_repository import NotificationRepository
from app.repositories.hmi_repository import HMIRepository
from app.repositories.district_repository import (
    DistrictRepository,
    StateRepository,
    CountryRepository,
)

__all__ = [
    "BaseRepository",
    "PatientRepository",
    "HospitalRepository",
    "InventoryRepository",
    "AttendanceRepository",
    "EquipmentRepository",
    "LabReportRepository",
    "ImagingReportRepository",
    "AmbulanceRepository",
    "ReportRepository",
    "RecommendationRepository",
    "NotificationRepository",
    "HMIRepository",
    "DistrictRepository",
    "StateRepository",
    "CountryRepository",
]
