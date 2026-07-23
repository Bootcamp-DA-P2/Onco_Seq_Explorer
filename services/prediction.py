"""Prediction service for hierarchical inference orchestration."""

from __future__ import annotations

from typing import Any, Dict

import pandas as pd

from managers.prediction_manager import PredictionManager


class PredictionService:
    """Facade around PredictionManager for page-level orchestration."""

    def __init__(self):
        self.manager = PredictionManager()

    def is_available(self) -> bool:
        return True

    def analyze_sample(
        self,
        sample_df: pd.DataFrame,
        sample_name: str,
        user_notes: str,
        patient_context: Dict[str, Any],
        validation_summary: Dict[str, Any],
    ) -> Dict[str, Any]:
        return self.manager.run_prediction(
            sample_df=sample_df,
            sample_name=sample_name,
            user_notes=user_notes,
            patient_context=patient_context,
            validation_summary=validation_summary,
        )