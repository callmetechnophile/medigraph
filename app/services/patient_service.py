"""Patient service — Orchestrates Patient registration, records, and access."""

from __future__ import annotations

from typing import Any
from fastapi import HTTPException
import structlog

from app.models import Patient
from app.repositories import PatientRepository
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
)

logger = structlog.get_logger(__name__)

class PatientService:
    def __init__(self, patient_repo: PatientRepository):
        self.patient_repo = patient_repo

    async def register_patient(self, clerk_user_id: str, data: PatientCreate) -> PatientResponse:
        # Check if already registered
        existing = await self.patient_repo.find_by_clerk_id(clerk_user_id)
        if existing:
            raise HTTPException(status_code=400, detail="Patient already registered.")
        
        patient_dict = data.model_dump()
        patient_dict["clerk_user_id"] = clerk_user_id
        res = await self.patient_repo.create(patient_dict)
        return PatientResponse(**res)

    async def get_patient(self, patient_id: str) -> PatientResponse:
        res = await self.patient_repo.find_by_id(patient_id)
        if not res:
            raise HTTPException(status_code=404, detail="Patient not found.")
        return PatientResponse(**res)

    async def get_patient_by_clerk_id(self, clerk_user_id: str) -> PatientResponse:
        res = await self.patient_repo.find_by_clerk_id(clerk_user_id)
        if not res:
            raise HTTPException(status_code=404, detail="Patient not found.")
        return PatientResponse(**res)

    async def update_patient(self, patient_id: str, data: PatientUpdate) -> PatientResponse:
        await self.get_patient(patient_id)  # Validate exists
        res = await self.patient_repo.update(patient_id, data.model_dump(exclude_unset=True))
        if not res:
            raise HTTPException(status_code=404, detail="Patient update failed.")
        return PatientResponse(**res)

    async def delete_patient(self, patient_id: str) -> bool:
        await self.get_patient(patient_id)
        return await self.patient_repo.delete(patient_id)

    async def list_patients(self, skip: int = 0, limit: int = 20, sort_by: str = "created_at", sort_order: str = "desc", search: str = "") -> PaginatedResponse[PatientResponse]:
        items, total = await self.patient_repo.find_all(
            skip=skip, limit=limit, sort_by=sort_by, sort_order=sort_order, search=search
        )
        return PaginatedResponse(
            items=[PatientResponse(**i) for i in items],
            total=total,
            skip=skip,
            limit=limit,
            has_more=(skip + limit) < total,
        )

    async def get_medical_records(self, patient_id: str, skip: int = 0, limit: int = 20) -> PaginatedResponse[MedicalRecordResponse]:
        await self.get_patient(patient_id)
        items, total = await self.patient_repo.get_medical_records(patient_id, skip=skip, limit=limit)
        return PaginatedResponse(
            items=[MedicalRecordResponse(**i) for i in items],
            total=total,
            skip=skip,
            limit=limit,
            has_more=(skip + limit) < total,
        )

    async def add_medical_record(self, patient_id: str, data: MedicalRecordCreate) -> MedicalRecordResponse:
        await self.get_patient(patient_id)
        record_dict = data.model_dump()
        record_dict["patient_id"] = patient_id
        res = await self.patient_repo.add_medical_record(patient_id, record_dict)
        return MedicalRecordResponse(**res)

    async def get_prescriptions(self, patient_id: str, skip: int = 0, limit: int = 20) -> PaginatedResponse[PrescriptionResponse]:
        await self.get_patient(patient_id)
        items, total = await self.patient_repo.get_prescriptions(patient_id, skip=skip, limit=limit)
        return PaginatedResponse(
            items=[PrescriptionResponse(**i) for i in items],
            total=total,
            skip=skip,
            limit=limit,
            has_more=(skip + limit) < total,
        )

    async def add_prescription(self, patient_id: str, data: PrescriptionCreate) -> PrescriptionResponse:
        await self.get_patient(patient_id)
        prescription_dict = data.model_dump()
        prescription_dict["patient_id"] = patient_id
        res = await self.patient_repo.add_prescription(patient_id, prescription_dict)
        return PrescriptionResponse(**res)

    async def get_diagnoses(self, patient_id: str, skip: int = 0, limit: int = 20) -> PaginatedResponse[DiagnosisResponse]:
        await self.get_patient(patient_id)
        items, total = await self.patient_repo.get_diagnoses(patient_id, skip=skip, limit=limit)
        return PaginatedResponse(
            items=[DiagnosisResponse(**i) for i in items],
            total=total,
            skip=skip,
            limit=limit,
            has_more=(skip + limit) < total,
        )

    async def add_diagnosis(self, patient_id: str, data: DiagnosisCreate) -> DiagnosisResponse:
        await self.get_patient(patient_id)
        diagnosis_dict = data.model_dump()
        diagnosis_dict["patient_id"] = patient_id
        res = await self.patient_repo.add_diagnosis(patient_id, diagnosis_dict)
        return DiagnosisResponse(**res)

    async def grant_access(self, patient_id: str, hospital_id: str, access_level: str = "read", expires_at: str | None = None) -> dict[str, Any]:
        await self.get_patient(patient_id)
        success = await self.patient_repo.grant_access(patient_id, hospital_id, access_level, expires_at)
        if not success:
            raise HTTPException(status_code=400, detail="Failed to grant access.")
        return {"message": "Access granted successfully.", "success": True}

    async def revoke_access(self, patient_id: str, hospital_id: str) -> dict[str, Any]:
        await self.get_patient(patient_id)
        success = await self.patient_repo.revoke_access(patient_id, hospital_id)
        if not success:
            raise HTTPException(status_code=400, detail="Access revocation failed or relationship did not exist.")
        return {"message": "Access revoked successfully.", "success": True}

    async def get_granted_hospitals(self, patient_id: str) -> list[dict[str, Any]]:
        await self.get_patient(patient_id)
        return await self.patient_repo.get_granted_hospitals(patient_id)
