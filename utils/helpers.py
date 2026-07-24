"""Reusable helper functions for file loading and formatting."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

import pandas as pd


def read_json_file(path: Path) -> Optional[Any]:
    try:
        if not path.exists():
            return None
        with path.open("r", encoding="utf-8") as file_handle:
            return json.load(file_handle)
    except Exception:
        return None


def read_csv_file(path: Path) -> Optional[pd.DataFrame]:
    try:
        if not path.exists():
            return None
        return pd.read_csv(path)
    except Exception:
        return None


def read_parquet_shape(path: Path) -> Optional[tuple[int, int]]:
    try:
        if not path.exists():
            return None
        dataframe = pd.read_parquet(path)
        return dataframe.shape
    except Exception:
        return None


def format_metric(value: Optional[float]) -> str:
    if value is None:
        return "N/D"
    return f"{float(value):.4f}"