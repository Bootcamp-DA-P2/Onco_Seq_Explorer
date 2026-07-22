"""Canonical application configuration for OncoSeq Explorer."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List


@dataclass
class Config:
    """Central application configuration and filesystem paths."""

    BASE_DIR: Path = field(default_factory=lambda: Path(__file__).resolve().parent)
    ASSETS_DIR: Path = field(default_factory=lambda: Path(__file__).resolve().parent / "assets")
    DATA_DIR: Path = field(default_factory=lambda: Path(__file__).resolve().parent / "data")
    MODELS_DIR: Path = field(default_factory=lambda: Path(__file__).resolve().parent / "models")
    OUTPUTS_DIR: Path = field(default_factory=lambda: Path(__file__).resolve().parent / "outputs")
    REPORTS_DIR: Path = field(default_factory=lambda: Path(__file__).resolve().parent / "reports")
    LOGS_DIR: Path = field(default_factory=lambda: Path(__file__).resolve().parent / "logs")

    CSS_DIR: Path = field(default_factory=lambda: Path(__file__).resolve().parent / "assets" / "css")
    IMAGES_DIR: Path = field(default_factory=lambda: Path(__file__).resolve().parent / "assets" / "images")

    UPLOADS_DIR: Path = field(default_factory=lambda: Path(__file__).resolve().parent / "data" / "uploads")
    TEMPLATES_DIR: Path = field(default_factory=lambda: Path(__file__).resolve().parent / "data" / "templates")
    PROCESSED_DIR: Path = field(default_factory=lambda: Path(__file__).resolve().parent / "data" / "processed")
    RETRAINING_DIR: Path = field(default_factory=lambda: Path(__file__).resolve().parent / "data" / "retraining")

    MODEL1_PATH: Path = field(default_factory=lambda: Path(__file__).resolve().parent / "models" / "pipeline_modelo1.joblib")
    MODEL2_PATH: Path = field(default_factory=lambda: Path(__file__).resolve().parent / "models" / "pipeline_modelo2.joblib")
    FEATURE_NAMES_PATH: Path = field(default_factory=lambda: Path(__file__).resolve().parent / "models" / "feature_names.json")
    METADATA_MODEL1_PATH: Path = field(default_factory=lambda: Path(__file__).resolve().parent / "models" / "metadata_modelo1.json")
    METADATA_MODEL2_PATH: Path = field(default_factory=lambda: Path(__file__).resolve().parent / "models" / "metadata_modelo2.json")

    METRICS_MODEL1_PATH: Path = field(default_factory=lambda: Path(__file__).resolve().parent / "reports" / "final_metrics_modelo1.json")
    METRICS_MODEL2_PATH: Path = field(default_factory=lambda: Path(__file__).resolve().parent / "reports" / "final_metrics_modelo2.json")
    CONFUSION_MODEL1_PATH: Path = field(default_factory=lambda: Path(__file__).resolve().parent / "reports" / "matriz_confusion_modelo1.png")
    CONFUSION_MODEL2_PATH: Path = field(default_factory=lambda: Path(__file__).resolve().parent / "reports" / "matriz_confusion_modelo2.png")

    DB_PATH: Path = field(default_factory=lambda: Path(__file__).resolve().parent / "database" / "oncoseq.db")

    CANCER_TYPES: List[str] = field(default_factory=lambda: ["BRCA", "COAD", "KIRC", "LUAD", "PRAD"])
    BINARY_CLASSES: List[str] = field(default_factory=lambda: ["NORMAL", "TUMOR"])

    COLORS: Dict[str, str] = field(default_factory=lambda: {
        "primary": "#1068DA",
        "secondary": "#10CDDA",
        "accent": "#10DA82",
        "surface": "#FFFFFF",
        "background": "#F8FAFC",
        "text": "#0F172A",
        "muted": "#64748B",
        "border": "#E2E8F0",
        "sidebar": "#1E293B",
        "success": "#16A34A",
        "warning": "#F59E0B",
        "danger": "#DC2626",
    })

    PAGE_CONFIG: Dict[str, object] = field(default_factory=lambda: {
        "page_title": "Sistema de Soporte a la decisión clinica",
        "page_icon": "🧬",
        "layout": "wide",
        "initial_sidebar_state": "expanded",
    })

    PLOT_TEMPLATE: str = "plotly_white"
    PLOT_HEIGHT: int = 420

    def __post_init__(self) -> None:
        for directory in (
            self.ASSETS_DIR,
            self.CSS_DIR,
            self.IMAGES_DIR,
            self.DATA_DIR,
            self.UPLOADS_DIR,
            self.TEMPLATES_DIR,
            self.PROCESSED_DIR,
            self.RETRAINING_DIR,
            self.MODELS_DIR,
            self.OUTPUTS_DIR,
            self.REPORTS_DIR,
            self.LOGS_DIR,
            self.DB_PATH.parent,
        ):
            directory.mkdir(parents=True, exist_ok=True)


config = Config()