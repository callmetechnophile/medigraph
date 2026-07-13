"""Patient footfall forecaster — Forecasts daily patient volumes by department."""

from __future__ import annotations

from typing import Any
import numpy as np

from app.ai.base_predictor import BasePredictor, PredictionResult

class PatientFootfallForecaster(BasePredictor):
    async def predict(self, data: dict[str, Any]) -> list[PredictionResult]:
        daily_counts = data.get("daily_counts", [])
        results = []

        if len(daily_counts) >= 7:
            # We forecast the next period (tomorrow) based on simple moving average + trend adjustment
            values = [d.get("count", 0) for d in daily_counts]
            trend = self._calculate_trend(values)
            ma = self._calculate_moving_average(values, window=7)
            
            base_forecast = ma[-1]
            if trend == "increasing":
                forecast = base_forecast * 1.10
            elif trend == "decreasing":
                forecast = base_forecast * 0.90
            else:
                forecast = base_forecast

            rounded_forecast = int(np.ceil(forecast))
            results.append(PredictionResult(
                prediction=f"Expected patient volume tomorrow is {rounded_forecast}.",
                reason=f"Moving average is {round(base_forecast, 1)} with an {trend} trend.",
                confidence=0.85,
                priority="medium",
                expected_impact="Optimal bed allocation and ER waiting times.",
                suggested_action=f"Ensure staffing schedules correspond to an expected load of {rounded_forecast} patients.",
                metadata={"forecast": rounded_forecast, "trend": trend}
            ))

        return results
