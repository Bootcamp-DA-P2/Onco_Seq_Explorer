"""Model artifact loader and validator (no prediction logic)."""
from pathlib import Path
import json
from typing import Dict, Any, Optional
import logging
import joblib

from src.config import config


logger = logging.getLogger(__name__)


class ModelManager:
    def __init__(self):
        self.models_dir: Path = config.MODELS_DIR
        self.required_files: Dict[str, Path] = {
            "pipeline_modelo1.joblib": self.models_dir / "pipeline_modelo1.joblib",
            "pipeline_modelo2.joblib": self.models_dir / "pipeline_modelo2.joblib",
            "feature_names.json": self.models_dir / "feature_names.json",
            "metadata_modelo1.json": self.models_dir / "metadata_modelo1.json",
            "metadata_modelo2.json": self.models_dir / "metadata_modelo2.json",
        }

    def _read_json(self, path: Path) -> Optional[Any]:
        if not path.exists():
            return None
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)

    def _safe_load_joblib(self, path: Path) -> Dict[str, Any]:
        if not path.exists():
            return {
                "status": "missing",
                "message": f"Falta el archivo requerido: {path.name}",
            }
        try:
            obj = joblib.load(path)
            return {
                "status": "ok",
                "message": f"Archivo cargado correctamente: {path.name}",
                "object_type": type(obj).__name__,
            }
        except Exception as e:
            logger.warning("Error loading joblib '%s': %s", path, e)
            return {
                "status": "error",
                "message": f"No se pudo cargar {path.name}: {e}",
            }

    def _safe_load_json(self, path: Path) -> Dict[str, Any]:
        if not path.exists():
            return {
                "status": "missing",
                "message": f"Falta el archivo requerido: {path.name}",
            }
        try:
            data = self._read_json(path)
            if data is None:
                return {
                    "status": "error",
                    "message": f"No se pudo leer {path.name}",
                }

            return {
                "status": "ok",
                "message": f"Archivo cargado correctamente: {path.name}",
                "json_type": type(data).__name__,
                "items": len(data) if hasattr(data, "__len__") else None,
            }
        except Exception as e:
            logger.warning("Error reading json '%s': %s", path, e)
            return {
                "status": "error",
                "message": f"No se pudo cargar {path.name}: {e}",
            }

    def validate_required_artifacts(self) -> Dict[str, Dict[str, Any]]:
        """Load and validate only required model artifacts for this phase."""
        result: Dict[str, Dict[str, Any]] = {}

        result["pipeline_modelo1.joblib"] = self._safe_load_joblib(
            self.required_files["pipeline_modelo1.joblib"]
        )
        result["pipeline_modelo2.joblib"] = self._safe_load_joblib(
            self.required_files["pipeline_modelo2.joblib"]
        )

        result["feature_names.json"] = self._safe_load_json(
            self.required_files["feature_names.json"]
        )
        result["metadata_modelo1.json"] = self._safe_load_json(
            self.required_files["metadata_modelo1.json"]
        )
        result["metadata_modelo2.json"] = self._safe_load_json(
            self.required_files["metadata_modelo2.json"]
        )

        return result
