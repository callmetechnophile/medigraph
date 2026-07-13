"""Attendance predictor — Evaluates staff attendance patterns and predicts absences."""

from __future__ import annotations

from typing import Any
import numpy as np

from app.ai.base_predictor import BasePredictor, PredictionResult

class AttendancePredictor(BasePredictor):
    async def predict(self, data: dict[str, Any]) -> list[PredictionResult]:
        staff_records = data.get("staff_records", [])
        results = []

        for staff in staff_records:
            history = staff.get("attendance_history", [])
            staff_name = staff.get("name", "Unknown Staff")
            dept_name = staff.get("department_name", "General")

            prob = self._calculate_absence_probability(history)
            if prob > 0.3:
                priority = "high" if prob > 0.6 else "medium"
                results.append(PredictionResult(
                    prediction=f"Absence probability is {round(prob * 100, 1)}% for tomorrow.",
                    reason=f"Historical weekly patterns show recurrent absences for {staff_name}.",
                    confidence=0.80 if len(history) >= 14 else 0.50,
                    priority=priority,
                    expected_impact=f"Staff shortages in the {dept_name} department.",
                    suggested_action=f"Confirm availability of {staff_name} or arrange backup staffing.",
                    metadata={"staff_name": staff_name, "department_name": dept_name, "probability": prob}
                ))

        return results

    def _calculate_absence_probability(self, history: list[dict[str, Any]]) -> float:
        if not history:
            return 0.05  # baseline standard probability
        absences = sum(1 for h in history if h.get("status") == "absent")
        return absences / len(history)
