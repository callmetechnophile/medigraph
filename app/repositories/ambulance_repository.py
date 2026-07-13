"""Ambulance repository — CRUD and status tracking for Ambulance fleet."""

from __future__ import annotations

from typing import Any

from app.repositories.base_repository import BaseRepository
from app.utils.helpers import generate_id, utc_now, node_to_dict

class AmbulanceRepository(BaseRepository):
    label = "Ambulance"
    search_fields = ["vehicle_number", "driver_name"]

    async def create_for_hospital(self, hospital_id: str, ambulance_data: dict[str, Any]) -> dict[str, Any]:
        amb_id = ambulance_data.get("id") or generate_id()
        ambulance_data["id"] = amb_id
        ambulance_data.setdefault("created_at", utc_now())
        ambulance_data.setdefault("updated_at", utc_now())
        ambulance_data.setdefault("status", "available")

        props = ", ".join(f"{k}: ${k}" for k in ambulance_data)
        query = (
            f"MATCH (h:Hospital {{id: $hospital_id}}) "
            f"CREATE (a:Ambulance {{{props}}}) "
            f"CREATE (h)-[:HAS_AMBULANCE]->(a) "
            f"RETURN a"
        )
        records, _, _ = await self.driver.execute_query(
            query, hospital_id=hospital_id, **ambulance_data, database_=self.database
        )
        return node_to_dict(records[0]["a"]) if records else ambulance_data

    async def get_by_hospital(self, hospital_id: str, skip: int = 0, limit: int = 20, status_filter: str = "") -> tuple[list[dict[str, Any]], int]:
        where_parts = ["h.id = $hospital_id"]
        params: dict[str, Any] = {"hospital_id": hospital_id, "skip": skip, "limit": limit}

        if status_filter:
            where_parts.append("a.status = $status_filter")
            params["status_filter"] = status_filter

        where_clause = f"WHERE {' AND '.join(where_parts)}"

        count_query = (
            f"MATCH (h:Hospital)-[:HAS_AMBULANCE]->(a:Ambulance) "
            f"{where_clause} RETURN count(a) AS total"
        )
        count_records, _, _ = await self.driver.execute_query(
            count_query, **params, database_=self.database
        )
        total = count_records[0]["total"] if count_records else 0

        data_query = (
            f"MATCH (h:Hospital)-[:HAS_AMBULANCE]->(a:Ambulance) "
            f"{where_clause} RETURN a ORDER BY a.vehicle_number ASC SKIP $skip LIMIT $limit"
        )
        records, _, _ = await self.driver.execute_query(
            data_query, **params, database_=self.database
        )
        items = [node_to_dict(r["a"]) for r in records]
        return items, total

    async def get_available(self, hospital_id: str) -> list[dict[str, Any]]:
        query = (
            "MATCH (h:Hospital {id: $hospital_id})-[:HAS_AMBULANCE]->(a:Ambulance {status: 'available'}) "
            "RETURN a ORDER BY a.vehicle_number ASC"
        )
        records, _, _ = await self.driver.execute_query(
            query, hospital_id=hospital_id, database_=self.database
        )
        return [node_to_dict(r["a"]) for r in records]

    async def dispatch(self, ambulance_id: str, destination: str, patient_id: str | None = None, latitude: float | None = None, longitude: float | None = None) -> dict[str, Any] | None:
        # Set status to dispatched, update current_location
        query = (
            "MATCH (a:Ambulance {id: $ambulance_id}) "
            "SET a.status = 'dispatched', a.current_location = $destination, "
            "a.latitude = $latitude, a.longitude = $longitude, a.updated_at = $updated_at "
            "RETURN a"
        )
        records, _, _ = await self.driver.execute_query(
            query,
            ambulance_id=ambulance_id,
            destination=destination,
            latitude=latitude,
            longitude=longitude,
            updated_at=utc_now(),
            database_=self.database,
        )
        if records and patient_id:
            # If patient is provided, link the ambulance to patient for this trip
            await self.driver.execute_query(
                "MATCH (a:Ambulance {id: $ambulance_id}), (p:Patient {id: $patient_id}) "
                "MERGE (a)-[r:DISPATCHED_FOR]->(p) "
                "SET r.dispatched_at = $dispatched_at",
                ambulance_id=ambulance_id,
                patient_id=patient_id,
                dispatched_at=utc_now(),
                database_=self.database,
            )
        return node_to_dict(records[0]["a"]) if records else None

    async def mark_returned(self, ambulance_id: str) -> dict[str, Any] | None:
        query = (
            "MATCH (a:Ambulance {id: $ambulance_id}) "
            "SET a.status = 'available', a.current_location = 'base', "
            "a.latitude = null, a.longitude = null, a.updated_at = $updated_at "
            "RETURN a"
        )
        records, _, _ = await self.driver.execute_query(
            query,
            ambulance_id=ambulance_id,
            updated_at=utc_now(),
            database_=self.database,
        )
        # Delete any DISPATCHED_FOR relationships
        await self.driver.execute_query(
            "MATCH (a:Ambulance {id: $ambulance_id})-[r:DISPATCHED_FOR]->(p:Patient) DELETE r",
            ambulance_id=ambulance_id,
            database_=self.database,
        )
        return node_to_dict(records[0]["a"]) if records else None

    async def get_fleet_summary(self, hospital_id: str) -> dict[str, int]:
        query = (
            "MATCH (h:Hospital {id: $hospital_id})-[:HAS_AMBULANCE]->(a:Ambulance) "
            "RETURN a.status AS status, count(a) AS count"
        )
        records, _, _ = await self.driver.execute_query(
            query, hospital_id=hospital_id, database_=self.database
        )
        summary = {"available": 0, "dispatched": 0, "maintenance": 0, "out_of_service": 0}
        for rec in records:
            status = rec["status"]
            count = rec["count"]
            if status in summary:
                summary[status] = count
            else:
                summary[status] = count
        return summary
