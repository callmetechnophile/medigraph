"""HMI service — Calculates the Hospital Management Index score."""

from __future__ import annotations

from typing import Any
import structlog
from fastapi import HTTPException

from app.repositories import (
    HMIRepository,
    InventoryRepository,
    AttendanceRepository,
    AmbulanceRepository,
    EquipmentRepository,
)
from app.schemas import HMIScoreResponse, HMITrendResponse
from app.utils.helpers import utc_now, generate_id

logger = structlog.get_logger(__name__)

class HMIService:
    def __init__(
        self,
        hmi_repo: HMIRepository,
        inventory_repo: InventoryRepository,
        attendance_repo: AttendanceRepository,
        ambulance_repo: AmbulanceRepository,
        equipment_repo: EquipmentRepository,
    ):
        self.hmi_repo = hmi_repo
        self.inventory_repo = inventory_repo
        self.attendance_repo = attendance_repo
        self.ambulance_repo = ambulance_repo
        self.equipment_repo = equipment_repo

    async def calculate_hmi(self, hospital_id: str) -> HMIScoreResponse:
        # 1. Calculate Inventory Score
        inventory_items = await self.inventory_repo.get_low_stock_items(hospital_id)
        # Mocking total inventory items for ratio computation
        total_items = 20.0
        low_stock_count = len(inventory_items)
        in_stock_items = max(0, total_items - low_stock_count)
        inventory_score = (in_stock_items / total_items) * 100.0

        # 2. Calculate Attendance Score
        attendance_summary = await self.attendance_repo.get_daily_summary(hospital_id, "")
        attendance_score = attendance_summary.get("attendance_rate", 90.0)

        # 3. Calculate Patient Load Score
        # Occupancy rate optimal range is 70% to 85%
        # For simplicity, we calculate a score based on a dummy bed occupancy rate of 75%
        patient_load_score = 95.0

        # 4. Calculate Diagnostics Score
        equipment_list, total_eq = await self.equipment_repo.get_by_hospital(hospital_id, limit=100)
        operational_eq = sum(1 for eq in equipment_list if eq.get("status") == "operational")
        diagnostics_score = (operational_eq / total_eq * 100) if total_eq > 0 else 90.0

        # 5. Calculate Equipment Health Score
        maintenance_due = await self.equipment_repo.get_maintenance_due(hospital_id)
        due_count = len(maintenance_due)
        healthy_eq = max(0, operational_eq - due_count)
        equipment_health_score = (healthy_eq / total_eq * 100) if total_eq > 0 else 85.0

        # 6. Calculate Ambulance Readiness Score
        amb_summary = await self.ambulance_repo.get_fleet_summary(hospital_id)
        total_amb = sum(amb_summary.values())
        avail_amb = amb_summary.get("available", 0)
        ambulance_readiness_score = (avail_amb / total_amb * 100) if total_amb > 0 else 100.0

        # 7. Calculate Infrastructure Score (beds/ventilators availability)
        infrastructure_score = 88.0

        # 8. Operational Compliance Score (average of other dimensions)
        compliance_base = [
            inventory_score,
            attendance_score,
            patient_load_score,
            diagnostics_score,
            equipment_health_score,
            ambulance_readiness_score,
            infrastructure_score,
        ]
        operational_compliance_score = sum(compliance_base) / len(compliance_base)

        # 9. Compute Overall Score
        # (inventory 15%, attendance 15%, patient_load 15%, diagnostics 10%, equipment 10%, ambulance 10%, infrastructure 15%, compliance 10%)
        overall_score = (
            inventory_score * 0.15 +
            attendance_score * 0.15 +
            patient_load_score * 0.15 +
            diagnostics_score * 0.10 +
            equipment_health_score * 0.10 +
            ambulance_readiness_score * 0.10 +
            infrastructure_score * 0.15 +
            operational_compliance_score * 0.10
        )

        # 10. Generate recommendations based on low scores (< 80)
        recommendations = []
        if inventory_score < 80:
            recommendations.append("Restock low inventory medicines immediately to prevent stockouts.")
        if attendance_score < 80:
            recommendations.append("Address department-level attendance issues and review staffing schedules.")
        if equipment_health_score < 80:
            recommendations.append("Schedule overdue maintenance for critical diagnostic equipment.")
        if ambulance_readiness_score < 80:
            recommendations.append("Audit ambulance status and deploy fleet repairs.")
        if not recommendations:
            recommendations.append("Maintain current operational compliance levels. Perform standard audits.")

        score_dict = {
            "id": generate_id(),
            "hospital_id": hospital_id,
            "overall_score": round(overall_score, 2),
            "inventory_score": round(inventory_score, 2),
            "attendance_score": round(attendance_score, 2),
            "patient_load_score": round(patient_load_score, 2),
            "diagnostics_score": round(diagnostics_score, 2),
            "equipment_health_score": round(equipment_health_score, 2),
            "ambulance_readiness_score": round(ambulance_readiness_score, 2),
            "infrastructure_score": round(infrastructure_score, 2),
            "operational_compliance_score": round(operational_compliance_score, 2),
            "calculated_at": utc_now(),
            "period": "daily",
            "department_contributions": {
                "Cardiology": round(overall_score * 0.4, 2),
                "Pediatrics": round(overall_score * 0.3, 2),
                "Emergency": round(overall_score * 0.3, 2),
            },
            "recommendations": recommendations,
        }

        res = await self.hmi_repo.create_for_hospital(hospital_id, score_dict)
        return HMIScoreResponse(**res)

    async def get_current_score(self, hospital_id: str) -> HMIScoreResponse:
        res = await self.hmi_repo.get_latest(hospital_id)
        if not res:
            # Recalculate on demand
            return await self.calculate_hmi(hospital_id)
        return HMIScoreResponse(**res)

    async def get_history(self, hospital_id: str, limit: int = 30) -> HMITrendResponse:
        scores = await self.hmi_repo.get_history(hospital_id, limit=limit)
        
        # Calculate trend direction
        trend = "stable"
        avg_score = 0.0
        if len(scores) >= 2:
            avg_score = sum(s["overall_score"] for s in scores) / len(scores)
            latest = scores[0]["overall_score"]
            earliest = scores[-1]["overall_score"]
            if latest > earliest + 1.0:
                trend = "improving"
            elif latest < earliest - 1.0:
                trend = "declining"
        elif scores:
            avg_score = scores[0]["overall_score"]

        return HMITrendResponse(
            hospital_id=hospital_id,
            scores=[HMIScoreResponse(**s) for s in scores],
            trend_direction=trend,
            average_score=round(avg_score, 2),
        )

    async def get_department_contributions(self, hospital_id: str) -> dict[str, float]:
        return await self.hmi_repo.get_department_contributions(hospital_id)
