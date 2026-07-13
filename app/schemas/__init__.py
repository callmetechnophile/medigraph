"""Request / Response schemas for all API endpoints."""

from __future__ import annotations

from typing import Any, Generic, Optional, TypeVar

from pydantic import BaseModel, Field

from app.models import (
    AmbulanceStatus,
    AttendanceStatus,
    BloodGroup,
    EquipmentStatus,
    Gender,
    NotificationPriority,
    NotificationSource,
    RecommendationPriority,
    RecommendationStatus,
    ReportFormat,
    ReportType,
)

T = TypeVar("T")


# ═══════════════════════════════════════════════════════════════
# Common / Shared Schemas
# ═══════════════════════════════════════════════════════════════

class PaginatedResponse(BaseModel, Generic[T]):
    """Standard paginated list response."""
    items: list[T]
    total: int
    skip: int
    limit: int
    has_more: bool


class ErrorResponse(BaseModel):
    detail: str
    error_code: str = ""
    timestamp: str = ""


class SuccessResponse(BaseModel):
    message: str
    data: dict[str, Any] = Field(default_factory=dict)


class FilterParams(BaseModel):
    skip: int = Field(default=0, ge=0)
    limit: int = Field(default=20, ge=1, le=100)
    sort_by: str = "created_at"
    sort_order: str = "desc"  # asc or desc
    search: str = ""


class DateRangeFilter(BaseModel):
    start_date: str = ""
    end_date: str = ""


# ═══════════════════════════════════════════════════════════════
# Patient Schemas
# ═══════════════════════════════════════════════════════════════

class PatientCreate(BaseModel):
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


class PatientUpdate(BaseModel):
    name: Optional[str] = None
    date_of_birth: Optional[str] = None
    gender: Optional[Gender] = None
    blood_group: Optional[BloodGroup] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    allergies: Optional[list[str]] = None
    chronic_conditions: Optional[list[str]] = None


class PatientResponse(BaseModel):
    id: str
    clerk_user_id: str = ""
    name: str
    date_of_birth: str = ""
    gender: str = ""
    blood_group: Optional[str] = None
    phone: str = ""
    email: str = ""
    address: str = ""
    emergency_contact_name: str = ""
    emergency_contact_phone: str = ""
    allergies: list[str] = Field(default_factory=list)
    chronic_conditions: list[str] = Field(default_factory=list)
    is_active: bool = True
    created_at: str = ""
    updated_at: str = ""


class GrantAccessRequest(BaseModel):
    hospital_id: str
    access_level: str = "read"  # read, write, full
    expires_at: Optional[str] = None


# ═══════════════════════════════════════════════════════════════
# Medical Record Schemas
# ═══════════════════════════════════════════════════════════════

class MedicalRecordCreate(BaseModel):
    hospital_id: str = ""
    doctor_id: str = ""
    visit_date: str = ""
    chief_complaint: str = ""
    symptoms: list[str] = Field(default_factory=list)
    examination_notes: str = ""
    vital_signs: dict[str, Any] = Field(default_factory=dict)
    follow_up_date: str = ""
    notes: str = ""


class MedicalRecordResponse(BaseModel):
    id: str
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
    created_at: str = ""
    updated_at: str = ""


# ═══════════════════════════════════════════════════════════════
# Prescription Schemas
# ═══════════════════════════════════════════════════════════════

class PrescriptionCreate(BaseModel):
    doctor_id: str
    hospital_id: str = ""
    medical_record_id: str = ""
    medicines: list[dict[str, Any]] = Field(default_factory=list)
    diagnosis_summary: str = ""
    notes: str = ""


class PrescriptionResponse(BaseModel):
    id: str
    patient_id: str
    doctor_id: str
    hospital_id: str = ""
    medical_record_id: str = ""
    medicines: list[dict[str, Any]] = Field(default_factory=list)
    diagnosis_summary: str = ""
    notes: str = ""
    is_active: bool = True
    created_at: str = ""
    updated_at: str = ""


