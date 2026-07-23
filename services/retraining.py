"""Manual retraining service using clinically confirmed cases."""

from __future__ import annotations

import json
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import joblib
import pandas as pd
from sklearn.metrics import accuracy_score, f1_score

from src.config import config
from streamlit_app.database.cdss_database import CDSSDatabase


class RetrainingService:
    def __init__(self):
        self.db = CDSSDatabase()

    def is_available(self) -> bool:
        return True

    def _build_training_frame(self, cases: List[Dict[str, Any]]) -> pd.DataFrame:
        rows = []
        for case in cases:
            raw = case.get("sample_values_json")
            if not raw:
                continue
            try:
                sample_map = json.loads(raw)
                if isinstance(sample_map, dict):
                    sample_map["_confirmed_label"] = str(case.get("confirmed_diagnosis", "")).upper()
                    rows.append(sample_map)
            except Exception:
                continue
        if not rows:
            return pd.DataFrame()
        return pd.DataFrame(rows)

    def run_manual_retraining(self) -> Dict[str, Any]:
        cases = self.db.get_confirmed_retraining_cases()
        frame = self._build_training_frame(cases)

        if frame.empty or "_confirmed_label" not in frame.columns:
            return {
                "ok": False,
                "message": "No hay suficientes casos confirmados para reentrenar.",
            }

        y_confirmed = frame.pop("_confirmed_label").astype(str)
        x = frame.apply(pd.to_numeric, errors="coerce").fillna(0.0)

        if x.shape[0] < 3:
            return {
                "ok": False,
                "message": "Se requieren al menos 3 casos confirmados para lanzar reentrenamiento.",
            }

        model1 = joblib.load(config.MODEL1_PATH)
        model2 = joblib.load(config.MODEL2_PATH)

        y_stage1 = y_confirmed.apply(lambda label: "NORMAL" if label == "NORMAL" else "TUMOR")

        retrained_model1 = deepcopy(model1)
        retrained_model1.fit(x, y_stage1)
        pred1 = retrained_model1.predict(x)

        tumor_mask = y_stage1 == "TUMOR"
        retrained_model2 = deepcopy(model2)
        model2_metrics = {"n_samples": int(tumor_mask.sum())}
        if int(tumor_mask.sum()) >= 2:
            x_tumor = x[tumor_mask]
            y_tumor = y_confirmed[tumor_mask]
            retrained_model2.fit(x_tumor, y_tumor)
            pred2 = retrained_model2.predict(x_tumor)
            model2_metrics.update(
                {
                    "f1_macro": float(f1_score(y_tumor, pred2, average="macro")),
                    "accuracy": float(accuracy_score(y_tumor, pred2)),
                }
            )
        else:
            model2_metrics.update({"f1_macro": None, "accuracy": None})

        model1_metrics = {
            "f1_macro": float(f1_score(y_stage1, pred1, average="macro")),
            "accuracy": float(accuracy_score(y_stage1, pred1)),
            "n_samples": int(x.shape[0]),
        }

        version_id = f"v{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        versions_dir = Path(config.MODELS_DIR) / "versions" / version_id
        versions_dir.mkdir(parents=True, exist_ok=True)

        model1_path = versions_dir / "pipeline_modelo1.joblib"
        model2_path = versions_dir / "pipeline_modelo2.joblib"
        metrics_path = versions_dir / "metrics.json"

        joblib.dump(retrained_model1, model1_path)
        joblib.dump(retrained_model2, model2_path)

        metrics_payload = {
            "version_id": version_id,
            "source_cases": int(x.shape[0]),
            "model1": model1_metrics,
            "model2": model2_metrics,
            "created_at": datetime.now().isoformat(timespec="seconds"),
        }
        metrics_path.write_text(json.dumps(metrics_payload, ensure_ascii=True, indent=2), encoding="utf-8")

        self.db.save_model_version(
            {
                "version_id": version_id,
                "source_cases": int(x.shape[0]),
                "model1_path": str(model1_path),
                "model2_path": str(model2_path),
                "metrics_json": json.dumps(metrics_payload),
                "notes": "Version generada desde casos confirmados.",
            }
        )

        return {
            "ok": True,
            "version_id": version_id,
            "source_cases": int(x.shape[0]),
            "model1_metrics": model1_metrics,
            "model2_metrics": model2_metrics,
            "model1_path": str(model1_path),
            "model2_path": str(model2_path),
        }
