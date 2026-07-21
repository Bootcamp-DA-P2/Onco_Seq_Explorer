import sqlite3
from pathlib import Path
from typing import Dict, Any, List
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
                    age INTEGER,
                    sex TEXT,
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
                    sample_name TEXT NOT NULL,
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
                    model2_probabilities_json TEXT
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
            conn.commit()
            self._migrate_schema(conn)

    def _migrate_schema(self, conn):
        cur = conn.cursor()
        migrations = {
            "predictions": [
                ("is_tumor", "INTEGER DEFAULT 0"),
                ("processed", "INTEGER DEFAULT 0"),
                ("model2_probabilities_json", "TEXT DEFAULT NULL"),
            ],
            "clinical_feedback": [("is_correct", "BOOLEAN DEFAULT NULL")],
            "retraining_buffer": [("processed", "BOOLEAN DEFAULT 0")],
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

    def save_prediction(self, prediction: Dict[str, Any]) -> int:
        with self._get_conn() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO predictions (
                    sample_name, stage1_prediction, stage1_probability,
                    stage2_prediction, stage2_probability, final_prediction,
                    confidence_level, n_features, user_notes, validated, is_tumor,
                    model2_probabilities_json
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    prediction.get("sample_name"),
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
                ),
            )
            conn.commit()
            return int(cur.lastrowid)

    def get_predictions(self, limit: int = 200) -> List[Dict[str, Any]]:
        with self._get_conn() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT id, timestamp, sample_name, stage1_prediction, stage1_probability,
                       stage2_prediction, stage2_probability, final_prediction,
                       confidence_level, validated, is_tumor, user_notes
                FROM predictions
                ORDER BY id DESC
                LIMIT ?
                """,
                (limit,),
            )
            return [dict(r) for r in cur.fetchall()]

    def save_feedback(self, feedback_id: str, prediction_id: int, confirmed_diagnosis: str, clinical_notes: str, is_correct: bool | None):
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

            try:
                cur.execute("SELECT COUNT(*) FROM predictions WHERE is_tumor = 1")
                tumors = int(cur.fetchone()[0])
            except sqlite3.OperationalError:
                cur.execute("SELECT COUNT(*) FROM predictions WHERE upper(final_prediction) <> 'NORMAL'")
                tumors = int(cur.fetchone()[0])
            normals = max(total - tumors, 0)

            return {
                "total_predictions": total,
                "tumor_predictions": tumors,
                "normal_predictions": normals,
            }
