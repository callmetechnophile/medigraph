"""Inventory forecaster — Forecasts item stockout dates and reorder quantities."""

from __future__ import annotations

from typing import Any
import numpy as np

from app.ai.base_predictor import BasePredictor, PredictionResult

class InventoryForecaster(BasePredictor):
    async def predict(self, data: dict[str, Any]) -> list[PredictionResult]:
        items = data.get("items", [])
        results = []

        for item in items:
            history = item.get("consumption_history", [])
            current_stock = item.get("current_stock", 0)
            reorder_level = item.get("reorder_level", 10)
            med_name = item.get("medicine_name", "Unknown Medicine")

            daily_consumption = self._estimate_daily_consumption(history)
            
            if daily_consumption > 0:
                days_to_stockout = current_stock / daily_consumption
                expected_stockout_days = int(np.ceil(days_to_stockout))
                
                # Formulate forecast action
                if expected_stockout_days <= 5:
                    priority = "critical"
                    suggested_action = f"Place emergency order for {med_name}."
                elif expected_stockout_days <= 10:
                    priority = "high"
                    suggested_action = f"Submit purchase request for {med_name}."
                else:
                    priority = "medium"
                    suggested_action = f"Monitor stock levels of {med_name}."

                results.append(PredictionResult(
                    prediction=f"Stockout expected in {expected_stockout_days} days.",
                    reason=f"Current stock of {current_stock} units. Daily consumption rate is {round(daily_consumption, 2)} units.",
                    confidence=0.90 if len(history) >= 7 else 0.60,
                    priority=priority,
                    expected_impact="Ensures medication availability for patients.",
                    suggested_action=suggested_action,
                    metadata={"medicine_name": med_name, "daily_consumption": daily_consumption, "days_to_stockout": expected_stockout_days}
                ))
            
        return results

    def _estimate_daily_consumption(self, history: list[dict[str, Any]]) -> float:
        """Estimate the average daily consumption rate based on history."""
        if not history:
            return 2.0  # default fallback consumption rate
        quantities = [h.get("quantity", 0) for h in history]
        return float(np.mean(quantities))
