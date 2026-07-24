import uuid
from datetime import datetime
from pathlib import Path
from time import perf_counter
from typing import Any, Dict, List

from postgrest.exceptions import APIError
from database.supabase_client import supabase


class CDSSDatabase:
    def __init__(self, db_path: Path | None = None):
        self.last_timings: Dict[str, Any] = {}
    
    def _get_patient_db_id(self, clinical_patient_id: str) -> int:
        response = (
            supabase
            .table("patients")
            .select("id")
            .eq("clinical_patient_id", clinical_patient_id)
            .maybe_single()
            .execute()
        )

        if not response.data:
            raise ValueError(
                f"No existe el paciente con clinical_patient_id='{clinical_patient_id}'"
            )

        return response.data["id"]
    # def _get_conn(self):
    #     conn = sqlite3.connect(self.db_path)
    #     conn.row_factory = sqlite3.Row
    #     return conn

    # def _init_database(self):
    #     with self._get_conn() as conn:
    #         cur = conn.cursor()
    #         cur.execute(
    #             """
    #             CREATE TABLE IF NOT EXISTS patients (
    #                 patient_id TEXT PRIMARY KEY,
    #                 first_name TEXT,
    #                 last_name TEXT,
    #                 age INTEGER,
    #                 sex TEXT,
    #                 nationality TEXT,
    #                 weight_kg REAL,
    #                 height_cm REAL,
    #                 bmi REAL,
    #                 bmi_classification TEXT,
    #                 smoker_status TEXT,
    #                 cohort TEXT,
    #                 clinical_notes TEXT,
    #                 created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    #                 updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    #             )
    #             """
    #         )
    #         cur.execute(
    #             """
    #             CREATE TABLE IF NOT EXISTS predictions (
    #                 id INTEGER PRIMARY KEY AUTOINCREMENT,
    #                 timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    #                 patient_id TEXT,
    #                 first_name TEXT,
    #                 last_name TEXT,
    #                 age INTEGER,
    #                 sex TEXT,
    #                 nationality TEXT,
    #                 weight_kg REAL,
    #                 height_cm REAL,
    #                 bmi REAL,
    #                 bmi_classification TEXT,
    #                 smoker_status TEXT,
    #                 sample_name TEXT NOT NULL,
    #                 sample_values_json TEXT,
    #                 validation_summary_json TEXT,
    #                 stage1_prediction TEXT NOT NULL,
    #                 stage1_probability REAL NOT NULL,
    #                 stage2_prediction TEXT,
    #                 stage2_probability REAL,
    #                 final_prediction TEXT NOT NULL,
    #                 confidence_level TEXT,
    #                 n_features INTEGER,
    #                 user_notes TEXT,
    #                 validated BOOLEAN DEFAULT 0,
    #                 is_tumor INTEGER DEFAULT 0,
    #                 processed INTEGER DEFAULT 0,
    #                 model2_probabilities_json TEXT,
    #                 confirmed_diagnosis TEXT,
    #                 case_status TEXT DEFAULT 'PENDIENTE_VALIDACION',
    #                 comparison_result TEXT,
    #                 is_correct BOOLEAN,
    #                 retraining_eligible INTEGER DEFAULT 0,
    #                 confirmed_at DATETIME
    #             )
    #             """
    #         )
    #         cur.execute(
    #             """
    #             CREATE TABLE IF NOT EXISTS clinical_feedback (
    #                 feedback_id TEXT PRIMARY KEY,
    #                 prediction_id TEXT NOT NULL UNIQUE,
    #                 confirmed_diagnosis TEXT NOT NULL,
    #                 feedback_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    #                 clinical_notes TEXT,
    #                 is_correct BOOLEAN
    #             )
    #             """
    #         )
    #         cur.execute(
    #             """
    #             CREATE TABLE IF NOT EXISTS retraining_buffer (
    #                 buffer_id TEXT PRIMARY KEY,
    #                 prediction_id TEXT NOT NULL UNIQUE,
    #                 patient_id TEXT NOT NULL,
    #                 label_true TEXT NOT NULL,
    #                 sample_data TEXT NOT NULL,
    #                 gene_names_json TEXT NOT NULL,
    #                 created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    #                 processed BOOLEAN DEFAULT 0
    #             )
    #             """
    #         )
    #         cur.execute(
    #             """
    #             CREATE TABLE IF NOT EXISTS model_versions (
    #                 version_id TEXT PRIMARY KEY,
    #                 created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    #                 source_cases INTEGER NOT NULL,
    #                 model1_path TEXT,
    #                 model2_path TEXT,
    #                 metrics_json TEXT,
    #                 notes TEXT
    #             )
    #             """
    #         )
    #         conn.commit()
    #         self._migrate_schema(conn)

    # def _migrate_schema(self, conn):
    #     cur = conn.cursor()
    #     migrations = {
    #         "patients": [
    #             ("first_name", "TEXT DEFAULT NULL"),
    #             ("last_name", "TEXT DEFAULT NULL"),
    #             ("nationality", "TEXT DEFAULT NULL"),
    #             ("weight_kg", "REAL DEFAULT NULL"),
    #             ("height_cm", "REAL DEFAULT NULL"),
    #             ("bmi", "REAL DEFAULT NULL"),
    #             ("bmi_classification", "TEXT DEFAULT NULL"),
    #             ("smoker_status", "TEXT DEFAULT NULL"),
    #         ],
    #         "predictions": [
    #             ("patient_id", "TEXT DEFAULT NULL"),
    #             ("first_name", "TEXT DEFAULT NULL"),
    #             ("last_name", "TEXT DEFAULT NULL"),
    #             ("age", "INTEGER DEFAULT NULL"),
    #             ("sex", "TEXT DEFAULT NULL"),
    #             ("nationality", "TEXT DEFAULT NULL"),
    #             ("weight_kg", "REAL DEFAULT NULL"),
    #             ("height_cm", "REAL DEFAULT NULL"),
    #             ("bmi", "REAL DEFAULT NULL"),
    #             ("bmi_classification", "TEXT DEFAULT NULL"),
    #             ("smoker_status", "TEXT DEFAULT NULL"),
    #             ("sample_values_json", "TEXT DEFAULT NULL"),
    #             ("validation_summary_json", "TEXT DEFAULT NULL"),
    #             ("is_tumor", "INTEGER DEFAULT 0"),
    #             ("processed", "INTEGER DEFAULT 0"),
    #             ("model2_probabilities_json", "TEXT DEFAULT NULL"),
    #             ("confirmed_diagnosis", "TEXT DEFAULT NULL"),
    #             ("case_status", "TEXT DEFAULT 'PENDIENTE_VALIDACION'"),
    #             ("comparison_result", "TEXT DEFAULT NULL"),
    #             ("is_correct", "BOOLEAN DEFAULT NULL"),
    #             ("retraining_eligible", "INTEGER DEFAULT 0"),
    #             ("confirmed_at", "DATETIME DEFAULT NULL"),
    #         ],
    #         "clinical_feedback": [("is_correct", "BOOLEAN DEFAULT NULL")],
    #         "retraining_buffer": [("processed", "BOOLEAN DEFAULT 0")],
    #         "model_versions": [
    #             ("source_cases", "INTEGER DEFAULT 0"),
    #             ("model1_path", "TEXT DEFAULT NULL"),
    #             ("model2_path", "TEXT DEFAULT NULL"),
    #             ("metrics_json", "TEXT DEFAULT NULL"),
    #             ("notes", "TEXT DEFAULT NULL"),
    #         ],
    #     }
        # for table, cols in migrations.items():
        #     cur.execute(f"PRAGMA table_info({table});")
        #     existing = [r[1] for r in cur.fetchall()]
        #     if not existing:
        #         continue
        #     for col, col_type in cols:
        #         if col not in existing:
        #             cur.execute(f"ALTER TABLE {table} ADD COLUMN {col} {col_type};")
        # conn.commit()
    def save_or_update_patient(self, patient: Dict[str, Any]) -> None:
        clinical_patient_id = str(patient.get("patient_id", "")).strip()
        data = {
            "clinical_patient_id": clinical_patient_id,
            "first_name": patient.get("first_name"),
            "last_name": patient.get("last_name"),
            "age": patient.get("age"),
            "sex": patient.get("sex"),
            "nationality": patient.get("nationality"),
            "weight_kg": patient.get("weight_kg"),
            "height_cm": patient.get("height_cm"),
            "bmi": patient.get("bmi"),
            "bmi_classification": patient.get("bmi_classification"),
            "smoker_status": patient.get("smoker_status"),
            "cohort": patient.get("cohort"),
            "notes": patient.get("clinical_notes"),
        }

        existing = (
            supabase
            .table("patients")
            .select("id")
            .eq("clinical_patient_id", clinical_patient_id)
            .limit(1)
            .execute()
        )

        if existing.data:
            (
                supabase
                .table("patients")
                .update(data)
                .eq("id", existing.data[0]["id"])
                .execute()
            )
        else:
            (
                supabase
                .table("patients")
                .insert(data)
                .execute()
            )
    # def save_or_update_patient(self, patient: Dict[str, Any]) -> None:
    #     with self._get_conn() as conn:
    #         cur = conn.cursor()
    #         cur.execute(
    #             """
    #             INSERT INTO patients (
    #                 patient_id, first_name, last_name, age, sex, nationality,
    #                 weight_kg, height_cm, bmi, bmi_classification, smoker_status,
    #                 cohort, clinical_notes
    #             ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    #             ON CONFLICT(patient_id) DO UPDATE SET
    #                 first_name = excluded.first_name,
    #                 last_name = excluded.last_name,
    #                 age = excluded.age,
    #                 sex = excluded.sex,
    #                 nationality = excluded.nationality,
    #                 weight_kg = excluded.weight_kg,
    #                 height_cm = excluded.height_cm,
    #                 bmi = excluded.bmi,
    #                 bmi_classification = excluded.bmi_classification,
    #                 smoker_status = excluded.smoker_status,
    #                 cohort = excluded.cohort,
    #                 clinical_notes = excluded.clinical_notes,
    #                 updated_at = CURRENT_TIMESTAMP
    #             """,
    #             (
    #                 str(patient.get("patient_id", "")).strip(),
    #                 patient.get("first_name"),
    #                 patient.get("last_name"),
    #                 patient.get("age"),
    #                 patient.get("sex"),
    #                 patient.get("nationality"),
    #                 patient.get("weight_kg"),
    #                 patient.get("height_cm"),
    #                 patient.get("bmi"),
    #                 patient.get("bmi_classification"),
    #                 patient.get("smoker_status"),
    #                 patient.get("cohort"),
    #                 patient.get("clinical_notes"),
    #             ),
    #         )
    #         conn.commit()

    # def save_prediction(self, prediction: Dict[str, Any]) -> int:
    #     with self._get_conn() as conn:
    #         cur = conn.cursor()
    #         cur.execute(
    #             """
    #             INSERT INTO predictions (
    #                 patient_id, first_name, last_name, age, sex, nationality,
    #                 weight_kg, height_cm, bmi, bmi_classification, smoker_status,
    #                 sample_name, sample_values_json, validation_summary_json,
    #                 stage1_prediction, stage1_probability, stage2_prediction,
    #                 stage2_probability, final_prediction, confidence_level,
    #                 n_features, user_notes, validated, is_tumor,
    #                 model2_probabilities_json, case_status
    #             )
    #             VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    #             """,
    #             (
    #                 prediction.get("patient_id"),
    #                 prediction.get("first_name"),
    #                 prediction.get("last_name"),
    #                 prediction.get("age"),
    #                 prediction.get("sex"),
    #                 prediction.get("nationality"),
    #                 prediction.get("weight_kg"),
    #                 prediction.get("height_cm"),
    #                 prediction.get("bmi"),
    #                 prediction.get("bmi_classification"),
    #                 prediction.get("smoker_status"),
    #                 prediction.get("sample_name"),
    #                 prediction.get("sample_values_json"),
    #                 prediction.get("validation_summary_json"),
    #                 prediction.get("stage1_prediction"),
    #                 float(prediction.get("stage1_probability", 0.0)),
    #                 prediction.get("stage2_prediction"),
    #                 prediction.get("stage2_probability"),
    #                 prediction.get("final_prediction"),
    #                 prediction.get("confidence_level"),
    #                 int(prediction.get("n_features", 0)),
    #                 prediction.get("user_notes"),
    #                 int(bool(prediction.get("validated", False))),
    #                 int(bool(prediction.get("is_tumor", False))),
    #                 prediction.get("model2_probabilities_json"),
    #                 "PENDIENTE_VALIDACION",
    #             ),
    #         )
    #         conn.commit()
    #         return int(cur.lastrowid)
    def save_prediction(self, prediction: Dict[str, Any]) -> int:
        timings: Dict[str, float | str] = {}

        clinical_patient_id = str(prediction.get("patient_id") or "").strip()
        if not clinical_patient_id:
            raise ValueError("patient_id es obligatorio para guardar la prediccion.")

        t0 = perf_counter()
        patient = (
            supabase
            .table("patients")
            .select("id")
            .eq("clinical_patient_id", clinical_patient_id)
            .maybe_single()
            .execute()
        )
        timings["patient_lookup_ms"] = round((perf_counter() - t0) * 1000.0, 2)

        patient_data = patient.data if patient is not None else None

        if not patient_data:
            # Ensure prediction persistence is resilient for anonymized flows
            # where the patient may not have been pre-created in the same run.
            t0 = perf_counter()
            created = (
                supabase
                .table("patients")
                .insert({"clinical_patient_id": clinical_patient_id})
                .execute()
            )
            timings["patient_create_ms"] = round((perf_counter() - t0) * 1000.0, 2)

            created_data = created.data if created is not None else None

            if not created_data:
                raise ValueError(
                    f"No fue posible crear el paciente con clinical_patient_id={clinical_patient_id}"
                )
            patient_id = created_data[0]["id"]
        else:
            patient_id = patient_data["id"]

        sample_id = prediction.get("sample_id")
        if not sample_id:
            sample_id = str(prediction.get("sample_name") or f"sample_{uuid.uuid4().hex[:12]}")

        sample_row = {
            "sample_id": sample_id,
            "patient_id": patient_id,
            "source_patient_id": clinical_patient_id,
            "tipo": "tumor" if bool(prediction.get("is_tumor", False)) else "normal",
            "cohorte": (
                prediction.get("stage2_prediction")
                if bool(prediction.get("is_tumor", False))
                else prediction.get("cohort")
            ) or "BRCA",
            "fecha_carga": datetime.utcnow().isoformat(timespec="seconds"),
        }

        t0 = perf_counter()
        try:
            (
                supabase
                .table("samples")
                .upsert(sample_row, on_conflict="sample_id")
                .execute()
            )
        except APIError as exc:
            # Some deployments enforce a strict cohort CHECK constraint.
            # Retry once with a known valid cohort to keep persistence stable.
            if "muestras_cohorte_check" not in str(exc):
                raise
            sample_row["cohorte"] = "BRCA"
            (
                supabase
                .table("samples")
                .upsert(sample_row, on_conflict="sample_id")
                .execute()
            )
        timings["sample_upsert_ms"] = round((perf_counter() - t0) * 1000.0, 2)

        data = {
            "patient_id": patient_id,
            "sample_id": sample_id,
            "sample_values_json": prediction.get("sample_values_json"),
            "validation_summary_json": prediction.get("validation_summary_json"),
            "stage1_prediction": prediction.get("stage1_prediction"),
            "stage1_probability": float(prediction.get("stage1_probability", 0.0)),
            "stage2_prediction": prediction.get("stage2_prediction"),
            "stage2_probability": prediction.get("stage2_probability"),
            "final_prediction": prediction.get("final_prediction"),
            "confidence_level": prediction.get("confidence_level"),
            "n_features": int(prediction.get("n_features", 0)),
            "user_notes": prediction.get("user_notes"),
            "validated": bool(prediction.get("validated", False)),
            "is_tumor": bool(prediction.get("is_tumor", False)),
            "processed": False,
            "model2_probabilities_json": prediction.get("model2_probabilities_json"),
            "case_status": "PENDIENTE_VALIDACION",
            "comparison_result": None,
            "retraining_eligible": False,
            "version_id": prediction.get("version_id"),
        }

        # Idempotency guard: keep one prediction per sample_id.
        # If Streamlit re-runs the action or the user re-clicks, return existing row.
        t0 = perf_counter()
        existing_prediction = (
            supabase
            .table("predictions")
            .select("id")
            .eq("sample_id", sample_id)
            .limit(1)
            .execute()
        )
        timings["prediction_lookup_ms"] = round((perf_counter() - t0) * 1000.0, 2)

        if existing_prediction.data:
            timings["prediction_write_mode"] = "reuse_existing"
            timings["prediction_write_ms"] = 0.0
            self.last_timings = timings
            return int(existing_prediction.data[0]["id"])

        t0 = perf_counter()
        response = (
            supabase
            .table("predictions")
            .insert(data)
            .execute()
        )
        timings["prediction_write_mode"] = "insert"
        timings["prediction_write_ms"] = round((perf_counter() - t0) * 1000.0, 2)
        self.last_timings = timings

        return response.data[0]["id"]

    # def get_predictions(self, limit: int = 500) -> List[Dict[str, Any]]:
    #     with self._get_conn() as conn:
    #         cur = conn.cursor()
    #         cur.execute(
    #             """
    #             SELECT id, timestamp, patient_id, first_name, last_name, age, sex, nationality,
    #                    weight_kg, height_cm, bmi, bmi_classification, smoker_status,
    #                    sample_name, stage1_prediction, stage1_probability, stage2_prediction,
    #                    stage2_probability, final_prediction, confidence_level, validated, is_tumor,
    #                    user_notes, model2_probabilities_json, confirmed_diagnosis, case_status,
    #                    comparison_result, is_correct, retraining_eligible, confirmed_at
    #             FROM predictions
    #             ORDER BY id DESC
    #             LIMIT ?
    #             """,
    #             (limit,),
    #         )
    #         return [dict(r) for r in cur.fetchall()]

    def get_predictions(self, limit: int = 500) -> List[Dict[str, Any]]:

        response = (
            supabase
            .table("predictions")
            .select("""
                *,
                patients(
                    clinical_patient_id,
                    first_name,
                    last_name,
                    age,
                    sex,
                    nationality,
                    weight_kg,
                    height_cm,
                    bmi,
                    bmi_classification,
                    smoker_status,
                    cohort,
                    notes
                ),
                samples(
                    sample_id,
                    tipo,
                    cohorte,
                    fecha_carga
                ),
                clinical_feedback(
                    confirmed_diagnosis,
                    clinical_notes,
                    is_correct,
                    feedback_date
                )
            """)
            .order("timestamp", desc=True)
            .limit(limit)
            .execute()
        )

        rows = []
        for row in response.data or []:
            patient_info = row.get("patients") or {}
            sample_info = row.get("samples") or {}
            feedback_info = row.get("clinical_feedback") or []
            if isinstance(feedback_info, list):
                feedback = feedback_info[0] if feedback_info else {}
            else:
                feedback = feedback_info

            rows.append(
                {
                    **row,
                    "patient_id": patient_info.get("clinical_patient_id", row.get("patient_id")),
                    "first_name": patient_info.get("first_name"),
                    "last_name": patient_info.get("last_name"),
                    "age": patient_info.get("age"),
                    "sex": patient_info.get("sex"),
                    "nationality": patient_info.get("nationality"),
                    "weight_kg": patient_info.get("weight_kg"),
                    "height_cm": patient_info.get("height_cm"),
                    "bmi": patient_info.get("bmi"),
                    "bmi_classification": patient_info.get("bmi_classification"),
                    "smoker_status": patient_info.get("smoker_status"),
                    "cohort": patient_info.get("cohort"),
                    "clinical_notes": patient_info.get("notes"),
                    "sample_id": sample_info.get("sample_id", row.get("sample_id")),
                    "sample_tipo": sample_info.get("tipo"),
                    "sample_cohorte": sample_info.get("cohorte"),
                    "sample_fecha_carga": sample_info.get("fecha_carga"),
                    "confirmed_diagnosis": feedback.get("confirmed_diagnosis"),
                    "feedback_date": feedback.get("feedback_date"),
                    "is_correct": feedback.get("is_correct"),
                }
            )

        return rows

    # def confirm_case_validation(self, prediction_id: int, confirmed_diagnosis: str, clinical_notes: str = "") -> Dict[str, Any]:
    #     confirmed_label = confirmed_diagnosis.strip().upper()
    #     with self._get_conn() as conn:
    #         cur = conn.cursor()
    #         cur.execute(
    #             """
    #             SELECT id, patient_id, final_prediction, sample_values_json
    #             FROM predictions
    #             WHERE id = ?
    #             """,
    #             (prediction_id,),
    #         )
    #         row = cur.fetchone()
    #         if row is None:
    #             return {"ok": False, "message": "Caso no encontrado."}

    #         predicted_label = str(row["final_prediction"]).strip().upper()
    #         is_correct = predicted_label == confirmed_label
    #         comparison_result = "CORRECTO" if is_correct else "INCORRECTO"
    #         now = datetime.utcnow().isoformat(timespec="seconds")

    #         cur.execute(
    #             """
    #             UPDATE predictions
    #             SET confirmed_diagnosis = ?,
    #                 case_status = 'CONFIRMADO',
    #                 comparison_result = ?,
    #                 is_correct = ?,
    #                 retraining_eligible = 1,
    #                 confirmed_at = ?
    #             WHERE id = ?
    #             """,
    #             (confirmed_label, comparison_result, int(is_correct), now, prediction_id),
    #         )

    #         feedback_id = str(uuid.uuid4())
    #         cur.execute(
    #             """
    #             INSERT OR REPLACE INTO clinical_feedback (
    #                 feedback_id, prediction_id, confirmed_diagnosis, clinical_notes, is_correct
    #             ) VALUES (?, ?, ?, ?, ?)
    #             """,
    #             (feedback_id, str(prediction_id), confirmed_label, clinical_notes, int(is_correct)),
    #         )

    #         sample_values_json = row["sample_values_json"]
    #         if sample_values_json:
    #             cur.execute(
    #                 """
    #                 INSERT OR REPLACE INTO retraining_buffer (
    #                     buffer_id, prediction_id, patient_id, label_true, sample_data, gene_names_json, processed
    #                 ) VALUES (?, ?, ?, ?, ?, ?, 0)
    #                 """,
    #                 (
    #                     str(uuid.uuid4()),
    #                     str(prediction_id),
    #                     str(row["patient_id"] or f"case-{prediction_id}"),
    #                     confirmed_label,
    #                     sample_values_json,
    #                     "[]",
    #                 ),
    #             )

    #         conn.commit()
    #         return {
    #             "ok": True,
    #             "prediction": predicted_label,
    #             "confirmed": confirmed_label,
    #             "comparison_result": comparison_result,
    #             "is_correct": is_correct,
    #         }

    def confirm_case_validation(
        self,
        prediction_id: int,
        confirmed_diagnosis: str,
        clinical_notes: str = "",
    ) -> Dict[str, Any]:

        confirmed_label = confirmed_diagnosis.strip().upper()

    # Obtener la predicción
        response = (
            supabase
            .table("predictions")
            .select("*")
            .eq("id", prediction_id)
            .single()
            .execute()
        )

        if not response.data:
            return {
                "ok": False,
                "message": "Caso no encontrado."
            }

        prediction = response.data

        predicted_label = prediction["final_prediction"].strip().upper()

        is_correct = predicted_label == confirmed_label

        comparison_result = (
            "CORRECTO"
            if is_correct
            else "INCORRECTO"
        )

    # Actualizar únicamente las columnas existentes
        (
            supabase
            .table("predictions")
            .update({
                "case_status": "CONFIRMADO",
                "comparison_result": comparison_result,
                "retraining_eligible": True,
            })
            .eq("id", prediction_id)
            .execute()
        )

        # Guardar feedback clinico
        feedback_row = {
            "prediction_id": prediction_id,
            "confirmed_diagnosis": confirmed_label,
            "clinical_notes": clinical_notes,
            "is_correct": is_correct,
        }
        feedback_existing = (
            supabase
            .table("clinical_feedback")
            .select("feedback_id")
            .eq("prediction_id", prediction_id)
            .limit(1)
            .execute()
        )
        if feedback_existing.data:
            (
                supabase
                .table("clinical_feedback")
                .update(feedback_row)
                .eq("feedback_id", feedback_existing.data[0]["feedback_id"])
                .execute()
            )
        else:
            (
                supabase
                .table("clinical_feedback")
                .insert({"feedback_id": str(uuid.uuid4()), **feedback_row})
                .execute()
            )

        # Anadir al buffer de reentrenamiento
        if prediction.get("sample_values_json"):

            retraining_row = {
                "prediction_id": prediction_id,
                "patient_id": str(prediction["patient_id"]),
                "label_true": confirmed_label,
                "sample_id": prediction["sample_id"],
                "processed": False,
            }
            retraining_existing = (
                supabase
                .table("retraining_buffer")
                .select("buffer_id")
                .eq("prediction_id", prediction_id)
                .limit(1)
                .execute()
            )
            if retraining_existing.data:
                (
                    supabase
                    .table("retraining_buffer")
                    .update(retraining_row)
                    .eq("buffer_id", retraining_existing.data[0]["buffer_id"])
                    .execute()
                )
            else:
                (
                    supabase
                    .table("retraining_buffer")
                    .insert({"buffer_id": str(uuid.uuid4()), **retraining_row})
                    .execute()
                )

        return {
            "ok": True,
            "prediction": predicted_label,
            "confirmed": confirmed_label,
            "comparison_result": comparison_result,
            "is_correct": is_correct,
        }

    # def get_confirmed_retraining_cases(self) -> List[Dict[str, Any]]:
    #     with self._get_conn() as conn:
    #         cur = conn.cursor()
    #         cur.execute(
    #             """
    #             SELECT id, patient_id, final_prediction, confirmed_diagnosis, sample_values_json, confirmed_at
    #             FROM predictions
    #             WHERE case_status = 'CONFIRMADO'
    #               AND retraining_eligible = 1
    #               AND sample_values_json IS NOT NULL
    #             ORDER BY id ASC
    #             """
    #         )
    #         return [dict(r) for r in cur.fetchall()]

    def get_confirmed_retraining_cases(self) -> List[Dict[str, Any]]:

        response = (
            supabase
            .table("predictions")
            .select("""
                id,
                patient_id,
                final_prediction,
                sample_values_json,
                case_status,
                retraining_eligible,
                clinical_feedback(
                    confirmed_diagnosis,
                    feedback_date
                )
            """)
            .eq("case_status", "CONFIRMADO")
            .eq("retraining_eligible", True)
            .not_.is_("sample_values_json", "null")
            .order("id")
            .execute()
        )

        rows = []
        for row in response.data or []:
            feedback_info = row.get("clinical_feedback") or []
            if isinstance(feedback_info, list):
                feedback = feedback_info[0] if feedback_info else {}
            else:
                feedback = feedback_info
            rows.append(
                {
                    "id": row.get("id"),
                    "patient_id": row.get("patient_id"),
                    "final_prediction": row.get("final_prediction"),
                    "sample_values_json": row.get("sample_values_json"),
                    "case_status": row.get("case_status"),
                    "retraining_eligible": row.get("retraining_eligible"),
                    "confirmed_diagnosis": feedback.get("confirmed_diagnosis"),
                    "feedback_date": feedback.get("feedback_date"),
                }
            )

        return rows

    # def save_model_version(self, version: Dict[str, Any]) -> None:
    #     with self._get_conn() as conn:
    #         cur = conn.cursor()
    #         cur.execute(
    #             """
    #             INSERT INTO model_versions (
    #                 version_id, source_cases, model1_path, model2_path, metrics_json, notes
    #             ) VALUES (?, ?, ?, ?, ?, ?)
    #             """,
    #             (
    #                 version.get("version_id"),
    #                 int(version.get("source_cases", 0)),
    #                 version.get("model1_path"),
    #                 version.get("model2_path"),
    #                 version.get("metrics_json"),
    #                 version.get("notes"),
    #             ),
    #         )
    #         conn.commit()

    def save_model_version(self, version: Dict[str, Any]) -> None:

        data = {
            "version_id": version.get("version_id"),
            "source_cases": int(version.get("source_cases", 0)),
            "model1_path": version.get("model1_path") or version.get("model_path"),
            "model2_path": version.get("model2_path"),
            "metrics_json": version.get("metrics_json"),
            "notes": version.get("notes"),
        }

        (
            supabase
            .table("model_versions")
            .insert(data)
            .execute()
        )

    # def get_model_versions(self, limit: int = 20) -> List[Dict[str, Any]]:
    #     with self._get_conn() as conn:
    #         cur = conn.cursor()
    #         cur.execute(
    #             """
    #             SELECT version_id, created_at, source_cases, model1_path, model2_path, metrics_json, notes
    #             FROM model_versions
    #             ORDER BY created_at DESC
    #             LIMIT ?
    #             """,
    #             (limit,),
    #         )
    #         return [dict(r) for r in cur.fetchall()]

    def get_model_versions(self, limit: int = 20) -> List[Dict[str, Any]]:

        response = (
            supabase
            .table("model_versions")
            .select("""
                version_id,
                created_at,
                source_cases,
                model1_path,
                model2_path,
                metrics_json,
                notes
            """)
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )

        return response.data or []

    # def save_feedback(
    #     self,
    #     feedback_id: str,
    #     prediction_id: int,
    #     confirmed_diagnosis: str,
    #     clinical_notes: str,
    #     is_correct: bool | None,
    # ):
    #     with self._get_conn() as conn:
    #         cur = conn.cursor()
    #         cur.execute(
    #             """
    #             INSERT OR REPLACE INTO clinical_feedback (
    #                 feedback_id, prediction_id, confirmed_diagnosis, clinical_notes, is_correct
    #             ) VALUES (?, ?, ?, ?, ?)
    #             """,
    #             (feedback_id, str(prediction_id), confirmed_diagnosis, clinical_notes, is_correct),
    #         )
    #         conn.commit()

    def save_feedback(
        self,
        feedback_id: str,
        prediction_id: int,
        confirmed_diagnosis: str,
        clinical_notes: str,
        is_correct: bool | None,
    ) -> None:

        data = {
            "prediction_id": prediction_id,
            "confirmed_diagnosis": confirmed_diagnosis,
            "clinical_notes": clinical_notes,
            "is_correct": is_correct,
        }

        existing = (
            supabase
            .table("clinical_feedback")
            .select("feedback_id")
            .eq("prediction_id", prediction_id)
            .limit(1)
            .execute()
        )

        if existing.data:
            (
                supabase
                .table("clinical_feedback")
                .update(data)
                .eq("feedback_id", existing.data[0]["feedback_id"])
                .execute()
            )
        else:
            (
                supabase
                .table("clinical_feedback")
                .insert({"feedback_id": feedback_id, **data})
                .execute()
            )

    # def get_statistics(self) -> Dict[str, Any]:
    #     with self._get_conn() as conn:
    #         cur = conn.cursor()
    #         cur.execute("SELECT COUNT(*) AS n FROM predictions")
    #         total = int(cur.fetchone()[0])

    #         cur.execute("SELECT COUNT(*) FROM predictions WHERE is_tumor = 1")
    #         tumors = int(cur.fetchone()[0])

    #         cur.execute("SELECT COUNT(*) FROM predictions WHERE case_status = 'CONFIRMADO'")
    #         confirmed = int(cur.fetchone()[0])

    #         return {
    #             "total_predictions": total,
    #             "tumor_predictions": tumors,
    #             "normal_predictions": max(total - tumors, 0),
    #             "confirmed_cases": confirmed,
    #             "pending_cases": max(total - confirmed, 0),
    #         }
    def get_statistics(self) -> Dict[str, Any]:

        total = (
            supabase
            .table("predictions")
            .select("id", count="exact")
            .execute()
        ).count

        tumors = (
            supabase
            .table("predictions")
            .select("id", count="exact")
            .eq("is_tumor", True)
            .execute()
        ).count

        confirmed = (
            supabase
            .table("predictions")
            .select("id", count="exact")
            .eq("case_status", "CONFIRMADO")
            .execute()
        ).count

        return {
            "total_predictions": total or 0,
            "tumor_predictions": tumors or 0,
            "normal_predictions": (total or 0) - (tumors or 0),
            "confirmed_cases": confirmed or 0,
            "pending_cases": (total or 0) - (confirmed or 0),
        }

