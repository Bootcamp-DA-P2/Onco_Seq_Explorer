import sqlite3
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from src.config import config


class CDSSDatabase:
    def __init__(self, db_path: Path | None = None):
        self.db_path = Path(db_path) if db_path else Path(config.DB_PATH)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()

    def _get_conn(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_database(self):
        with self._get_conn() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS patients (
                    patient_id TEXT PRIMARY KEY,
                    first_name TEXT,
                    last_name TEXT,
                    age INTEGER,
                    sex TEXT,
                    nationality TEXT,
                    weight_kg REAL,
                    height_cm REAL,
                    bmi REAL,
                    bmi_classification TEXT,
                    smoker_status TEXT,
                    cohort TEXT,
                    clinical_notes TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS predictions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    patient_id TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    age INTEGER,
                    sex TEXT,
                    nationality TEXT,
                    weight_kg REAL,
                    height_cm REAL,
                    bmi REAL,
                    bmi_classification TEXT,
                    smoker_status TEXT,
                    sample_name TEXT NOT NULL,
                    sample_values_json TEXT,
                    validation_summary_json TEXT,
                    stage1_prediction TEXT NOT NULL,
                    stage1_probability REAL NOT NULL,
                    stage2_prediction TEXT,
                    stage2_probability REAL,
                    final_prediction TEXT NOT NULL,
                    confidence_level TEXT,
                    n_features INTEGER,
                    user_notes TEXT,
                    validated BOOLEAN DEFAULT 0,
                    is_tumor INTEGER DEFAULT 0,
                    processed INTEGER DEFAULT 0,
                    model2_probabilities_json TEXT,
                    confirmed_diagnosis TEXT,
                    case_status TEXT DEFAULT 'PENDIENTE_VALIDACION',
                    comparison_result TEXT,
                    is_correct BOOLEAN,
                    retraining_eligible INTEGER DEFAULT 0,
                    confirmed_at DATETIME
                )
                """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS clinical_feedback (
                    feedback_id TEXT PRIMARY KEY,
                    prediction_id TEXT NOT NULL UNIQUE,
                    confirmed_diagnosis TEXT NOT NULL,
                    feedback_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                    clinical_notes TEXT,
                    is_correct BOOLEAN
                )
                """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS retraining_buffer (
                    buffer_id TEXT PRIMARY KEY,
                    prediction_id TEXT NOT NULL UNIQUE,
                    patient_id TEXT NOT NULL,
                    label_true TEXT NOT NULL,
                    sample_data TEXT NOT NULL,
                    gene_names_json TEXT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    processed BOOLEAN DEFAULT 0
                )
                """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS model_versions (
                    version_id TEXT PRIMARY KEY,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    source_cases INTEGER NOT NULL,
                    model1_path TEXT,
                    model2_path TEXT,
                    metrics_json TEXT,
                    notes TEXT
                )
                """
            )
            conn.commit()
            self._migrate_schema(conn)

    def _migrate_schema(self, conn):
        cur = conn.cursor()
        migrations = {
            "patients": [
                ("first_name", "TEXT DEFAULT NULL"),
                ("last_name", "TEXT DEFAULT NULL"),
                ("nationality", "TEXT DEFAULT NULL"),
                ("weight_kg", "REAL DEFAULT NULL"),
                ("height_cm", "REAL DEFAULT NULL"),
                ("bmi", "REAL DEFAULT NULL"),
                ("bmi_classification", "TEXT DEFAULT NULL"),
                ("smoker_status", "TEXT DEFAULT NULL"),
            ],
            "predictions": [
                ("patient_id", "TEXT DEFAULT NULL"),
                ("first_name", "TEXT DEFAULT NULL"),
                ("last_name", "TEXT DEFAULT NULL"),
                ("age", "INTEGER DEFAULT NULL"),
                ("sex", "TEXT DEFAULT NULL"),
                ("nationality", "TEXT DEFAULT NULL"),
                ("weight_kg", "REAL DEFAULT NULL"),
                ("height_cm", "REAL DEFAULT NULL"),
                ("bmi", "REAL DEFAULT NULL"),
                ("bmi_classification", "TEXT DEFAULT NULL"),
                ("smoker_status", "TEXT DEFAULT NULL"),
                ("sample_values_json", "TEXT DEFAULT NULL"),
                ("validation_summary_json", "TEXT DEFAULT NULL"),
                ("is_tumor", "INTEGER DEFAULT 0"),
                ("processed", "INTEGER DEFAULT 0"),
                ("model2_probabilities_json", "TEXT DEFAULT NULL"),
                ("confirmed_diagnosis", "TEXT DEFAULT NULL"),
                ("case_status", "TEXT DEFAULT 'PENDIENTE_VALIDACION'"),
                ("comparison_result", "TEXT DEFAULT NULL"),
                ("is_correct", "BOOLEAN DEFAULT NULL"),
                ("retraining_eligible", "INTEGER DEFAULT 0"),
                ("confirmed_at", "DATETIME DEFAULT NULL"),
            ],
            "clinical_feedback": [("is_correct", "BOOLEAN DEFAULT NULL")],
            "retraining_buffer": [("processed", "BOOLEAN DEFAULT 0")],
            "model_versions": [
                ("source_cases", "INTEGER DEFAULT 0"),
                ("model1_path", "TEXT DEFAULT NULL"),
                ("model2_path", "TEXT DEFAULT NULL"),
                ("metrics_json", "TEXT DEFAULT NULL"),
                ("notes", "TEXT DEFAULT NULL"),
            ],
        }
        for table, cols in migrations.items():
            cur.execute(f"PRAGMA table_info({table});")
            existing = [r[1] for r in cur.fetchall()]
            if not existing:
                continue
            for col, col_type in cols:
                if col not in existing:
                    cur.execute(f"ALTER TABLE {table} ADD COLUMN {col} {col_type};")
        conn.commit()

    def save_or_update_patient(self, patient: Dict[str, Any]) -> None:
        with self._get_conn() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO patients (
                    patient_id, first_name, last_name, age, sex, nationality,
                    weight_kg, height_cm, bmi, bmi_classification, smoker_status,
                    cohort, clinical_notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(patient_id) DO UPDATE SET
                    first_name = excluded.first_name,
                    last_name = excluded.last_name,
                    age = excluded.age,
                    sex = excluded.sex,
                    nationality = excluded.nationality,
                    weight_kg = excluded.weight_kg,
                    height_cm = excluded.height_cm,
                    bmi = excluded.bmi,
                    bmi_classification = excluded.bmi_classification,
                    smoker_status = excluded.smoker_status,
                    cohort = excluded.cohort,
                    clinical_notes = excluded.clinical_notes,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (
                    str(patient.get("patient_id", "")).strip(),
                    patient.get("first_name"),
                    patient.get("last_name"),
                    patient.get("age"),
                    patient.get("sex"),
                    patient.get("nationality"),
                    patient.get("weight_kg"),
                    patient.get("height_cm"),
                    patient.get("bmi"),
                    patient.get("bmi_classification"),
                    patient.get("smoker_status"),
                    patient.get("cohort"),
                    patient.get("clinical_notes"),
                ),
            )
            conn.commit()

    def save_prediction(self, prediction: Dict[str, Any]) -> int:
        with self._get_conn() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO predictions (
                    patient_id, first_name, last_name, age, sex, nationality,
                    weight_kg, height_cm, bmi, bmi_classification, smoker_status,
                    sample_name, sample_values_json, validation_summary_json,
                    stage1_prediction, stage1_probability, stage2_prediction,
                    stage2_probability, final_prediction, confidence_level,
                    n_features, user_notes, validated, is_tumor,
                    model2_probabilities_json, case_status
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    prediction.get("patient_id"),
                    prediction.get("first_name"),
                    prediction.get("last_name"),
                    prediction.get("age"),
                    prediction.get("sex"),
                    prediction.get("nationality"),
                    prediction.get("weight_kg"),
                    prediction.get("height_cm"),
                    prediction.get("bmi"),
                    prediction.get("bmi_classification"),
                    prediction.get("smoker_status"),
                    prediction.get("sample_name"),
                    prediction.get("sample_values_json"),
                    prediction.get("validation_summary_json"),
                    prediction.get("stage1_prediction"),
                    float(prediction.get("stage1_probability", 0.0)),
                    prediction.get("stage2_prediction"),
                    prediction.get("stage2_probability"),
                    prediction.get("final_prediction"),
                    prediction.get("confidence_level"),
                    int(prediction.get("n_features", 0)),
                    prediction.get("user_notes"),
                    int(bool(prediction.get("validated", False))),
                    int(bool(prediction.get("is_tumor", False))),
                    prediction.get("model2_probabilities_json"),
                    "PENDIENTE_VALIDACION",
                ),
            )
            conn.commit()
            return int(cur.lastrowid)

    def get_predictions(self, limit: int = 500) -> List[Dict[str, Any]]:
        with self._get_conn() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT id, timestamp, patient_id, first_name, last_name, age, sex, nationality,
                       weight_kg, height_cm, bmi, bmi_classification, smoker_status,
                       sample_name, stage1_prediction, stage1_probability, stage2_prediction,
                       stage2_probability, final_prediction, confidence_level, validated, is_tumor,
                       user_notes, model2_probabilities_json, confirmed_diagnosis, case_status,
                       comparison_result, is_correct, retraining_eligible, confirmed_at
                FROM predictions
                ORDER BY id DESC
                LIMIT ?
                """,
                (limit,),
            )
            return [dict(r) for r in cur.fetchall()]

    def confirm_case_validation(self, prediction_id: int, confirmed_diagnosis: str, clinical_notes: str = "") -> Dict[str, Any]:
        confirmed_label = confirmed_diagnosis.strip().upper()
        with self._get_conn() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT id, patient_id, final_prediction, sample_values_json
                FROM predictions
                WHERE id = ?
                """,
                (prediction_id,),
            )
            row = cur.fetchone()
            if row is None:
                return {"ok": False, "message": "Caso no encontrado."}

            predicted_label = str(row["final_prediction"]).strip().upper()
            is_correct = predicted_label == confirmed_label
            comparison_result = "CORRECTO" if is_correct else "INCORRECTO"
            now = datetime.utcnow().isoformat(timespec="seconds")

            cur.execute(
                """
                UPDATE predictions
                SET confirmed_diagnosis = ?,
                    case_status = 'CONFIRMADO',
                    comparison_result = ?,
                    is_correct = ?,
                    retraining_eligible = 1,
                    confirmed_at = ?
                WHERE id = ?
                """,
                (confirmed_label, comparison_result, int(is_correct), now, prediction_id),
            )

            feedback_id = str(uuid.uuid4())
            cur.execute(
                """
                INSERT OR REPLACE INTO clinical_feedback (
                    feedback_id, prediction_id, confirmed_diagnosis, clinical_notes, is_correct
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (feedback_id, str(prediction_id), confirmed_label, clinical_notes, int(is_correct)),
            )

            sample_values_json = row["sample_values_json"]
            if sample_values_json:
                cur.execute(
                    """
                    INSERT OR REPLACE INTO retraining_buffer (
                        buffer_id, prediction_id, patient_id, label_true, sample_data, gene_names_json, processed
                    ) VALUES (?, ?, ?, ?, ?, ?, 0)
                    """,
                    (
                        str(uuid.uuid4()),
                        str(prediction_id),
                        str(row["patient_id"] or f"case-{prediction_id}"),
                        confirmed_label,
                        sample_values_json,
                        "[]",
                    ),
                )

            conn.commit()
            return {
                "ok": True,
                "prediction": predicted_label,
                "confirmed": confirmed_label,
                "comparison_result": comparison_result,
                "is_correct": is_correct,
            }

    def get_confirmed_retraining_cases(self) -> List[Dict[str, Any]]:
        with self._get_conn() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT id, patient_id, final_prediction, confirmed_diagnosis, sample_values_json, confirmed_at
                FROM predictions
                WHERE case_status = 'CONFIRMADO'
                  AND retraining_eligible = 1
                  AND sample_values_json IS NOT NULL
                ORDER BY id ASC
                """
            )
            return [dict(r) for r in cur.fetchall()]

    def save_model_version(self, version: Dict[str, Any]) -> None:
        with self._get_conn() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO model_versions (
                    version_id, source_cases, model1_path, model2_path, metrics_json, notes
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    version.get("version_id"),
                    int(version.get("source_cases", 0)),
                    version.get("model1_path"),
                    version.get("model2_path"),
                    version.get("metrics_json"),
                    version.get("notes"),
                ),
            )
            conn.commit()

    def get_model_versions(self, limit: int = 20) -> List[Dict[str, Any]]:
        with self._get_conn() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT version_id, created_at, source_cases, model1_path, model2_path, metrics_json, notes
                FROM model_versions
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (limit,),
            )
            return [dict(r) for r in cur.fetchall()]

    def save_feedback(
        self,
        feedback_id: str,
        prediction_id: int,
        confirmed_diagnosis: str,
        clinical_notes: str,
        is_correct: bool | None,
    ):
        with self._get_conn() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT OR REPLACE INTO clinical_feedback (
                    feedback_id, prediction_id, confirmed_diagnosis, clinical_notes, is_correct
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (feedback_id, str(prediction_id), confirmed_diagnosis, clinical_notes, is_correct),
            )
            conn.commit()

    def get_statistics(self) -> Dict[str, Any]:
        with self._get_conn() as conn:
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) AS n FROM predictions")
            total = int(cur.fetchone()[0])

            cur.execute("SELECT COUNT(*) FROM predictions WHERE is_tumor = 1")
            tumors = int(cur.fetchone()[0])

            cur.execute("SELECT COUNT(*) FROM predictions WHERE case_status = 'CONFIRMADO'")
            confirmed = int(cur.fetchone()[0])

            return {
                "total_predictions": total,
                "tumor_predictions": tumors,
                "normal_predictions": max(total - tumors, 0),
                "confirmed_cases": confirmed,
                "pending_cases": max(total - confirmed, 0),
            }
