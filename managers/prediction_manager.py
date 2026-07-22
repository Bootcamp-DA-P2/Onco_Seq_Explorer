import json
from pathlib import Path
from typing import Any, Dict

import joblib
import numpy as np
import pandas as pd

from database.cdss_database import CDSSDatabase
from src.config import config


class PredictionManager:
    def __init__(self):
        self.db = CDSSDatabase()
        self.model1 = None
        self.model2 = None
        self.feature_names = self._load_feature_names()

    def _load_feature_names(self):
        path = Path(config.MODELS_DIR) / "feature_names.json"
        if not path.exists():
            return []
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)

    def _load_models_if_needed(self):
        if self.model1 is None:
            self.model1 = joblib.load(config.MODEL1_PATH)
        if self.model2 is None:
            self.model2 = joblib.load(config.MODEL2_PATH)

    def _to_wide_row(self, df: pd.DataFrame) -> pd.DataFrame:
        cols = {c.lower(): c for c in df.columns}
        if "gene" in cols and "expression" in cols:
            g = cols["gene"]
            e = cols["expression"]
            row = {str(r[g]): float(r[e]) for _, r in df.iterrows()}
            return pd.DataFrame([row])
        return df.iloc[[0]].copy()

    def preprocess_sample(self, sample_df: pd.DataFrame) -> pd.DataFrame:
        wide = self._to_wide_row(sample_df)
        if self.feature_names:
            for feat in self.feature_names:
                if feat not in wide.columns:
                    wide[feat] = 0.0
            wide = wide[self.feature_names]
        wide = wide.apply(pd.to_numeric, errors="coerce").fillna(0.0)
        return wide

    def run_prediction(self, sample_df: pd.DataFrame, sample_name: str, user_notes: str = "") -> Dict[str, Any]:
        self._load_models_if_needed()
        x = self.preprocess_sample(sample_df)

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

        final_prediction = stage2_label if stage2_label else ("NORMAL" if not is_tumor else "TUMOR")
        confidence = "HIGH" if p1 >= 0.8 else ("MEDIUM" if p1 >= 0.6 else "LOW")

        payload = {
            "sample_name": sample_name,
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
        prediction_id = self.db.save_prediction(payload)
        payload["prediction_id"] = prediction_id
        return payload
