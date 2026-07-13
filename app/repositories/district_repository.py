"""District repository — CRUD and district-wide hierarchy management."""

from __future__ import annotations

from typing import Any

from app.repositories.base_repository import BaseRepository
from app.utils.helpers import generate_id, utc_now, node_to_dict

class DistrictRepository(BaseRepository):
    label = "District"
    search_fields = ["name", "code"]

    async def get_managed_hospitals(self, district_id: str, skip: int = 0, limit: int = 20) -> tuple[list[dict[str, Any]], int]:
        count_query = (
            "MATCH (d:District {id: $district_id})-[:MANAGES]->(h:Hospital) "
            "RETURN count(h) AS total"
        )
        count_records, _, _ = await self.driver.execute_query(
            count_query, district_id=district_id, database_=self.database
        )
        total = count_records[0]["total"] if count_records else 0

        data_query = (
            "MATCH (d:District {id: $district_id})-[:MANAGES]->(h:Hospital) "
            "RETURN h ORDER BY h.name ASC SKIP $skip LIMIT $limit"
        )
        records, _, _ = await self.driver.execute_query(
            data_query, district_id=district_id, skip=skip, limit=limit, database_=self.database
        )
        items = [node_to_dict(r["h"]) for r in records]
        return items, total

    async def assign_hospital(self, district_id: str, hospital_id: str) -> bool:
        query = (
            "MATCH (d:District {id: $district_id}), (h:Hospital {id: $hospital_id}) "
            "MERGE (d)-[r:MANAGES]->(h) "
            "SET r.assigned_at = $assigned_at "
            "RETURN r"
        )
        records, _, _ = await self.driver.execute_query(
            query, district_id=district_id, hospital_id=hospital_id, assigned_at=utc_now(), database_=self.database
        )
        return bool(records)

    async def unassign_hospital(self, district_id: str, hospital_id: str) -> bool:
        query = (
            "MATCH (d:District {id: $district_id})-[r:MANAGES]->(h:Hospital {id: $hospital_id}) "
            "DELETE r RETURN count(*) AS cnt"
        )
        records, _, _ = await self.driver.execute_query(
            query, district_id=district_id, hospital_id=hospital_id, database_=self.database
        )
        return records[0]["cnt"] > 0 if records else False

    async def get_aggregated_stats(self, district_id: str) -> dict[str, Any]:
        # Query total beds, available beds, total doctors, total staff present, average HMI score across managed hospitals
        query = """
        MATCH (d:District {id: $district_id})-[:MANAGES]->(h:Hospital)
        OPTIONAL MATCH (h)-[:HAS_DEPARTMENT]->(dept:Department)-[:HAS_DOCTOR]->(doc:Doctor)
        OPTIONAL MATCH (h)-[:HAS_HMI]->(s:HMIScore)
        WITH h, count(distinct doc) AS doctors, max(s.overall_score) AS latest_hmi
        
        RETURN count(distinct h) AS total_hospitals,
               sum(h.total_beds) AS total_beds,
               sum(h.available_beds) AS available_beds,
               sum(doctors) AS total_doctors,
               avg(latest_hmi) AS average_hmi_score
        """
        records, _, _ = await self.driver.execute_query(
            query, district_id=district_id, database_=self.database
        )
        if records:
            r = records[0]
            return {
                "total_hospitals": r["total_hospitals"] or 0,
                "total_beds": r["total_beds"] or 0,
                "available_beds": r["available_beds"] or 0,
                "total_doctors": r["total_doctors"] or 0,
                "average_hmi_score": round(r["average_hmi_score"] or 0.0, 2),
            }
        return {
            "total_hospitals": 0,
            "total_beds": 0,
            "available_beds": 0,
            "total_doctors": 0,
            "average_hmi_score": 0.0,
        }


class StateRepository(BaseRepository):
    label = "State"
    search_fields = ["name", "code"]


class CountryRepository(BaseRepository):
    label = "Country"
    search_fields = ["name", "code"]
