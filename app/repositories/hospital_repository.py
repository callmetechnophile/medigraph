"""Hospital repository — CRUD and relationships for Hospital operations."""

from __future__ import annotations

from typing import Any

from app.repositories.base_repository import BaseRepository
from app.utils.helpers import generate_id, utc_now, node_to_dict

class HospitalRepository(BaseRepository):
    label = "Hospital"
    search_fields = ["name", "city", "registration_number"]

    async def add_department(self, hospital_id: str, dept_data: dict[str, Any]) -> dict[str, Any]:
        dept_id = dept_data.get("id") or generate_id()
        dept_data["id"] = dept_id
        dept_data.setdefault("created_at", utc_now())
        dept_data.setdefault("updated_at", utc_now())

        props = ", ".join(f"{k}: ${k}" for k in dept_data)
        query = (
            f"MATCH (h:Hospital {{id: $hospital_id}}) "
            f"CREATE (d:Department {{{props}}}) "
            f"CREATE (h)-[:HAS_DEPARTMENT]->(d) "
            f"RETURN d"
        )
        records, _, _ = await self.driver.execute_query(
            query, hospital_id=hospital_id, **dept_data, database_=self.database
        )
        return node_to_dict(records[0]["d"]) if records else dept_data

    async def get_departments(self, hospital_id: str, skip: int = 0, limit: int = 20) -> tuple[list[dict[str, Any]], int]:
        count_query = (
            "MATCH (h:Hospital {id: $hospital_id})-[:HAS_DEPARTMENT]->(d:Department) "
            "RETURN count(d) AS total"
        )
        count_records, _, _ = await self.driver.execute_query(
            count_query, hospital_id=hospital_id, database_=self.database
        )
        total = count_records[0]["total"] if count_records else 0

        data_query = (
            "MATCH (h:Hospital {id: $hospital_id})-[:HAS_DEPARTMENT]->(d:Department) "
            "RETURN d ORDER BY d.name ASC SKIP $skip LIMIT $limit"
        )
        records, _, _ = await self.driver.execute_query(
            data_query, hospital_id=hospital_id, skip=skip, limit=limit, database_=self.database
        )
        items = [node_to_dict(r["d"]) for r in records]
        return items, total

    async def add_doctor(self, hospital_id: str, department_id: str, doctor_data: dict[str, Any]) -> dict[str, Any]:
        doc_id = doctor_data.get("id") or generate_id()
        doctor_data["id"] = doc_id
        doctor_data.setdefault("created_at", utc_now())
        doctor_data.setdefault("updated_at", utc_now())

        props = ", ".join(f"{k}: ${k}" for k in doctor_data)
        query = (
            f"MATCH (h:Hospital {{id: $hospital_id}})-[:HAS_DEPARTMENT]->(d:Department {{id: $department_id}}) "
            f"CREATE (doc:Doctor {{{props}}}) "
            f"CREATE (d)-[:HAS_DOCTOR]->(doc) "
            f"RETURN doc"
        )
        records, _, _ = await self.driver.execute_query(
            query, hospital_id=hospital_id, department_id=department_id, **doctor_data, database_=self.database
        )
        return node_to_dict(records[0]["doc"]) if records else doctor_data

    async def get_doctors(self, hospital_id: str, skip: int = 0, limit: int = 20) -> tuple[list[dict[str, Any]], int]:
        count_query = (
            "MATCH (h:Hospital {id: $hospital_id})-[:HAS_DEPARTMENT]->(d:Department)-[:HAS_DOCTOR]->(doc:Doctor) "
            "RETURN count(doc) AS total"
        )
        count_records, _, _ = await self.driver.execute_query(
            count_query, hospital_id=hospital_id, database_=self.database
        )
        total = count_records[0]["total"] if count_records else 0

        data_query = (
            "MATCH (h:Hospital {id: $hospital_id})-[:HAS_DEPARTMENT]->(d:Department)-[:HAS_DOCTOR]->(doc:Doctor) "
            "RETURN doc, d.name AS department_name ORDER BY doc.name ASC SKIP $skip LIMIT $limit"
        )
        records, _, _ = await self.driver.execute_query(
            data_query, hospital_id=hospital_id, skip=skip, limit=limit, database_=self.database
        )
        items = []
        for r in records:
            d_dict = node_to_dict(r["doc"])
            d_dict["department_name"] = r["department_name"]
            items.append(d_dict)
        return items, total

    async def get_hospitals_by_district(self, district_id: str, skip: int = 0, limit: int = 20) -> tuple[list[dict[str, Any]], int]:
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

    async def get_dashboard_data(self, hospital_id: str) -> dict[str, Any]:
        # Count patients today, staff present, beds available/total, ambulances available/total, low stock items, critical notifications
        query = """
        MATCH (h:Hospital {id: $hospital_id})
        OPTIONAL MATCH (h)-[:HAS_DEPARTMENT]->(d:Department)-[:HAS_DOCTOR]->(doc:Doctor)
        OPTIONAL MATCH (h)-[:HAS_AMBULANCE]->(amb:Ambulance)
        OPTIONAL MATCH (h)-[:HAS_INVENTORY]->(inv:Inventory)
        
        // Count total doctors
        WITH h, count(distinct doc) AS total_doctors, 
             count(distinct amb) AS total_ambulances,
             sum(CASE WHEN amb.status = 'available' THEN 1 ELSE 0 END) AS available_ambulances,
             sum(CASE WHEN inv.current_stock <= inv.reorder_level THEN 1 ELSE 0 END) AS low_stock_items
             
        // Get today's attendance count
        OPTIONAL MATCH (h)-[:HAS_DEPARTMENT]->(d2:Department)
        OPTIONAL MATCH (att:Attendance {hospital_id: $hospital_id}) WHERE att.date = date().epochMillis OR att.date = str(date())
        
        RETURN h.total_beds AS total_beds, 
               h.available_beds AS available_beds,
               total_doctors,
               total_ambulances,
               available_ambulances,
               low_stock_items,
               count(distinct att) AS staff_present
        """
        records, _, _ = await self.driver.execute_query(
            query, hospital_id=hospital_id, database_=self.database
        )
        if records:
            rec = records[0]
            return {
                "total_beds": rec.get("total_beds", 0) or 0,
                "available_beds": rec.get("available_beds", 0) or 0,
                "total_doctors": rec.get("total_doctors", 0) or 0,
                "total_ambulances": rec.get("total_ambulances", 0) or 0,
                "available_ambulances": rec.get("available_ambulances", 0) or 0,
                "low_stock_items": rec.get("low_stock_items", 0) or 0,
                "staff_present": rec.get("staff_present", 0) or 0,
            }
        return {
            "total_beds": 0,
            "available_beds": 0,
            "total_doctors": 0,
            "total_ambulances": 0,
            "available_ambulances": 0,
            "low_stock_items": 0,
            "staff_present": 0,
        }
