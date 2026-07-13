"""Pydantic domain models for all Neo4j node types."""

from __future__ import annotations

from datetime import date, datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field

from app.utils.helpers import generate_id, utc_now


# ═══════════════════════════════════════════════════════════════
# Enums
# ═══════════════════════════════════════════════════════════════

class Gender(str, Enum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"


class BloodGroup(str, Enum):
    A_POS = "A+"
    A_NEG = "A-"
    B_POS = "B+"
    B_NEG = "B-"
    AB_POS = "AB+"
    AB_NEG = "AB-"
    O_POS = "O+"
    O_NEG = "O-"


class UserRole(str, Enum):
    PATIENT = "patient"
    DOCTOR = "doctor"
    HOSPITAL_STAFF = "hospital_staff"
    HOSPITAL_ADMIN = "hospital_admin"
    DISTRICT_ADMIN = "district_admin"
    SYSTEM_ADMIN = "system_admin"


class AmbulanceStatus(str, Enum):
    AVAILABLE = "available"
    DISPATCHED = "dispatched"
    EN_ROUTE = "en_route"
    AT_SCENE = "at_scene"
    RETURNING = "returning"
    MAINTENANCE = "maintenance"
    OUT_OF_SERVICE = "out_of_service"


class EquipmentStatus(str, Enum):
    OPERATIONAL = "operational"
    NEEDS_MAINTENANCE = "needs_maintenance"
    UNDER_MAINTENANCE = "under_maintenance"
    OUT_OF_ORDER = "out_of_order"
    DECOMMISSIONED = "decommissioned"


class NotificationPriority(str, Enum):
    INFORMATION = "information"
    WARNING = "warning"
    CRITICAL = "critical"


class NotificationSource(str, Enum):
    INVENTORY = "inventory"
    ATTENDANCE = "attendance"
    DIAGNOSTICS = "diagnostics"
    PATIENTS = "patients"
    REPORTS = "reports"
    AI = "ai"
    WORKFLOW = "workflow"
    SYSTEM = "system"


class RecommendationStatus(str, Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    DISMISSED = "dismissed"
    EXPIRED = "expired"


class RecommendationPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ReportType(str, Enum):
    INVENTORY = "inventory"
    ATTENDANCE = "attendance"
    OPERATIONAL = "operational"
    FORECAST = "forecast"
    PERFORMANCE = "performance"
    DISTRICT = "district"


class ReportFormat(str, Enum):
    PDF = "pdf"
    CSV = "csv"
    EXCEL = "excel"


class AttendanceStatus(str, Enum):
    PRESENT = "present"
    ABSENT = "absent"
    LATE = "late"
    HALF_DAY = "half_day"
    ON_LEAVE = "on_leave"


# ═══════════════════════════════════════════════════════════════
# Base Model
# ═══════════════════════════════════════════════════════════════

class NodeBase(BaseModel):
    """Base for all Neo4j node models."""
    id: str = Field(default_factory=generate_id)
    created_at: str = Field(default_factory=utc_now)
    updated_at: str = Field(default_factory=utc_now)


# ═══════════════════════════════════════════════════════════════
# Patient
# ═══════════════════════════════════════════════════════════════

class Patient(NodeBase):
    clerk_user_id: str = ""
    name: str
    date_of_birth: str = ""
    gender: Gender = Gender.OTHER
    blood_group: Optional[BloodGroup] = None
    phone: str = ""
    email: str = ""
    address: str = ""
    emergency_contact_name: str = ""
    emergency_contact_phone: str = ""
    allergies: list[str] = Field(default_factory=list)
    chronic_conditions: list[str] = Field(default_factory=list)
    is_active: bool = True


# ═══════════════════════════════════════════════════════════════
# Hospital
# ═══════════════════════════════════════════════════════════════

class Hospital(NodeBase):
    name: str
    registration_number: str = ""
    hospital_type: str = ""  # government, private, trust
    address: str = ""
    city: str = ""
    state: str = ""
    pincode: str = ""
    phone: str = ""
    email: str = ""
    website: str = ""
    total_beds: int = 0
    available_beds: int = 0
    icu_beds: int = 0
    ventilators: int = 0
    is_active: bool = True


# ═══════════════════════════════════════════════════════════════
# Department
# ═══════════════════════════════════════════════════════════════

class Department(NodeBase):
    name: str
    description: str = ""
    head_doctor_id: Optional[str] = None
    floor: str = ""
    is_active: bool = True


# ═══════════════════════════════════════════════════════════════
# Doctor
# ═══════════════════════════════════════════════════════════════

class Doctor(NodeBase):
    clerk_user_id: str = ""
    name: str
    specialization: str = ""
    qualification: str = ""
    license_number: str = ""
    phone: str = ""
    email: str = ""
    experience_years: int = 0
    consultation_fee: float = 0.0
    is_available: bool = True
    is_active: bool = True


# ═══════════════════════════════════════════════════════════════
# Medicine
# ═══════════════════════════════════════════════════════════════

class Medicine(NodeBase):
    name: str
    generic_name: str = ""
    manufacturer: str = ""
    category: str = ""  # antibiotic, painkiller, etc.
    unit: str = "tablet"  # tablet, ml, mg, capsule
    price_per_unit: float = 0.0
    requires_prescription: bool = True
    description: str = ""


# ═══════════════════════════════════════════════════════════════
# Inventory
# ═══════════════════════════════════════════════════════════════

class Inventory(NodeBase):
    medicine_id: str
    hospital_id: str
    current_stock: int = 0
    minimum_stock: int = 10
    maximum_stock: int = 1000
    reorder_level: int = 20
    batch_number: str = ""
    expiry_date: str = ""
    last_restocked_at: str = ""
    unit_cost: float = 0.0


# ═══════════════════════════════════════════════════════════════
# Attendance
# ═══════════════════════════════════════════════════════════════

class Attendance(NodeBase):
    staff_id: str
    hospital_id: str
    department_id: str = ""
    date: str = ""  # YYYY-MM-DD
    check_in: str = ""
    check_out: str = ""
    status: AttendanceStatus = AttendanceStatus.PRESENT
    hours_worked: float = 0.0
    notes: str = ""


# ═══════════════════════════════════════════════════════════════
# Medical Record
# ═══════════════════════════════════════════════════════════════

class MedicalRecord(NodeBase):
    patient_id: str
    hospital_id: str = ""
    doctor_id: str = ""
    visit_date: str = ""
    chief_complaint: str = ""
    symptoms: list[str] = Field(default_factory=list)
    examination_notes: str = ""
    vital_signs: dict[str, Any] = Field(default_factory=dict)
    follow_up_date: str = ""
    notes: str = ""


# ═══════════════════════════════════════════════════════════════
# Prescription
# ═══════════════════════════════════════════════════════════════

class Prescription(NodeBase):
    patient_id: str
    doctor_id: str
    hospital_id: str = ""
    medical_record_id: str = ""
    medicines: list[dict[str, Any]] = Field(default_factory=list)
    # Each medicine: {medicine_id, name, dosage, frequency, duration, instructions}
    diagnosis_summary: str = ""
    notes: str = ""
    is_active: bool = True


# ═══════════════════════════════════════════════════════════════
# Diagnosis
# ═══════════════════════════════════════════════════════════════

class Diagnosis(NodeBase):
    patient_id: str
    doctor_id: str
    hospital_id: str = ""
    medical_record_id: str = ""
    icd_code: str = ""
    condition_name: str
    severity: str = "moderate"  # mild, moderate, severe, critical
    description: str = ""
    is_confirmed: bool = False
    diagnosed_at: str = ""


# ═══════════════════════════════════════════════════════════════
# Laboratory Report
# ═══════════════════════════════════════════════════════════════

class LaboratoryReport(NodeBase):
    patient_id: str
    doctor_id: str = ""
    hospital_id: str = ""
    test_name: str
    test_category: str = ""
    sample_type: str = ""  # blood, urine, tissue, etc.
    results: dict[str, Any] = Field(default_factory=dict)
    reference_range: dict[str, Any] = Field(default_factory=dict)
    is_abnormal: bool = False
    notes: str = ""
    reported_at: str = ""
    equipment_id: str = ""


# ═══════════════════════════════════════════════════════════════
# Imaging Report
# ═══════════════════════════════════════════════════════════════

class ImagingReport(NodeBase):
    patient_id: str
    doctor_id: str = ""
    hospital_id: str = ""
    imaging_type: str = ""  # X-Ray, CT, MRI, Ultrasound
    body_part: str = ""
    findings: str = ""
    impression: str = ""
    image_urls: list[str] = Field(default_factory=list)
    equipment_id: str = ""
    technician_id: str = ""
    reported_at: str = ""


# ═══════════════════════════════════════════════════════════════
# Diagnostic Equipment
# ═══════════════════════════════════════════════════════════════

class DiagnosticEquipment(NodeBase):
    hospital_id: str
    name: str
    equipment_type: str = ""  # X-Ray, CT Scanner, MRI, Ventilator
    manufacturer: str = ""
    model_number: str = ""
    serial_number: str = ""
    purchase_date: str = ""
    last_maintenance_date: str = ""
    next_maintenance_date: str = ""
    status: EquipmentStatus = EquipmentStatus.OPERATIONAL
    usage_hours: float = 0.0
    location: str = ""
    department_id: str = ""


# ═══════════════════════════════════════════════════════════════
# Ambulance
# ═══════════════════════════════════════════════════════════════

class Ambulance(NodeBase):
    hospital_id: str
    vehicle_number: str
    vehicle_type: str = "basic"  # basic, advanced, icu_on_wheels
    driver_name: str = ""
    driver_phone: str = ""
    status: AmbulanceStatus = AmbulanceStatus.AVAILABLE
    current_location: str = ""
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    last_service_date: str = ""
    is_equipped_with_oxygen: bool = True
    is_equipped_with_defibrillator: bool = False


# ═══════════════════════════════════════════════════════════════
# Notification
# ═══════════════════════════════════════════════════════════════

class Notification(NodeBase):
    recipient_id: str
    recipient_type: str = "user"  # user, hospital, department
    title: str
    message: str
    priority: NotificationPriority = NotificationPriority.INFORMATION
    source: NotificationSource = NotificationSource.SYSTEM
    source_id: str = ""
    is_read: bool = False
    read_at: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)


# ═══════════════════════════════════════════════════════════════
# Recommendation
# ═══════════════════════════════════════════════════════════════

class Recommendation(NodeBase):
    hospital_id: str
    category: str = ""  # inventory, attendance, equipment, patient_flow, etc.
    title: str
    description: str = ""
    prediction: str = ""
    reason: str = ""
    confidence: float = 0.0
    priority: RecommendationPriority = RecommendationPriority.MEDIUM
    expected_impact: str = ""
    suggested_action: str = ""
    status: RecommendationStatus = RecommendationStatus.PENDING
    expires_at: Optional[str] = None
    acted_on_at: Optional[str] = None
    acted_on_by: Optional[str] = None


# ═══════════════════════════════════════════════════════════════
# HMI Score
# ═══════════════════════════════════════════════════════════════

class HMIScore(NodeBase):
    hospital_id: str
    overall_score: float = 0.0
    inventory_score: float = 0.0
    attendance_score: float = 0.0
    patient_load_score: float = 0.0
    diagnostics_score: float = 0.0
    equipment_health_score: float = 0.0
    ambulance_readiness_score: float = 0.0
    infrastructure_score: float = 0.0
    operational_compliance_score: float = 0.0
    calculated_at: str = Field(default_factory=utc_now)
    period: str = "daily"  # daily, weekly, monthly
    department_contributions: dict[str, float] = Field(default_factory=dict)
    recommendations: list[str] = Field(default_factory=list)


# ═══════════════════════════════════════════════════════════════
# District / State / Country (Geography Hierarchy)
# ═══════════════════════════════════════════════════════════════

class District(NodeBase):
    name: str
    code: str = ""
    state_id: str = ""
    population: int = 0
    area_sq_km: float = 0.0
    district_health_officer: str = ""
    contact_phone: str = ""
    contact_email: str = ""


class State(NodeBase):
    name: str
    code: str = ""
    country_id: str = ""


class Country(NodeBase):
    name: str
    code: str = ""


# ═══════════════════════════════════════════════════════════════
# Report (metadata — actual files stored in Supabase)
# ═══════════════════════════════════════════════════════════════

class Report(NodeBase):
    hospital_id: str = ""
    district_id: str = ""
    report_type: ReportType = ReportType.OPERATIONAL
    report_format: ReportFormat = ReportFormat.PDF
    title: str = ""
    description: str = ""
    file_url: str = ""  # Supabase Storage URL
    file_size_bytes: int = 0
    generated_by: str = ""
    period_start: str = ""
    period_end: str = ""
    parameters: dict[str, Any] = Field(default_factory=dict)
