"""Patient repository — CRUD and relationships for Patient nodes."""

from __future__ import annotations

from typing import Any

from app.models import Patient
from app.repositories.base_repository import BaseRepository
from app.utils.helpers import generate_id, utc_now, node_to_dict

class PatientRepository(BaseRepository):
    label = "Patient"
    search_fields = ["name", "phone", "email"]

    async def find_by_clerk_id(self, clerk_user_id: str) -> dict[str, Any] | None:
        query = f"MATCH (n:{self.label} {{clerk_user_id: $clerk_user_id}}) RETURN n"
        records, _, _ = await self.driver.execute_query(
            query, clerk_user_id=clerk_user_id, database_=self.database
        )
        return node_to_dict(records[0]["n"]) if records else None

    async def get_medical_records(self, patient_id: str, skip: int = 0, limit: int = 20) -> tuple[list[dict[str, Any]], int]:
        count_query = (
            "MATCH (p:Patient {id: $patient_id})-[:HAS_MEDICAL_RECORD]->(m:MedicalRecord) "
            "RETURN count(m) AS total"
        )
        count_records, _, _ = await self.driver.execute_query(
            count_query, patient_id=patient_id, database_=self.database
        )
        total = count_records[0]["total"] if count_records else 0

        data_query = (
            "MATCH (p:Patient {id: $patient_id})-[:HAS_MEDICAL_RECORD]->(m:MedicalRecord) "
            "RETURN m ORDER BY m.visit_date DESC SKIP $skip LIMIT $limit"
        )
        records, _, _ = await self.driver.execute_query(
            data_query, patient_id=patient_id, skip=skip, limit=limit, database_=self.database
        )
        items = [node_to_dict(r["m"]) for r in records]
        return items, total

    async def add_medical_record(self, patient_id: str, record_data: dict[str, Any]) -> dict[str, Any]:
        record_id = record_data.get("id") or generate_id()
        record_data["id"] = record_id
        record_data.setdefault("created_at", utc_now())
        record_data.setdefault("updated_at", utc_now())

        props = ", ".join(f"{k}: ${k}" for k in record_data)
        query = (
            f"MATCH (p:Patient {{id: $patient_id}}) "
            f"CREATE (m:MedicalRecord {{{props}}}) "
            f"CREATE (p)-[:HAS_MEDICAL_RECORD]->(m) "
            f"RETURN m"
        )
        records, _, _ = await self.driver.execute_query(
            query, patient_id=patient_id, **record_data, database_=self.database
        )
        return node_to_dict(records[0]["m"]) if records else record_data

    async def get_prescriptions(self, patient_id: str, skip: int = 0, limit: int = 20) -> tuple[list[dict[str, Any]], int]:
        count_query = (
            "MATCH (p:Patient {id: $patient_id})-[:HAS_PRESCRIPTION]->(pr:Prescription) "
            "RETURN count(pr) AS total"
        )
        count_records, _, _ = await self.driver.execute_query(
            count_query, patient_id=patient_id, database_=self.database
        )
        total = count_records[0]["total"] if count_records else 0

        data_query = (
            "MATCH (p:Patient {id: $patient_id})-[:HAS_PRESCRIPTION]->(pr:Prescription) "
            "RETURN pr ORDER BY pr.created_at DESC SKIP $skip LIMIT $limit"
        )
        records, _, _ = await self.driver.execute_query(
            data_query, patient_id=patient_id, skip=skip, limit=limit, database_=self.database
        )
        items = [node_to_dict(r["pr"]) for r in records]
        return items, total

    async def add_prescription(self, patient_id: str, prescription_data: dict[str, Any]) -> dict[str, Any]:
        pres_id = prescription_data.get("id") or generate_id()
        prescription_data["id"] = pres_id
        prescription_data.setdefault("created_at", utc_now())
        prescription_data.setdefault("updated_at", utc_now())
        doctor_id = prescription_data.get("doctor_id")

        props = ", ".join(f"{k}: ${k}" for k in prescription_data)
        query = (
            f"MATCH (p:Patient {{id: $patient_id}}), (d:Doctor {{id: $doctor_id}}) "
            f"CREATE (pr:Prescription {{{props}}}) "
            f"CREATE (p)-[:HAS_PRESCRIPTION]->(pr) "
            f"CREATE (d)-[:CREATED]->(pr) "
            f"RETURN pr"
        )
        records, _, _ = await self.driver.execute_query(
            query, patient_id=patient_id, doctor_id=doctor_id, **prescription_data, database_=self.database
        )
        return node_to_dict(records[0]["pr"]) if records else prescription_data

    async def get_diagnoses(self, patient_id: str, skip: int = 0, limit: int = 20) -> tuple[list[dict[str, Any]], int]:
        count_query = (
            "MATCH (p:Patient {id: $patient_id})-[:HAS_DIAGNOSIS]->(d:Diagnosis) "
            "RETURN count(d) AS total"
        )
        count_records, _, _ = await self.driver.execute_query(
            count_query, patient_id=patient_id, database_=self.database
        )
        total = count_records[0]["total"] if count_records else 0

        data_query = (
            "MATCH (p:Patient {id: $patient_id})-[:HAS_DIAGNOSIS]->(d:Diagnosis) "
            "RETURN d ORDER BY d.diagnosed_at DESC SKIP $skip LIMIT $limit"
        )
        records, _, _ = await self.driver.execute_query(
            data_query, patient_id=patient_id, skip=skip, limit=limit, database_=self.database
        )
        items = [node_to_dict(r["d"]) for r in records]
        return items, total

    async def add_diagnosis(self, patient_id: str, diagnosis_data: dict[str, Any]) -> dict[str, Any]:
        diag_id = diagnosis_data.get("id") or generate_id()
        diagnosis_data["id"] = diag_id
        diagnosis_data.setdefault("created_at", utc_now())
        diagnosis_data.setdefault("updated_at", utc_now())
        diagnosis_data.setdefault("diagnosed_at", utc_now())

        props = ", ".join(f"{k}: ${k}" for k in diagnosis_data)
        query = (
            f"MATCH (p:Patient {{id: $patient_id}}) "
            f"CREATE (d:Diagnosis {{{props}}}) "
            f"CREATE (p)-[:HAS_DIAGNOSIS]->(d) "
            f"RETURN d"
        )
        records, _, _ = await self.driver.execute_query(
            query, patient_id=patient_id, **diagnosis_data, database_=self.database
        )
        return node_to_dict(records[0]["d"]) if records else diagnosis_data

    async def grant_access(self, patient_id: str, hospital_id: str, access_level: str = "read", expires_at: str | None = None) -> bool:
        props_parts = [f"access_level: $access_level", f"granted_at: $granted_at"]
        params = {
            "patient_id": patient_id,
            "hospital_id": hospital_id,
            "access_level": access_level,
            "granted_at": utc_now(),
        }
        if expires_at:
            props_parts.append("expires_at: $expires_at")
            params["expires_at"] = expires_at

        query = (
            f"MATCH (p:Patient {{id: $patient_id}}), (h:Hospital {{id: $hospital_id}}) "
            f"MERGE (p)-[r:GRANTED_ACCESS_TO {{{', '.join(props_parts)}}}]->(h) "
            f"RETURN r"
        )
        records, _, _ = await self.driver.execute_query(
            query, **params, database_=self.database
        )
        return bool(records)

    async def revoke_access(self, patient_id: str, hospital_id: str) -> bool:
        query = (
            "MATCH (p:Patient {id: $patient_id})-[r:GRANTED_ACCESS_TO]->(h:Hospital {id: $hospital_id}) "
            "DELETE r RETURN count(*) AS cnt"
        )
        records, _, _ = await self.driver.execute_query(
            query, patient_id=patient_id, hospital_id=hospital_id, database_=self.database
        )
        return records[0]["cnt"] > 0 if records else False

    async def get_granted_hospitals(self, patient_id: str) -> list[dict[str, Any]]:
        query = (
            "MATCH (p:Patient {id: $patient_id})-[r:GRANTED_ACCESS_TO]->(h:Hospital) "
            "RETURN h, r.access_level AS access_level, r.expires_at AS expires_at"
        )
        records, _, _ = await self.driver.execute_query(
            query, patient_id=patient_id, database_=self.database
        )
        hospitals = []
        for rec in records:
            h_dict = node_to_dict(rec["h"])
            h_dict["access_level"] = rec["access_level"]
            h_dict["expires_at"] = rec["expires_at"]
            hospitals.append(h_dict)
        return hospitals
