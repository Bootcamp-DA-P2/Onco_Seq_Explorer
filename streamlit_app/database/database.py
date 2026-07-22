"""SQLite connection helpers."""

from __future__ import annotations

import sqlite3

from streamlit_app.config import config


def get_connection() -> sqlite3.Connection:
    return sqlite3.connect(config.DB_PATH)