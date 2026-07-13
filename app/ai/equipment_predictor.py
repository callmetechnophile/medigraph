"""Equipment predictor — Predicts device failure and schedule maintenance windows."""

from __future__ import annotations

from typing import Any
import numpy as np

from app.ai.base_predictor import BasePredictor, PredictionResult

class EquipmentPredictor(BasePredictor):
    async def predict(self, data: dict[str, Any]) -> list[PredictionResult]:
        equipment = data.get("equipment", [])
        results = []

        for eq in equipment:
            name = eq.get("name", "Unknown Equipment")
            usage_hours = eq.get("usage_hours", 0.0)
            status = eq.get("status", "operational")
            # Assume standard MTBF of 2000 hours
            mtbf = 2000.0
            
            prob = self._calculate_failure_probability(usage_hours, mtbf)
            
            if prob > 0.4:
                priority = "critical" if prob > 0.7 else "high"
                results.append(PredictionResult(
                    prediction=f"Failure risk of {round(prob * 100, 1)}% detected.",
                    reason=f"Current cumulative usage hours {usage_hours} is approaching MTBF limits ({mtbf} hours).",
                    confidence=0.90,
                    priority=priority,
                    expected_impact=f"Unexpected downtime for diagnostic device {name}.",
                    suggested_action=f"Schedule preventative maintenance for {name} immediately.",
                    metadata={"equipment_name": name, "failure_probability": prob}
                ))

        return results

    def _calculate_failure_probability(self, usage_hours: float, mtbf: float) -> float:
        # Standard reliability formula: R(t) = exp(-t/MTBF). Failure probability F(t) = 1 - R(t)
        return float(1.0 - np.exp(-usage_hours / mtbf))
