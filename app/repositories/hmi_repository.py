"""HMI Score repository — CRUD and trend tracking for Hospital Management Index."""

from __future__ import annotations

from typing import Any

from app.repositories.base_repository import BaseRepository
from app.utils.helpers import generate_id, utc_now, node_to_dict

class HMIRepository(BaseRepository):
    label = "HMIScore"
    search_fields = []

    async def create_for_hospital(self, hospital_id: str, score_data: dict[str, Any]) -> dict[str, Any]:
        score_id = score_data.get("id") or generate_id()
        score_data["id"] = score_id
        score_data.setdefault("created_at", utc_now())
        score_data.setdefault("updated_at", utc_now())

        props = ", ".join(f"{k}: ${k}" for k in score_data)
        query = (
            f"MATCH (h:Hospital {{id: $hospital_id}}) "
            f"CREATE (s:HMIScore {{{props}}}) "
            f"CREATE (h)-[:HAS_HMI]->(s) "
            f"RETURN s"
        )
        records, _, _ = await self.driver.execute_query(
            query, hospital_id=hospital_id, **score_data, database_=self.database
        )
        return node_to_dict(records[0]["s"]) if records else score_data

    async def get_latest(self, hospital_id: str) -> dict[str, Any] | None:
        query = (
            "MATCH (h:Hospital {id: $hospital_id})-[:HAS_HMI]->(s:HMIScore) "
            "RETURN s ORDER BY s.calculated_at DESC LIMIT 1"
        )
        records, _, _ = await self.driver.execute_query(
            query, hospital_id=hospital_id, database_=self.database
        )
        return node_to_dict(records[0]["s"]) if records else None

    async def get_history(self, hospital_id: str, limit: int = 30) -> list[dict[str, Any]]:
        query = (
            "MATCH (h:Hospital {id: $hospital_id})-[:HAS_HMI]->(s:HMIScore) "
            "RETURN s ORDER BY s.calculated_at DESC LIMIT $limit"
        )
        records, _, _ = await self.driver.execute_query(
            query, hospital_id=hospital_id, limit=limit, database_=self.database
        )
        return [node_to_dict(r["s"]) for r in records]

    async def get_department_contributions(self, hospital_id: str) -> dict[str, Any]:
        # Return department contributions from the latest score
        latest = await self.get_latest(hospital_id)
        if latest and "department_contributions" in latest:
            return latest["department_contributions"]
        return {}
