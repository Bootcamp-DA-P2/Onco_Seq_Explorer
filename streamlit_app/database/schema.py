"""Database schema definitions."""


PREDICTIONS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS predictions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    model1_result TEXT,
    model2_result TEXT,
    report_path TEXT,
    status TEXT
);
"""