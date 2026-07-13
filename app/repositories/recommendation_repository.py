"""Recommendation repository — CRUD and status tracking for AI Recommendations."""

from __future__ import annotations

from typing import Any

from app.repositories.base_repository import BaseRepository
from app.utils.helpers import generate_id, utc_now, node_to_dict

class RecommendationRepository(BaseRepository):
    label = "Recommendation"
    search_fields = ["title", "category"]

    async def create_for_hospital(self, hospital_id: str, recommendation_data: dict[str, Any]) -> dict[str, Any]:
        rec_id = recommendation_data.get("id") or generate_id()
        recommendation_data["id"] = rec_id
        recommendation_data.setdefault("created_at", utc_now())
        recommendation_data.setdefault("updated_at", utc_now())
        recommendation_data.setdefault("status", "pending")

        props = ", ".join(f"{k}: ${k}" for k in recommendation_data)
        query = (
            f"MATCH (h:Hospital {{id: $hospital_id}}) "
            f"CREATE (r:Recommendation {{{props}}}) "
            f"CREATE (h)-[:HAS_RECOMMENDATION]->(r) "
            f"RETURN r"
        )
        records, _, _ = await self.driver.execute_query(
            query, hospital_id=hospital_id, **recommendation_data, database_=self.database
        )
        return node_to_dict(records[0]["r"]) if records else recommendation_data

    async def get_by_hospital(self, hospital_id: str, skip: int = 0, limit: int = 20, status_filter: str = "", priority_filter: str = "") -> tuple[list[dict[str, Any]], int]:
        where_parts = ["h.id = $hospital_id"]
        params: dict[str, Any] = {"hospital_id": hospital_id, "skip": skip, "limit": limit}

        if status_filter:
            where_parts.append("r.status = $status_filter")
            params["status_filter"] = status_filter

        if priority_filter:
            where_parts.append("r.priority = $priority_filter")
            params["priority_filter"] = priority_filter

        where_clause = f"WHERE {' AND '.join(where_parts)}"

        count_query = (
            f"MATCH (h:Hospital)-[:HAS_RECOMMENDATION]->(r:Recommendation) "
            f"{where_clause} RETURN count(r) AS total"
        )
        count_records, _, _ = await self.driver.execute_query(
            count_query, **params, database_=self.database
        )
        total = count_records[0]["total"] if count_records else 0

        data_query = (
            f"MATCH (h:Hospital)-[:HAS_RECOMMENDATION]->(r:Recommendation) "
            f"{where_clause} RETURN r ORDER BY r.created_at DESC SKIP $skip LIMIT $limit"
        )
        records, _, _ = await self.driver.execute_query(
            data_query, **params, database_=self.database
        )
        items = [node_to_dict(r["r"]) for r in records]
        return items, total

    async def get_pending(self, hospital_id: str) -> list[dict[str, Any]]:
        query = (
            "MATCH (h:Hospital {id: $hospital_id})-[:HAS_RECOMMENDATION]->(r:Recommendation {status: 'pending'}) "
            "RETURN r ORDER BY r.created_at DESC"
        )
        records, _, _ = await self.driver.execute_query(
            query, hospital_id=hospital_id, database_=self.database
        )
        return [node_to_dict(r["r"]) for r in records]

    async def accept(self, recommendation_id: str, acted_by: str) -> dict[str, Any] | None:
        query = (
            "MATCH (r:Recommendation {id: $recommendation_id}) "
            "SET r.status = 'accepted', r.acted_on_at = $acted_at, r.acted_on_by = $acted_by, r.updated_at = $acted_at "
            "RETURN r"
        )
        records, _, _ = await self.driver.execute_query(
            query,
            recommendation_id=recommendation_id,
            acted_by=acted_by,
            acted_at=utc_now(),
            database_=self.database,
        )
        return node_to_dict(records[0]["r"]) if records else None

    async def dismiss(self, recommendation_id: str, acted_by: str) -> dict[str, Any] | None:
        query = (
            "MATCH (r:Recommendation {id: $recommendation_id}) "
            "SET r.status = 'dismissed', r.acted_on_at = $acted_at, r.acted_on_by = $acted_by, r.updated_at = $acted_at "
            "RETURN r"
        )
        records, _, _ = await self.driver.execute_query(
            query,
            recommendation_id=recommendation_id,
            acted_by=acted_by,
            acted_at=utc_now(),
            database_=self.database,
        )
        return node_to_dict(records[0]["r"]) if records else None
