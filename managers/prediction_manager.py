import json
from functools import lru_cache
from pathlib import Path
from time import perf_counter
from typing import Any, Dict

import joblib
import numpy as np
import pandas as pd

from src.config import config
from database.cdss_database import CDSSDatabase


@lru_cache(maxsize=1)
def _cached_feature_names(feature_path: str) -> list[str]:
    path = Path(feature_path)
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as file_handle:
        data = json.load(file_handle)
    return data if isinstance(data, list) else []


@lru_cache(maxsize=1)
def _cached_models(model1_path: str, model2_path: str):
    return joblib.load(model1_path), joblib.load(model2_path)


class PredictionManager:
    def __init__(self):
        self.db = CDSSDatabase()
        self.model1 = None
        self.model2 = None
        self.feature_names = self._load_feature_names()

    def _load_feature_names(self):
        return _cached_feature_names(str(Path(config.MODELS_DIR) / "feature_names.json"))

    def _load_models_if_needed(self):
        if self.model1 is None:
            self.model1, self.model2 = _cached_models(str(config.MODEL1_PATH), str(config.MODEL2_PATH))

    def _to_wide_row(self, df: pd.DataFrame) -> pd.DataFrame:
        cols = {c.lower(): c for c in df.columns}
        if "gene" in cols and "expression" in cols:
            gene_col = cols["gene"]
            expr_col = cols["expression"]
            row = {str(r[gene_col]): float(r[expr_col]) for _, r in df.iterrows()}
            return pd.DataFrame([row])
        return df.iloc[[0]].copy()

    def preprocess_sample(self, sample_df: pd.DataFrame) -> pd.DataFrame:
        wide = self._to_wide_row(sample_df)
        if self.feature_names:
            wide = wide.reindex(columns=self.feature_names, fill_value=0.0).copy()
        wide = wide.apply(pd.to_numeric, errors="coerce").fillna(0.0)
        return wide

    def run_prediction(
        self,
        sample_df: pd.DataFrame,
        sample_name: str,
        user_notes: str = "",
        patient_context: Dict[str, Any] | None = None,
        validation_summary: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]:
        timings: Dict[str, float | str] = {}

        t0 = perf_counter()
        self._load_models_if_needed()
        timings["model_load_ms"] = round((perf_counter() - t0) * 1000.0, 2)

        t0 = perf_counter()
        x = self.preprocess_sample(sample_df)
        timings["preprocess_ms"] = round((perf_counter() - t0) * 1000.0, 2)

        t0 = perf_counter()
        y1 = self.model1.predict(x)[0]
        p1 = float(np.max(self.model1.predict_proba(x)[0])) if hasattr(self.model1, "predict_proba") else 0.5

        stage1_label = str(y1)
        is_tumor = stage1_label.upper() == "TUMOR" or stage1_label == "1"

        stage2_label = None
        stage2_prob = None
        probs2_json = None

        if is_tumor:
            y2 = self.model2.predict(x)[0]
            p2 = self.model2.predict_proba(x)[0] if hasattr(self.model2, "predict_proba") else None
            stage2_label = str(y2)
            if p2 is not None:
                stage2_prob = float(np.max(p2))
                classes2 = [str(c) for c in getattr(self.model2, "classes_", [])]
                probs2_json = json.dumps({c: float(v) for c, v in zip(classes2, p2)})
        timings["inference_ms"] = round((perf_counter() - t0) * 1000.0, 2)

        final_prediction = stage2_label if stage2_label else ("NORMAL" if not is_tumor else "TUMOR")
        confidence = "HIGH" if p1 >= 0.8 else ("MEDIUM" if p1 >= 0.6 else "LOW")

        context = patient_context or {}
        payload = {
            "patient_id": context.get("patient_id"),
            "first_name": context.get("first_name"),
            "last_name": context.get("last_name"),
            "age": context.get("age"),
            "sex": context.get("sex"),
            "nationality": context.get("nationality"),
            "weight_kg": context.get("weight_kg"),
            "height_cm": context.get("height_cm"),
            "bmi": context.get("bmi"),
            "bmi_classification": context.get("bmi_classification"),
            "smoker_status": context.get("smoker_status"),
            "sample_name": sample_name,
            "sample_values_json": json.dumps(x.iloc[0].to_dict()),
            "validation_summary_json": json.dumps(validation_summary or {}),
            "stage1_prediction": stage1_label,
            "stage1_probability": p1,
            "stage2_prediction": stage2_label,
            "stage2_probability": stage2_prob,
            "final_prediction": final_prediction,
            "confidence_level": confidence,
            "n_features": int(x.shape[1]),
            "user_notes": user_notes,
            "validated": True,
            "is_tumor": is_tumor,
            "model2_probabilities_json": probs2_json,
        }

        t0 = perf_counter()
        prediction_id = self.db.save_prediction(payload)
        timings["db_save_ms"] = round((perf_counter() - t0) * 1000.0, 2)

        for key, value in (self.db.last_timings or {}).items():
            if isinstance(value, (int, float)):
                timings[f"db_{key}"] = float(value)
            else:
                timings[f"db_{key}"] = str(value)

        payload["prediction_id"] = prediction_id
        payload["model2_probabilities"] = json.loads(probs2_json) if probs2_json else {}
        payload["_timings"] = timings
        return payload
