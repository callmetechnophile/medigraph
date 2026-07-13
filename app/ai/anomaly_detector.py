"""Anomaly detector — Detects spikes and drops in inventory, attendance, etc."""

from __future__ import annotations

from typing import Any
import numpy as np

from app.ai.base_predictor import BasePredictor, PredictionResult

class AnomalyDetector(BasePredictor):
    async def predict(self, data: dict[str, Any]) -> list[PredictionResult]:
        metrics = data.get("metrics", {})
        results = []

        for metric_name, values in metrics.items():
            if len(values) >= 5:
                anomalies = self._detect_anomaly(values)
                if anomalies:
                    last_idx = anomalies[-1]
                    anomaly_value = values[last_idx]
                    results.append(PredictionResult(
                        prediction=f"Operational anomaly detected in metric {metric_name}.",
                        reason=f"Value {anomaly_value} at index {last_idx} deviates significantly from mean behavior.",
                        confidence=0.85,
                        priority="high",
                        expected_impact="Potential system failure or data entry error.",
                        suggested_action=f"Review operations log matching metric {metric_name}.",
                        metadata={"metric_name": metric_name, "anomaly_value": anomaly_value, "index": last_idx}
                    ))

        return results
