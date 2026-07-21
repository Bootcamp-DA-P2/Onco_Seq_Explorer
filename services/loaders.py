"""Model and artifact loading services."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

import joblib

from config import config
from utils.helpers import read_json_file
from utils.logger import get_logger


logger = get_logger(__name__)


class ArtifactLoader:
    """Loads trained artifacts and metadata for UI consumption."""

    def __init__(self) -> None:
        self.required_files: Dict[str, Path] = {
            "pipeline_modelo1.joblib": config.MODEL1_PATH,
            "pipeline_modelo2.joblib": config.MODEL2_PATH,
            "feature_names.json": config.FEATURE_NAMES_PATH,
            "metadata_modelo1.json": config.METADATA_MODEL1_PATH,
            "metadata_modelo2.json": config.METADATA_MODEL2_PATH,
        }

    def _load_joblib(self, path: Path) -> Dict[str, Any]:
        if not path.exists():
            return {"status": "missing", "message": f"Falta el archivo requerido: {path.name}"}
        try:
            obj = joblib.load(path)
            return {"status": "ok", "message": f"Archivo cargado correctamente: {path.name}", "object_type": type(obj).__name__}
        except Exception as exc:
            logger.warning("No se pudo cargar %s: %s", path, exc)
            return {"status": "error", "message": f"No se pudo cargar {path.name}: {exc}"}

    def _load_json(self, path: Path) -> Dict[str, Any]:
        if not path.exists():
            return {"status": "missing", "message": f"Falta el archivo requerido: {path.name}"}
        data = read_json_file(path)
        if data is None:
            return {"status": "error", "message": f"No se pudo cargar {path.name}"}
        size = len(data) if hasattr(data, "__len__") else None
        return {"status": "ok", "message": f"Archivo cargado correctamente: {path.name}", "json_type": type(data).__name__, "items": size}

    def validate_required_artifacts(self) -> Dict[str, Dict[str, Any]]:
        return {
            "pipeline_modelo1.joblib": self._load_joblib(config.MODEL1_PATH),
            "pipeline_modelo2.joblib": self._load_joblib(config.MODEL2_PATH),
            "feature_names.json": self._load_json(config.FEATURE_NAMES_PATH),
            "metadata_modelo1.json": self._load_json(config.METADATA_MODEL1_PATH),
            "metadata_modelo2.json": self._load_json(config.METADATA_MODEL2_PATH),
        }

    def load_report_metrics(self, path: Path) -> Optional[Dict[str, Any]]:
        data = read_json_file(path)
        return data if isinstance(data, dict) else None