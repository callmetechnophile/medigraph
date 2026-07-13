"""AI Engine Package."""

from app.ai.base_predictor import BasePredictor, PredictionResult
from app.ai.inventory_forecaster import InventoryForecaster
from app.ai.attendance_predictor import AttendancePredictor
from app.ai.patient_footfall_forecaster import PatientFootfallForecaster
from app.ai.equipment_predictor import EquipmentPredictor
from app.ai.disease_trend_analyzer import DiseaseTrendAnalyzer
from app.ai.ambulance_demand_predictor import AmbulanceDemandPredictor
from app.ai.anomaly_detector import AnomalyDetector
from app.ai.recommendation_engine import RecommendationEngine

__all__ = [
    "BasePredictor",
    "PredictionResult",
    "InventoryForecaster",
    "AttendancePredictor",
    "PatientFootfallForecaster",
    "EquipmentPredictor",
    "DiseaseTrendAnalyzer",
    "AmbulanceDemandPredictor",
    "AnomalyDetector",
    "RecommendationEngine",
]
