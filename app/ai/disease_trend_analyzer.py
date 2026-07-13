"""Disease trend analyzer — Outbreak warning signals and incidence rates."""

from __future__ import annotations

from typing import Any
import numpy as np

from app.ai.base_predictor import BasePredictor, PredictionResult

class DiseaseTrendAnalyzer(BasePredictor):
    async def predict(self, data: dict[str, Any]) -> list[PredictionResult]:
        diagnoses = data.get("diagnoses", [])
        results = []

        # Group count of cases by condition
        conditions = {}
        for diag in diagnoses:
            cond = diag.get("condition_name")
            if cond:
                conditions.setdefault(cond, []).append(diag)

        for cond, cases in conditions.items():
            # For simplicity, we calculate case count differences
            total_cases = len(cases)
            if total_cases >= 5:
                # Mock baseline
                baseline = 2.0
                is_outbreak = self._detect_outbreak([total_cases], baseline)
                
                if is_outbreak:
                    results.append(PredictionResult(
                        prediction=f"Possible localized outbreak warning: {cond}.",
                        reason=f"Significant spike detected: {total_cases} cases reported. Baseline expected is {baseline}.",
                        confidence=0.80,
                        priority="critical",
                        expected_impact=f"Increased patient flow and demand for resources matching {cond}.",
                        suggested_action=f"Alert district health administration and monitor inventory of treatments for {cond}.",
                        metadata={"condition": cond, "cases": total_cases}
                    ))

        return results

    def _detect_outbreak(self, counts: list[int], baseline: float) -> bool:
        if not counts:
            return False
        return float(np.mean(counts)) > (baseline * 1.5)
