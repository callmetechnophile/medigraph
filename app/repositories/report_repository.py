"""Report repository — CRUD and linking for generated reports."""

from __future__ import annotations

from typing import Any

from app.repositories.base_repository import BaseRepository
from app.utils.helpers import generate_id, utc_now, node_to_dict

class ReportRepository(BaseRepository):
    label = "Report"
    search_fields = ["title", "description"]

    async def create_for_hospital(self, hospital_id: str, report_data: dict[str, Any]) -> dict[str, Any]:
        rep_id = report_data.get("id") or generate_id()
        report_data["id"] = rep_id
        report_data.setdefault("created_at", utc_now())
        report_data.setdefault("updated_at", utc_now())

        props = ", ".join(f"{k}: ${k}" for k in report_data)
        query = (
            f"MATCH (h:Hospital {{id: $hospital_id}}) "
            f"CREATE (r:Report {{{props}}}) "
            f"CREATE (h)-[:GENERATED]->(r) "
            f"RETURN r"
        )
        records, _, _ = await self.driver.execute_query(
            query, hospital_id=hospital_id, **report_data, database_=self.database
        )
        return node_to_dict(records[0]["r"]) if records else report_data

    async def get_by_hospital(self, hospital_id: str, skip: int = 0, limit: int = 20, report_type_filter: str = "") -> tuple[list[dict[str, Any]], int]:
        where_parts = ["h.id = $hospital_id"]
        params: dict[str, Any] = {"hospital_id": hospital_id, "skip": skip, "limit": limit}

        if report_type_filter:
            where_parts.append("r.report_type = $report_type_filter")
            params["report_type_filter"] = report_type_filter

        where_clause = f"WHERE {' AND '.join(where_parts)}"

        count_query = (
            f"MATCH (h:Hospital)-[:GENERATED]->(r:Report) "
            f"{where_clause} RETURN count(r) AS total"
        )
        count_records, _, _ = await self.driver.execute_query(
            count_query, **params, database_=self.database
        )
        total = count_records[0]["total"] if count_records else 0

        data_query = (
            f"MATCH (h:Hospital)-[:GENERATED]->(r:Report) "
            f"{where_clause} RETURN r ORDER BY r.created_at DESC SKIP $skip LIMIT $limit"
        )
        records, _, _ = await self.driver.execute_query(
            data_query, **params, database_=self.database
        )
        items = [node_to_dict(r["r"]) for r in records]
        return items, total

    async def get_by_district(self, district_id: str, skip: int = 0, limit: int = 20) -> tuple[list[dict[str, Any]], int]:
        count_query = (
            "MATCH (d:District {id: $district_id})-[:MANAGES]->(h:Hospital)-[:GENERATED]->(r:Report) "
            "RETURN count(r) AS total"
        )
        count_records, _, _ = await self.driver.execute_query(
            count_query, district_id=district_id, database_=self.database
        )
        total = count_records[0]["total"] if count_records else 0

        data_query = (
            "MATCH (d:District {id: $district_id})-[:MANAGES]->(h:Hospital)-[:GENERATED]->(r:Report) "
            "RETURN r, h.name AS hospital_name ORDER BY r.created_at DESC SKIP $skip LIMIT $limit"
        )
        records, _, _ = await self.driver.execute_query(
            data_query, district_id=district_id, skip=skip, limit=limit, database_=self.database
        )
        items = []
        for r in records:
            rep_dict = node_to_dict(r["r"])
            rep_dict["hospital_name"] = r["hospital_name"]
            items.append(rep_dict)
        return items, total
