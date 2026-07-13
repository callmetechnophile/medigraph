"""Patient endpoints — registration, records, prescriptions, and access control."""

from __future__ import annotations

from typing import Any
from fastapi import APIRouter, Depends, Query, Path
from neo4j import AsyncDriver

from app.database.connection import get_driver
from app.repositories.patient_repository import PatientRepository
from app.services.patient_service import PatientService
from app.schemas import (
    PatientCreate,
    PatientUpdate,
    PatientResponse,
    PaginatedResponse,
    MedicalRecordCreate,
    MedicalRecordResponse,
    PrescriptionCreate,
    PrescriptionResponse,
    DiagnosisCreate,
    DiagnosisResponse,
    GrantAccessRequest,
    SuccessResponse,
)
from app.auth.dependencies import get_current_user, require_roles

router = APIRouter(prefix="/patients", tags=["Patients"])

# -- DI Helper --
def get_patient_service(driver: AsyncDriver = Depends(get_driver)) -> PatientService:
    repo = PatientRepository(driver)
    return PatientService(repo)

@router.post("", response_model=PatientResponse)
async def register_patient(
    data: PatientCreate,
    service: PatientService = Depends(get_patient_service),
    user: dict[str, Any] = Depends(get_current_user)
):
    """Register a new patient securely linked to their Clerk authentication profile."""
    return await service.register_patient(user["user_id"], data)

@router.get("", response_model=PaginatedResponse[PatientResponse])
async def list_patients(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    search: str = Query(""),
    service: PatientService = Depends(get_patient_service),
    user: dict[str, Any] = Depends(get_current_user)
):
    """List and search patients. Accessible to hospital staff and administrators."""
    return await service.list_patients(skip=skip, limit=limit, search=search)

@router.get("/me", response_model=PatientResponse)
async def get_patient_me(
    service: PatientService = Depends(get_patient_service),
    user: dict[str, Any] = Depends(get_current_user)
):
    """Get the current authenticated patient's profile."""
    return await service.get_patient_by_clerk_id(user["user_id"])

@router.get("/{patient_id}", response_model=PatientResponse)
async def get_patient(
    patient_id: str = Path(..., description="Unique patient identifier"),
    service: PatientService = Depends(get_patient_service),
    user: dict[str, Any] = Depends(get_current_user)
):
    """Get patient profile by ID."""
    return await service.get_patient(patient_id)

@router.put("/{patient_id}", response_model=PatientResponse)
async def update_patient(
    data: PatientUpdate,
    patient_id: str = Path(...),
    service: PatientService = Depends(get_patient_service),
    user: dict[str, Any] = Depends(get_current_user)
):
    """Update patient demographic details."""
    return await service.update_patient(patient_id, data)

@router.delete("/{patient_id}")
async def delete_patient(
    patient_id: str = Path(...),
    service: PatientService = Depends(get_patient_service),
    user: dict[str, Any] = Depends(require_roles("system_admin"))
):
    """Delete a patient profile. Restricted to system administrators."""
    success = await service.delete_patient(patient_id)
    return {"success": success, "message": "Patient deleted successfully."}

# -- Subgraph Traversal Routes --

@router.get("/{patient_id}/medical-records", response_model=PaginatedResponse[MedicalRecordResponse])
async def get_medical_records(
    patient_id: str = Path(...),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    service: PatientService = Depends(get_patient_service),
    user: dict[str, Any] = Depends(get_current_user)
):
    """Fetch patient medical records history."""
    return await service.get_medical_records(patient_id, skip, limit)

@router.post("/{patient_id}/medical-records", response_model=MedicalRecordResponse)
async def add_medical_record(
    data: MedicalRecordCreate,
    patient_id: str = Path(...),
    service: PatientService = Depends(get_patient_service),
    user: dict[str, Any] = Depends(require_roles("doctor", "system_admin"))
):
    """Add a medical record for a patient. Restricted to doctors."""
    return await service.add_medical_record(patient_id, data)

@router.get("/{patient_id}/prescriptions", response_model=PaginatedResponse[PrescriptionResponse])
async def get_prescriptions(
    patient_id: str = Path(...),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    service: PatientService = Depends(get_patient_service),
    user: dict[str, Any] = Depends(get_current_user)
):
    """Fetch patient prescription history."""
    return await service.get_prescriptions(patient_id, skip, limit)

@router.post("/{patient_id}/prescriptions", response_model=PrescriptionResponse)
async def add_prescription(
    data: PrescriptionCreate,
    patient_id: str = Path(...),
    service: PatientService = Depends(get_patient_service),
    user: dict[str, Any] = Depends(require_roles("doctor", "system_admin"))
):
    """Write a new prescription. Restricted to doctors."""
    return await service.add_prescription(patient_id, data)

@router.get("/{patient_id}/diagnoses", response_model=PaginatedResponse[DiagnosisResponse])
async def get_diagnoses(
    patient_id: str = Path(...),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    service: PatientService = Depends(get_patient_service),
    user: dict[str, Any] = Depends(get_current_user)
):
    """Fetch diagnosed clinical conditions."""
    return await service.get_diagnoses(patient_id, skip, limit)

@router.post("/{patient_id}/diagnoses", response_model=DiagnosisResponse)
async def add_diagnosis(
    data: DiagnosisCreate,
    patient_id: str = Path(...),
    service: PatientService = Depends(get_patient_service),
    user: dict[str, Any] = Depends(require_roles("doctor", "system_admin"))
):
    """Record a clinical diagnosis. Restricted to doctors."""
    return await service.add_diagnosis(patient_id, data)

# -- Access Control Grants --

@router.post("/{patient_id}/grant-access")
async def grant_access(
    data: GrantAccessRequest,
    patient_id: str = Path(...),
    service: PatientService = Depends(get_patient_service),
    user: dict[str, Any] = Depends(get_current_user)
):
    """Grant access permissions to a hospital."""
    return await service.grant_access(patient_id, data.hospital_id, data.access_level, data.expires_at)

@router.delete("/{patient_id}/revoke-access/{hospital_id}")
async def revoke_access(
    patient_id: str = Path(...),
    hospital_id: str = Path(...),
    service: PatientService = Depends(get_patient_service),
    user: dict[str, Any] = Depends(get_current_user)
):
    """Revoke access permissions from a hospital."""
    return await service.revoke_access(patient_id, hospital_id)
