"""Base predictor — Abstract parent for operational forecasting engines."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any
import numpy as np
from pydantic import BaseModel

class PredictionResult(BaseModel):
    prediction: str
    reason: str
    confidence: float  # 0.0 to 1.0
    priority: str  # low, medium, high, critical
    expected_impact: str
    suggested_action: str
    metadata: dict[str, Any] = {}

class BasePredictor(ABC):
    @abstractmethod
    async def predict(self, data: dict[str, Any]) -> list[PredictionResult]:
        """Perform predictions based on incoming historical data."""
        pass

    def _calculate_trend(self, values: list[float]) -> str:
        """Determine trend direction using linear regression slope."""
        if len(values) < 2:
            return "stable"
        x = np.arange(len(values))
        y = np.array(values)
        slope = np.polyfit(x, y, 1)[0]
        if slope > 0.05:
            return "increasing"
        elif slope < -0.05:
            return "decreasing"
        return "stable"

    def _calculate_moving_average(self, values: list[float], window: int = 7) -> list[float]:
        """Calculate simple moving average with custom window size."""
        if not values:
            return []
        ret = []
        for i in range(len(values)):
            start = max(0, i - window + 1)
            ret.append(float(np.mean(values[start:i+1])))
        return ret

    def _detect_anomaly(self, values: list[float], threshold: float = 2.0) -> list[int]:
        """Z-score based anomaly detection returning indices of anomalies."""
        if len(values) < 3:
            return []
        mean = np.mean(values)
        std = np.std(values)
        if std == 0:
            return []
        z_scores = [(v - mean) / std for v in values]
        return [i for i, z in enumerate(z_scores) if abs(z) > threshold]