# ═══════════════════════════════════════════════════════════════
# Diagnosis Schemas
# ═══════════════════════════════════════════════════════════════

class DiagnosisCreate(BaseModel):
    doctor_id: str
    hospital_id: str = ""
    medical_record_id: str = ""
    icd_code: str = ""
    condition_name: str
    severity: str = "moderate"
    description: str = ""
    is_confirmed: bool = False


class DiagnosisResponse(BaseModel):
    id: str
    patient_id: str
    doctor_id: str
    hospital_id: str = ""
    medical_record_id: str = ""
    icd_code: str = ""
    condition_name: str = ""
    severity: str = ""
    description: str = ""
    is_confirmed: bool = False
    diagnosed_at: str = ""
    created_at: str = ""
    updated_at: str = ""


# ═══════════════════════════════════════════════════════════════
# Hospital Schemas
# ═══════════════════════════════════════════════════════════════

class HospitalCreate(BaseModel):
    name: str
    registration_number: str = ""
    hospital_type: str = ""
    address: str = ""
    city: str = ""
    state: str = ""
    pincode: str = ""
    phone: str = ""
    email: str = ""
    website: str = ""
    total_beds: int = 0
    icu_beds: int = 0
    ventilators: int = 0


class HospitalUpdate(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    total_beds: Optional[int] = None
    available_beds: Optional[int] = None
    icu_beds: Optional[int] = None
    ventilators: Optional[int] = None


class HospitalResponse(BaseModel):
    id: str
    name: str
    registration_number: str = ""
    hospital_type: str = ""
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
    created_at: str = ""
    updated_at: str = ""


class DepartmentCreate(BaseModel):
    name: str
    description: str = ""
    head_doctor_id: Optional[str] = None
    floor: str = ""


class DepartmentResponse(BaseModel):
    id: str
    name: str
    description: str = ""
    head_doctor_id: Optional[str] = None
    floor: str = ""
    is_active: bool = True
    created_at: str = ""
    updated_at: str = ""


class DoctorCreate(BaseModel):
    name: str
    specialization: str = ""
    qualification: str = ""
    license_number: str = ""
    phone: str = ""
    email: str = ""
    experience_years: int = 0
    consultation_fee: float = 0.0


class DoctorResponse(BaseModel):
    id: str
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
    created_at: str = ""
    updated_at: str = ""


# ═══════════════════════════════════════════════════════════════
# Inventory Schemas
# ═══════════════════════════════════════════════════════════════

class InventoryItemCreate(BaseModel):
    medicine_id: str
    current_stock: int = 0
    minimum_stock: int = 10
    maximum_stock: int = 1000
    reorder_level: int = 20
    batch_number: str = ""
    expiry_date: str = ""
    unit_cost: float = 0.0


class InventoryItemUpdate(BaseModel):
    current_stock: Optional[int] = None
    minimum_stock: Optional[int] = None
    maximum_stock: Optional[int] = None
    reorder_level: Optional[int] = None
    batch_number: Optional[str] = None
    expiry_date: Optional[str] = None
    unit_cost: Optional[float] = None


class InventoryResponse(BaseModel):
    id: str
    medicine_id: str
    hospital_id: str
    medicine_name: str = ""
    current_stock: int = 0
    minimum_stock: int = 10
    maximum_stock: int = 1000
    reorder_level: int = 20
    batch_number: str = ""
    expiry_date: str = ""
    last_restocked_at: str = ""
    unit_cost: float = 0.0
    is_low_stock: bool = False
    created_at: str = ""
    updated_at: str = ""


class BatchStockUpdate(BaseModel):
    """For voice-command-driven batch stock updates."""
    updates: list[dict[str, Any]]
    # Each: {medicine_name: str, new_stock: int} or {inventory_id: str, new_stock: int}


class MedicineCreate(BaseModel):
    name: str
    generic_name: str = ""
    manufacturer: str = ""
    category: str = ""
    unit: str = "tablet"
    price_per_unit: float = 0.0
    requires_prescription: bool = True
    description: str = ""


class MedicineResponse(BaseModel):
    id: str
    name: str
    generic_name: str = ""
    manufacturer: str = ""
    category: str = ""
    unit: str = "tablet"
    price_per_unit: float = 0.0
    requires_prescription: bool = True
    description: str = ""
    created_at: str = ""
    updated_at: str = ""


# ═══════════════════════════════════════════════════════════════
# Attendance Schemas
# ═══════════════════════════════════════════════════════════════

class AttendanceCheckIn(BaseModel):
    staff_id: str
    department_id: str = ""
    notes: str = ""


class AttendanceCheckOut(BaseModel):
    notes: str = ""


class AttendanceResponse(BaseModel):
    id: str
    staff_id: str
    hospital_id: str
    department_id: str = ""
    date: str = ""
    check_in: str = ""
    check_out: str = ""
    status: str = ""
    hours_worked: float = 0.0
    notes: str = ""
    created_at: str = ""
    updated_at: str = ""


class AttendanceSummary(BaseModel):
    total_staff: int = 0
    present: int = 0
    absent: int = 0
    late: int = 0
    on_leave: int = 0
    attendance_rate: float = 0.0
    date: str = ""


# ═══════════════════════════════════════════════════════════════
# Diagnostics Schemas
# ═══════════════════════════════════════════════════════════════

class EquipmentCreate(BaseModel):
    name: str
    equipment_type: str = ""
    manufacturer: str = ""
    model_number: str = ""
    serial_number: str = ""
    purchase_date: str = ""
    location: str = ""
    department_id: str = ""


class EquipmentUpdate(BaseModel):
    status: Optional[EquipmentStatus] = None
    last_maintenance_date: Optional[str] = None
    next_maintenance_date: Optional[str] = None
    usage_hours: Optional[float] = None
    location: Optional[str] = None


class EquipmentResponse(BaseModel):
    id: str
    hospital_id: str
    name: str
    equipment_type: str = ""
    manufacturer: str = ""
    model_number: str = ""
    serial_number: str = ""
    purchase_date: str = ""
    last_maintenance_date: str = ""
    next_maintenance_date: str = ""
    status: str = ""
    usage_hours: float = 0.0
    location: str = ""
    department_id: str = ""
    created_at: str = ""
    updated_at: str = ""


class LabReportCreate(BaseModel):
    patient_id: str
    doctor_id: str = ""
    test_name: str
    test_category: str = ""
    sample_type: str = ""
    results: dict[str, Any] = Field(default_factory=dict)
    reference_range: dict[str, Any] = Field(default_factory=dict)
    is_abnormal: bool = False
    notes: str = ""
    equipment_id: str = ""


class LabReportResponse(BaseModel):
    id: str
    patient_id: str
    doctor_id: str = ""
    hospital_id: str = ""
    test_name: str = ""
    test_category: str = ""
    sample_type: str = ""
    results: dict[str, Any] = Field(default_factory=dict)
    reference_range: dict[str, Any] = Field(default_factory=dict)
    is_abnormal: bool = False
    notes: str = ""
    reported_at: str = ""
    equipment_id: str = ""
    created_at: str = ""
    updated_at: str = ""


class ImagingReportCreate(BaseModel):
    patient_id: str
    doctor_id: str = ""
    imaging_type: str = ""
    body_part: str = ""
    findings: str = ""
    impression: str = ""
    equipment_id: str = ""
    technician_id: str = ""


class ImagingReportResponse(BaseModel):
    id: str
    patient_id: str
    doctor_id: str = ""
    hospital_id: str = ""
    imaging_type: str = ""
    body_part: str = ""
    findings: str = ""
    impression: str = ""
    image_urls: list[str] = Field(default_factory=list)
    equipment_id: str = ""
    technician_id: str = ""
    reported_at: str = ""
    created_at: str = ""
    updated_at: str = ""


# ═══════════════════════════════════════════════════════════════
# Ambulance Schemas
# ═══════════════════════════════════════════════════════════════

class AmbulanceCreate(BaseModel):
    vehicle_number: str
    vehicle_type: str = "basic"
    driver_name: str = ""
    driver_phone: str = ""
    is_equipped_with_oxygen: bool = True
    is_equipped_with_defibrillator: bool = False


class AmbulanceUpdate(BaseModel):
    status: Optional[AmbulanceStatus] = None
    driver_name: Optional[str] = None
    driver_phone: Optional[str] = None
    current_location: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class AmbulanceResponse(BaseModel):
    id: str
    hospital_id: str
    vehicle_number: str
    vehicle_type: str = ""
    driver_name: str = ""
    driver_phone: str = ""
    status: str = ""
    current_location: str = ""
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    last_service_date: str = ""
    is_equipped_with_oxygen: bool = True
    is_equipped_with_defibrillator: bool = False
    created_at: str = ""
    updated_at: str = ""


class AmbulanceDispatchRequest(BaseModel):
    destination: str
    patient_id: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    emergency_type: str = "general"
    notes: str = ""


# ═══════════════════════════════════════════════════════════════
# Notification Schemas
# ═══════════════════════════════════════════════════════════════

class NotificationCreate(BaseModel):
    recipient_id: str
    recipient_type: str = "user"
    title: str
    message: str
    priority: NotificationPriority = NotificationPriority.INFORMATION
    source: NotificationSource = NotificationSource.SYSTEM
    source_id: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)


