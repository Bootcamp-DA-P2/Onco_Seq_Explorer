"""Inspect SQLite schema for Onco_Seq_Explorer.
Prints table list, PRAGMA table_info for key tables, and sample rows.
"""
import sqlite3
import sys
from pathlib import Path

# Ensure project root is on sys.path so `src` can be imported
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import config

DB_PATH = config.DB_PATH

print(f"Using DB: {DB_PATH}")

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

# List tables
cur.execute("SELECT name, type, sql FROM sqlite_master WHERE type IN ('table','index') ORDER BY name;")
rows = cur.fetchall()
print('\nTables and indexes:')
for r in rows:
    name, typ, sql = r
    print(f"- {typ}: {name}")

tables_to_inspect = ['patients', 'predictions', 'clinical_feedback', 'retraining_buffer']

for t in tables_to_inspect:
    print('\n' + '='*40)
    print(f"Inspecting table: {t}")
    try:
        cur.execute(f"PRAGMA table_info({t});")
        info = cur.fetchall()
        if not info:
            print('  (no such table)')
            continue
        print('  Columns:')
        for col in info:
            cid, name, ctype, notnull, dflt_value, pk = col
            print(f"    - {name} | {ctype} | notnull={notnull} | pk={pk} | default={dflt_value}")

        # show sample rows
        cur.execute(f"SELECT * FROM {t} LIMIT 5;")
        sample = cur.fetchall()
        col_names = [c[1] for c in cur.execute(f"PRAGMA table_info({t});")] if info else []
        print('  Sample rows (up to 5):')
        if sample:
            for row in sample:
                print('   ', row)
        else:
            print('   (no rows)')
    except Exception as e:
        print('  Error inspecting table:', e)

conn.close()
print('\nDone.')
