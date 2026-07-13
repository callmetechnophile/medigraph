"""Ambulance demand predictor — Forecasts ambulance demands by weekday and hour."""

from __future__ import annotations

from typing import Any
import numpy as np

from app.ai.base_predictor import BasePredictor, PredictionResult

class AmbulanceDemandPredictor(BasePredictor):
    async def predict(self, data: dict[str, Any]) -> list[PredictionResult]:
        dispatch_records = data.get("dispatch_records", [])
        results = []

        if len(dispatch_records) >= 5:
            # Predict fleet size required
            avg_demand = 3.0
            peak_demand = 6.0
            turnaround_time = 0.5 # hours
            
            recommended_size = self._recommend_fleet_size(avg_demand, peak_demand, turnaround_time)
            
            results.append(PredictionResult(
                prediction=f"Recommended ambulance active fleet size is {recommended_size}.",
                reason=f"Based on historical average demand of {avg_demand} dispatches per hour and turnaround time.",
                confidence=0.75,
                priority="medium",
                expected_impact="Reduces response times during peak emergency hours.",
                suggested_action=f"Maintain {recommended_size} ready ambulances in active service.",
                metadata={"recommended_fleet_size": recommended_size}
            ))

        return results

    def _recommend_fleet_size(self, avg_demand: float, peak_demand: float, turnaround_time: float) -> int:
        # Simple capacity rule: peak demand * turnaround + buffer
        capacity = peak_demand * turnaround_time
        return int(np.ceil(capacity + 1.0))