class NotificationResponse(BaseModel):
    id: str
    recipient_id: str
    recipient_type: str = ""
    title: str = ""
    message: str = ""
    priority: str = ""
    source: str = ""
    source_id: str = ""
    is_read: bool = False
    read_at: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: str = ""


class NotificationCount(BaseModel):
    total: int = 0
    unread: int = 0
    critical: int = 0
    warning: int = 0
    information: int = 0


class MarkReadRequest(BaseModel):
    notification_ids: list[str]


# ═══════════════════════════════════════════════════════════════
# Recommendation Schemas
# ═══════════════════════════════════════════════════════════════

class RecommendationResponse(BaseModel):
    id: str
    hospital_id: str
    category: str = ""
    title: str = ""
    description: str = ""
    prediction: str = ""
    reason: str = ""
    confidence: float = 0.0
    priority: str = ""
    expected_impact: str = ""
    suggested_action: str = ""
    status: str = ""
    expires_at: Optional[str] = None
    created_at: str = ""
    updated_at: str = ""


class RecommendationActionRequest(BaseModel):
    action: str  # "accept" or "dismiss"
    notes: str = ""


# ═══════════════════════════════════════════════════════════════
# Report Schemas
# ═══════════════════════════════════════════════════════════════

class ReportGenerateRequest(BaseModel):
    report_type: ReportType
    report_format: ReportFormat = ReportFormat.PDF
    hospital_id: str = ""
    district_id: str = ""
    period_start: str = ""
    period_end: str = ""
    title: str = ""
    parameters: dict[str, Any] = Field(default_factory=dict)


