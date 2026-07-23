"""Run lightweight schema migrations on all .db files under project root.
Adds missing columns to known tables without destructive changes.
"""
import sqlite3
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import config

DB_GLOB = ['*.db', 'data/*.db']

# Desired columns per table: (column_name, sql_definition)
MIGRATIONS = {
    'predictions': [
        ("is_tumor", "INTEGER DEFAULT 0"),
        ("processed", "INTEGER DEFAULT 0"),
        ("model2_probabilities_json", "TEXT DEFAULT NULL"),
    ],
    'clinical_feedback': [
        ("is_correct", "BOOLEAN DEFAULT NULL"),
    ],
    'retraining_buffer': [
        ("processed", "BOOLEAN DEFAULT 0"),
    ],
}


def migrate_db(db_path: Path):
    print(f"\nProcessing DB: {db_path}")
    conn = sqlite3.connect(str(db_path))
    cur = conn.cursor()

    for table, cols in MIGRATIONS.items():
        try:
            cur.execute(f"PRAGMA table_info({table});")
            existing = [r[1] for r in cur.fetchall()]
            if not existing:
                print(f" - Table '{table}' not found, skipping")
                continue
            for col_name, col_def in cols:
                if col_name in existing:
                    print(f" - Column '{col_name}' already exists on '{table}'")
                else:
                    sql = f"ALTER TABLE {table} ADD COLUMN {col_name} {col_def};"
                    try:
                        cur.execute(sql)
                        conn.commit()
                        print(f" + Added column '{col_name}' to '{table}'")
                    except Exception as e:
                        print(f" ! Failed to add column '{col_name}' to '{table}': {e}")
        except Exception as e:
            print(f" ! Error inspecting table '{table}': {e}")

    # show PRAGMA for predictions after migration
    try:
        cur.execute("PRAGMA table_info(predictions);")
        info = cur.fetchall()
        print('\n predictions schema now:')
        for col in info:
            print('  -', col[1], col[2])
    except Exception:
        pass

    conn.close()


if __name__ == '__main__':
    # Collect DB files: include config.DB_PATH and any .db under project
    db_paths = set()
    db_paths.add(Path(config.DB_PATH))
    for p in PROJECT_ROOT.rglob('*.db'):
        db_paths.add(p)

    if not db_paths:
        print('No .db files found')
        sys.exit(0)

    for db in sorted(db_paths):
        migrate_db(db)

    print('\nMigrations completed.')
