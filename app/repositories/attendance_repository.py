"""Attendance repository — CRUD and aggregations for Staff Attendance."""

from __future__ import annotations

from typing import Any

from app.repositories.base_repository import BaseRepository
from app.utils.helpers import generate_id, utc_now, node_to_dict

class AttendanceRepository(BaseRepository):
    label = "Attendance"
    search_fields = ["staff_id"]

    async def check_in(self, hospital_id: str, staff_id: str, department_id: str, date: str, check_in_time: str) -> dict[str, Any]:
        att_id = generate_id()
        attendance_data = {
            "id": att_id,
            "hospital_id": hospital_id,
            "staff_id": staff_id,
            "department_id": department_id,
            "date": date,
            "check_in": check_in_time,
            "check_out": "",
            "status": "present",
            "hours_worked": 0.0,
            "created_at": utc_now(),
            "updated_at": utc_now(),
        }
        props = ", ".join(f"{k}: ${k}" for k in attendance_data)
        query = (
            f"MATCH (h:Hospital {{id: $hospital_id}}), (d:Department {{id: $department_id}}) "
            f"CREATE (a:Attendance {{{props}}}) "
            f"CREATE (h)-[:HAS_ATTENDANCE_RECORD]->(a) "
            f"CREATE (d)-[:HAS_STAFF_ATTENDANCE]->(a) "
            f"RETURN a"
        )
        records, _, _ = await self.driver.execute_query(
            query, **attendance_data, database_=self.database
        )
        return node_to_dict(records[0]["a"]) if records else attendance_data

    async def check_out(self, attendance_id: str, check_out_time: str, hours_worked: float) -> dict[str, Any] | None:
        query = (
            "MATCH (a:Attendance {id: $attendance_id}) "
            "SET a.check_out = $check_out_time, a.hours_worked = $hours_worked, a.updated_at = $updated_at "
            "RETURN a"
        )
        records, _, _ = await self.driver.execute_query(
            query,
            attendance_id=attendance_id,
            check_out_time=check_out_time,
            hours_worked=hours_worked,
            updated_at=utc_now(),
            database_=self.database,
        )
        return node_to_dict(records[0]["a"]) if records else None

    async def get_by_hospital(self, hospital_id: str, date: str, skip: int = 0, limit: int = 20) -> tuple[list[dict[str, Any]], int]:
        count_query = (
            "MATCH (a:Attendance {hospital_id: $hospital_id, date: $date}) "
            "RETURN count(a) AS total"
        )
        count_records, _, _ = await self.driver.execute_query(
            count_query, hospital_id=hospital_id, date=date, database_=self.database
        )
        total = count_records[0]["total"] if count_records else 0

        data_query = (
            "MATCH (a:Attendance {hospital_id: $hospital_id, date: $date}) "
            "RETURN a ORDER BY a.check_in DESC SKIP $skip LIMIT $limit"
        )
        records, _, _ = await self.driver.execute_query(
            data_query, hospital_id=hospital_id, date=date, skip=skip, limit=limit, database_=self.database
        )
        items = [node_to_dict(r["a"]) for r in records]
        return items, total

    async def get_by_department(self, hospital_id: str, department_id: str, date: str, skip: int = 0, limit: int = 20) -> tuple[list[dict[str, Any]], int]:
        count_query = (
            "MATCH (a:Attendance {hospital_id: $hospital_id, department_id: $department_id, date: $date}) "
            "RETURN count(a) AS total"
        )
        count_records, _, _ = await self.driver.execute_query(
            count_query, hospital_id=hospital_id, department_id=department_id, date=date, database_=self.database
        )
        total = count_records[0]["total"] if count_records else 0

        data_query = (
            "MATCH (a:Attendance {hospital_id: $hospital_id, department_id: $department_id, date: $date}) "
            "RETURN a ORDER BY a.check_in DESC SKIP $skip LIMIT $limit"
        )
        records, _, _ = await self.driver.execute_query(
            data_query, hospital_id=hospital_id, department_id=department_id, date=date, skip=skip, limit=limit, database_=self.database
        )
        items = [node_to_dict(r["a"]) for r in records]
        return items, total

    async def get_daily_summary(self, hospital_id: str, date: str) -> dict[str, Any]:
        query = """
        MATCH (a:Attendance {hospital_id: $hospital_id, date: $date})
        RETURN count(a) AS total_present,
               sum(CASE WHEN a.status = 'late' THEN 1 ELSE 0 END) AS total_late,
               sum(CASE WHEN a.status = 'absent' THEN 1 ELSE 0 END) AS total_absent,
               sum(CASE WHEN a.status = 'half_day' THEN 1 ELSE 0 END) AS total_half_day,
               sum(CASE WHEN a.status = 'on_leave' THEN 1 ELSE 0 END) AS total_on_leave
        """
        records, _, _ = await self.driver.execute_query(
            query, hospital_id=hospital_id, date=date, database_=self.database
        )
        if records:
            r = records[0]
            present = r["total_present"] or 0
            late = r["total_late"] or 0
            absent = r["total_absent"] or 0
            half_day = r["total_half_day"] or 0
            on_leave = r["total_on_leave"] or 0
            total_staff = present + absent + on_leave
            attendance_rate = (present / total_staff * 100) if total_staff > 0 else 0.0
            return {
                "total_staff": total_staff,
                "present": present,
                "absent": absent,
                "late": late,
                "half_day": half_day,
                "on_leave": on_leave,
                "attendance_rate": round(attendance_rate, 2),
                "date": date,
            }
        return {
            "total_staff": 0,
            "present": 0,
            "absent": 0,
            "late": 0,
            "half_day": 0,
            "on_leave": 0,
            "attendance_rate": 0.0,
            "date": date,
        }

    async def get_staff_attendance_history(self, staff_id: str, start_date: str, end_date: str) -> list[dict[str, Any]]:
        query = (
            "MATCH (a:Attendance {staff_id: $staff_id}) "
            "WHERE a.date >= $start_date AND a.date <= $end_date "
            "RETURN a ORDER BY a.date DESC"
        )
        records, _, _ = await self.driver.execute_query(
            query, staff_id=staff_id, start_date=start_date, end_date=end_date, database_=self.database
        )
        return [node_to_dict(r["a"]) for r in records]

    async def get_absent_staff(self, hospital_id: str, date: str) -> list[dict[str, Any]]:
        # Find doctors and staff who DO NOT have attendance on date
        # For simplicity, we match all Doctors in the Hospital departments who have no attendance
        query = """
        MATCH (h:Hospital {id: $hospital_id})-[:HAS_DEPARTMENT]->(d:Department)-[:HAS_DOCTOR]->(doc:Doctor)
        WHERE NOT EXISTS {
            MATCH (doc)<-[:HAS_STAFF_ATTENDANCE]-(a:Attendance {date: $date, hospital_id: $hospital_id})
        }
        RETURN doc, d.name AS department_name
        """
        records, _, _ = await self.driver.execute_query(
            query, hospital_id=hospital_id, date=date, database_=self.database
        )
        items = []
        for r in records:
            doc_dict = node_to_dict(r["doc"])
            doc_dict["department_name"] = r["department_name"]
            items.append(doc_dict)
        return items