class ReportResponse(BaseModel):
    id: str
    hospital_id: str = ""
    district_id: str = ""
    report_type: str = ""
    report_format: str = ""
    title: str = ""
    description: str = ""
    file_url: str = ""
    file_size_bytes: int = 0
    generated_by: str = ""
    period_start: str = ""
    period_end: str = ""
    created_at: str = ""


# ═══════════════════════════════════════════════════════════════
# HMI Schemas
# ═══════════════════════════════════════════════════════════════

class HMIScoreResponse(BaseModel):
    id: str
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
    calculated_at: str = ""
    period: str = ""
    department_contributions: dict[str, float] = Field(default_factory=dict)
    recommendations: list[str] = Field(default_factory=list)


class HMITrendResponse(BaseModel):
    hospital_id: str
    scores: list[HMIScoreResponse]
    trend_direction: str = ""  # improving, declining, stable
    average_score: float = 0.0


# ═══════════════════════════════════════════════════════════════
# Voice Schemas
# ═══════════════════════════════════════════════════════════════

class VoiceCommandRequest(BaseModel):
    language_code: str = "hi-IN"
    hospital_id: str = ""


class VoiceCommandResponse(BaseModel):
    transcript: str = ""
    intent: str = ""
    entities: dict[str, Any] = Field(default_factory=dict)
    action_result: dict[str, Any] = Field(default_factory=dict)
    response_text: str = ""
    response_audio_base64: str = ""
    success: bool = True


