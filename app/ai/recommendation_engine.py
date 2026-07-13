"""Recommendation engine — Orchestrates the prediction and suggestions workflow."""

from __future__ import annotations

from typing import Any
import structlog

from app.ai.inventory_forecaster import InventoryForecaster
from app.ai.attendance_predictor import AttendancePredictor
from app.ai.patient_footfall_forecaster import PatientFootfallForecaster
from app.ai.equipment_predictor import EquipmentPredictor
from app.ai.disease_trend_analyzer import DiseaseTrendAnalyzer
from app.ai.ambulance_demand_predictor import AmbulanceDemandPredictor
from app.ai.anomaly_detector import AnomalyDetector
from app.ai.base_predictor import PredictionResult

logger = structlog.get_logger(__name__)

class RecommendationEngine:
    def __init__(
        self,
        inventory_forecaster: InventoryForecaster,
        attendance_predictor: AttendancePredictor,
        footfall_forecaster: PatientFootfallForecaster,
        equipment_predictor: EquipmentPredictor,
        disease_analyzer: DiseaseTrendAnalyzer,
        ambulance_predictor: AmbulanceDemandPredictor,
        anomaly_detector: AnomalyDetector,
    ):
        self.inventory_forecaster = inventory_forecaster
        self.attendance_predictor = attendance_predictor
        self.footfall_forecaster = footfall_forecaster
        self.equipment_predictor = equipment_predictor
        self.disease_analyzer = disease_analyzer
        self.ambulance_predictor = ambulance_predictor
        self.anomaly_detector = anomaly_detector

    async def generate_recommendations(self, hospital_data: dict[str, Any]) -> list[dict[str, Any]]:
        predictions: list[PredictionResult] = []

        # Gather predictions from all active components
        try:
            predictions.extend(await self.inventory_forecaster.predict(hospital_data.get("inventory", {})))
            predictions.extend(await self.attendance_predictor.predict(hospital_data.get("attendance", {})))
            predictions.extend(await self.footfall_forecaster.predict(hospital_data.get("footfall", {})))
            predictions.extend(await self.equipment_predictor.predict(hospital_data.get("equipment", {})))
            predictions.extend(await self.disease_analyzer.predict(hospital_data.get("disease", {})))
            predictions.extend(await self.ambulance_predictor.predict(hospital_data.get("ambulance", {})))
            predictions.extend(await self.anomaly_detector.predict(hospital_data.get("anomaly", {})))
        except Exception as e:
            logger.error("recommendation_engine.prediction_failed", error=str(e))

        # Prioritize and deduplicate
        prioritized = self._prioritize(predictions)
        
        # Format as recommendations ready for DB storage
        formatted = []
        for p in prioritized:
            formatted.append({
                "category": p.metadata.get("category", "general"),
                "title": f"AI Suggestion: {p.prediction[:40]}",
                "description": p.reason,
                "prediction": p.prediction,
                "reason": p.reason,
                "confidence": p.confidence,
                "priority": p.priority,
                "expected_impact": p.expected_impact,
                "suggested_action": p.suggested_action,
                "metadata": p.metadata,
            })
        return formatted

    def _prioritize(self, predictions: list[PredictionResult]) -> list[PredictionResult]:
        priority_map = {"critical": 4, "high": 3, "medium": 2, "low": 1}
        # Sort by priority, then confidence
        return sorted(
            predictions,
            key=lambda x: (priority_map.get(x.priority.lower(), 0), x.confidence),
            reverse=True
        )
