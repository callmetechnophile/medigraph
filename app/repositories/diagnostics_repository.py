"""Diagnostics repository — CRUD and relationships for equipment and reports."""

from __future__ import annotations

from typing import Any

from app.repositories.base_repository import BaseRepository
from app.utils.helpers import generate_id, utc_now, node_to_dict

class EquipmentRepository(BaseRepository):
    label = "DiagnosticEquipment"
    search_fields = ["name", "serial_number", "model_number"]

    async def get_by_hospital(self, hospital_id: str, skip: int = 0, limit: int = 20, status_filter: str = "") -> tuple[list[dict[str, Any]], int]:
        where_parts = ["n.hospital_id = $hospital_id"]
        params: dict[str, Any] = {"hospital_id": hospital_id, "skip": skip, "limit": limit}

        if status_filter:
            where_parts.append("n.status = $status_filter")
            params["status_filter"] = status_filter

        where_clause = f"WHERE {' AND '.join(where_parts)}"

        count_query = f"MATCH (n:{self.label}) {where_clause} RETURN count(n) AS total"
        count_records, _, _ = await self.driver.execute_query(
            count_query, **params, database_=self.database
        )
        total = count_records[0]["total"] if count_records else 0

        data_query = f"MATCH (n:{self.label}) {where_clause} RETURN n ORDER BY n.name ASC SKIP $skip LIMIT $limit"
        records, _, _ = await self.driver.execute_query(
            data_query, **params, database_=self.database
        )
        items = [node_to_dict(r["n"]) for r in records]
        return items, total

    async def get_maintenance_due(self, hospital_id: str) -> list[dict[str, Any]]:
        query = (
            f"MATCH (n:{self.label} {{hospital_id: $hospital_id}}) "
            f"WHERE n.next_maintenance_date IS NOT NULL AND date(n.next_maintenance_date) <= date() "
            f"RETURN n"
        )
        records, _, _ = await self.driver.execute_query(
            query, hospital_id=hospital_id, database_=self.database
        )
        return [node_to_dict(r["n"]) for r in records]

    async def update_status(self, equipment_id: str, status: str) -> dict[str, Any] | None:
        query = (
            f"MATCH (n:{self.label} {{id: $equipment_id}}) "
            f"SET n.status = $status, n.updated_at = $updated_at "
            f"RETURN n"
        )
        records, _, _ = await self.driver.execute_query(
            query, equipment_id=equipment_id, status=status, updated_at=utc_now(), database_=self.database
        )
        return node_to_dict(records[0]["n"]) if records else None

    async def log_usage(self, equipment_id: str, hours: float) -> dict[str, Any] | None:
        query = (
            f"MATCH (n:{self.label} {{id: $equipment_id}}) "
            f"SET n.usage_hours = coalesce(n.usage_hours, 0) + $hours, n.updated_at = $updated_at "
            f"RETURN n"
        )
        records, _, _ = await self.driver.execute_query(
            query, equipment_id=equipment_id, hours=hours, updated_at=utc_now(), database_=self.database
        )
        return node_to_dict(records[0]["n"]) if records else None


class LabReportRepository(BaseRepository):
    label = "LaboratoryReport"
    search_fields = ["test_name", "test_category"]

    async def create_for_patient(self, hospital_id: str, report_data: dict[str, Any]) -> dict[str, Any]:
        report_id = report_data.get("id") or generate_id()
        report_data["id"] = report_id
        report_data.setdefault("created_at", utc_now())
        report_data.setdefault("updated_at", utc_now())
        report_data.setdefault("reported_at", utc_now())
        patient_id = report_data.get("patient_id")

        props = ", ".join(f"{k}: ${k}" for k in report_data)
        query = (
            f"MATCH (p:Patient {{id: $patient_id}}), (h:Hospital {{id: $hospital_id}}) "
            f"CREATE (lr:LaboratoryReport {{{props}}}) "
            f"CREATE (p)-[:HAS_LAB_REPORT]->(lr) "
            f"CREATE (h)-[:GENERATED_LAB_REPORT]->(lr) "
            f"RETURN lr"
        )
        records, _, _ = await self.driver.execute_query(
            query, hospital_id=hospital_id, patient_id=patient_id, **report_data, database_=self.database
        )
        return node_to_dict(records[0]["lr"]) if records else report_data

    async def get_by_patient(self, patient_id: str, skip: int = 0, limit: int = 20) -> tuple[list[dict[str, Any]], int]:
        count_query = (
            "MATCH (p:Patient {id: $patient_id})-[:HAS_LAB_REPORT]->(lr:LaboratoryReport) "
            "RETURN count(lr) AS total"
        )
        count_records, _, _ = await self.driver.execute_query(
            count_query, patient_id=patient_id, database_=self.database
        )
        total = count_records[0]["total"] if count_records else 0

        data_query = (
            "MATCH (p:Patient {id: $patient_id})-[:HAS_LAB_REPORT]->(lr:LaboratoryReport) "
            "RETURN lr ORDER BY lr.reported_at DESC SKIP $skip LIMIT $limit"
        )
        records, _, _ = await self.driver.execute_query(
            data_query, patient_id=patient_id, skip=skip, limit=limit, database_=self.database
        )
        items = [node_to_dict(r["lr"]) for r in records]
        return items, total


class ImagingReportRepository(BaseRepository):
    label = "ImagingReport"
    search_fields = ["imaging_type", "body_part"]

    async def create_for_patient(self, hospital_id: str, report_data: dict[str, Any]) -> dict[str, Any]:
        report_id = report_data.get("id") or generate_id()
        report_data["id"] = report_id
        report_data.setdefault("created_at", utc_now())
        report_data.setdefault("updated_at", utc_now())
        report_data.setdefault("reported_at", utc_now())
        patient_id = report_data.get("patient_id")

        props = ", ".join(f"{k}: ${k}" for k in report_data)
        query = (
            f"MATCH (p:Patient {{id: $patient_id}}), (h:Hospital {{id: $hospital_id}}) "
            f"CREATE (ir:ImagingReport {{{props}}}) "
            f"CREATE (p)-[:HAS_IMAGING_REPORT]->(ir) "
            f"CREATE (h)-[:GENERATED_IMAGING_REPORT]->(ir) "
            f"RETURN ir"
        )
        records, _, _ = await self.driver.execute_query(
            query, hospital_id=hospital_id, patient_id=patient_id, **report_data, database_=self.database
        )
        return node_to_dict(records[0]["ir"]) if records else report_data

    async def get_by_patient(self, patient_id: str, skip: int = 0, limit: int = 20) -> tuple[list[dict[str, Any]], int]:
        count_query = (
            "MATCH (p:Patient {id: $patient_id})-[:HAS_IMAGING_REPORT]->(ir:ImagingReport) "
            "RETURN count(ir) AS total"
        )
        count_records, _, _ = await self.driver.execute_query(
            count_query, patient_id=patient_id, database_=self.database
        )
        total = count_records[0]["total"] if count_records else 0

        data_query = (
            "MATCH (p:Patient {id: $patient_id})-[:HAS_IMAGING_REPORT]->(ir:ImagingReport) "
            "RETURN ir ORDER BY ir.reported_at DESC SKIP $skip LIMIT $limit"
        )
        records, _, _ = await self.driver.execute_query(
            data_query, patient_id=patient_id, skip=skip, limit=limit, database_=self.database
        )
        items = [node_to_dict(r["ir"]) for r in records]
        return items, total