class TTSRequest(BaseModel):
    text: str
    language_code: str = "hi-IN"
    speaker: str = "meera"


class TTSResponse(BaseModel):
    audio_base64: str
    language_code: str = ""


# ═══════════════════════════════════════════════════════════════
# Dashboard Schemas
# ═══════════════════════════════════════════════════════════════

class HospitalDashboard(BaseModel):
    hospital_id: str
    hospital_name: str = ""
    total_patients_today: int = 0
    total_staff_present: int = 0
    available_beds: int = 0
    total_beds: int = 0
    bed_occupancy_rate: float = 0.0
    ambulances_available: int = 0
    ambulances_total: int = 0
    low_stock_items: int = 0
    critical_notifications: int = 0
    hmi_score: float = 0.0
    recent_notifications: list[NotificationResponse] = Field(default_factory=list)
    department_summary: list[dict[str, Any]] = Field(default_factory=list)


class DistrictDashboard(BaseModel):
    district_id: str
    district_name: str = ""
    total_hospitals: int = 0
    total_patients_today: int = 0
    average_hmi_score: float = 0.0
    hospitals_below_threshold: int = 0
    total_ambulances: int = 0
    total_available_beds: int = 0
    disease_trends: list[dict[str, Any]] = Field(default_factory=list)
    hospital_rankings: list[dict[str, Any]] = Field(default_factory=list)


# ═══════════════════════════════════════════════════════════════
# District Schemas
# ═══════════════════════════════════════════════════════════════

class DistrictCreate(BaseModel):
    name: str
    code: str = ""
    state_id: str = ""
    population: int = 0
    area_sq_km: float = 0.0
    district_health_officer: str = ""
    contact_phone: str = ""
    contact_email: str = ""


class DistrictResponse(BaseModel):
    id: str
    name: str
    code: str = ""
    state_id: str = ""
    population: int = 0
    area_sq_km: float = 0.0
    district_health_officer: str = ""
    contact_phone: str = ""
    contact_email: str = ""
    created_at: str = ""
    updated_at: str = ""


# ═══════════════════════════════════════════════════════════════
# Workflow Schemas
# ═══════════════════════════════════════════════════════════════

class WorkflowTriggerRequest(BaseModel):
    workflow_type: str
    hospital_id: str = ""
    parameters: dict[str, Any] = Field(default_factory=dict)


class WorkflowStatusResponse(BaseModel):
    id: str
    workflow_type: str = ""
    status: str = ""  # pending, running, completed, failed
    started_at: str = ""
    completed_at: str = ""
    result: dict[str, Any] = Field(default_factory=dict)
    error: str = ""


# ═══════════════════════════════════════════════════════════════
# AI Prediction Schemas
# ═══════════════════════════════════════════════════════════════

class PredictionResponse(BaseModel):
    prediction: str
    reason: str
    confidence: float
    priority: str
    expected_impact: str
    suggested_action: str
    metadata: dict[str, Any] = Field(default_factory=dict)
