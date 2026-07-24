"""Canonical application configuration for OncoLens."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List


def _first_existing_dir(candidates: Iterable[Path]) -> Path:
    candidate_list = [path for path in candidates if path is not None]
    for path in candidate_list:
        if path.exists() and path.is_dir():
            return path
    return candidate_list[0]


def _first_existing_file(candidates: Iterable[Path]) -> Path:
    candidate_list = [path for path in candidates if path is not None]
    for path in candidate_list:
        if path.exists() and path.is_file():
            return path
    return candidate_list[0]


@dataclass
class Config:
    """Central application configuration and filesystem paths."""

    APP_DIR: Path = field(default_factory=lambda: Path(__file__).resolve().parent)
    PROJECT_ROOT: Path = field(default_factory=lambda: Path(__file__).resolve().parent.parent)

    BASE_DIR: Path = field(default_factory=lambda: Path(__file__).resolve().parent.parent)
    ASSETS_DIR: Path = field(default_factory=lambda: Path(__file__).resolve().parent.parent / "assets")
    DATA_DIR: Path = field(default_factory=lambda: Path(__file__).resolve().parent.parent / "data")
    RAW_DATA_DIR: Path = field(default_factory=lambda: Path(__file__).resolve().parent.parent / "data" / "raw")
    MODELS_DIR: Path = field(default_factory=lambda: Path(__file__).resolve().parent.parent / "models")
    OUTPUTS_DIR: Path = field(default_factory=lambda: Path(__file__).resolve().parent.parent / "outputs")
    REPORTS_DIR: Path = field(default_factory=lambda: Path(__file__).resolve().parent.parent / "reports")
    METRICS_DIR: Path = field(default_factory=lambda: Path(__file__).resolve().parent.parent / "reports" / "metrics")
    INTERPRETABILITY_DIR: Path = field(default_factory=lambda: Path(__file__).resolve().parent.parent / "reports" / "interpretability")
    PCA_DIR: Path = field(default_factory=lambda: Path(__file__).resolve().parent / "pca")
    LOGS_DIR: Path = field(default_factory=lambda: Path(__file__).resolve().parent.parent / "logs")

    CSS_DIR: Path = field(default_factory=lambda: Path(__file__).resolve().parent.parent / "assets" / "css")
    IMAGES_DIR: Path = field(default_factory=lambda: Path(__file__).resolve().parent.parent / "assets" / "images")

    UPLOADS_DIR: Path = field(default_factory=lambda: Path(__file__).resolve().parent.parent / "data" / "uploads")
    TEMPLATES_DIR: Path = field(default_factory=lambda: Path(__file__).resolve().parent.parent / "data" / "templates")
    PROCESSED_DIR: Path = field(default_factory=lambda: Path(__file__).resolve().parent.parent / "data" / "processed")
    RETRAINING_DIR: Path = field(default_factory=lambda: Path(__file__).resolve().parent.parent / "data" / "retraining")

    MODEL1_PATH: Path = field(default_factory=lambda: Path(__file__).resolve().parent.parent / "models" / "pipeline_modelo1.joblib")
    MODEL2_PATH: Path = field(default_factory=lambda: Path(__file__).resolve().parent.parent / "models" / "pipeline_modelo2.joblib")
    FEATURE_NAMES_PATH: Path = field(default_factory=lambda: Path(__file__).resolve().parent.parent / "models" / "feature_names.json")
    METADATA_MODEL1_PATH: Path = field(default_factory=lambda: Path(__file__).resolve().parent.parent / "models" / "metadata_modelo1.json")
    METADATA_MODEL2_PATH: Path = field(default_factory=lambda: Path(__file__).resolve().parent.parent / "models" / "metadata_modelo2.json")

    METRICS_MODEL1_PATH: Path = field(default_factory=lambda: Path(__file__).resolve().parent.parent / "reports" / "final_metrics_modelo1.json")
    METRICS_MODEL2_PATH: Path = field(default_factory=lambda: Path(__file__).resolve().parent.parent / "reports" / "final_metrics_modelo2.json")
    CONFUSION_MODEL1_PATH: Path = field(default_factory=lambda: Path(__file__).resolve().parent.parent / "reports" / "matriz_confusion_modelo1.png")
    CONFUSION_MODEL2_PATH: Path = field(default_factory=lambda: Path(__file__).resolve().parent.parent / "reports" / "matriz_confusion_modelo2.png")

    TOP_GENES_MODEL1_JSON_PATH: Path = field(default_factory=lambda: Path(__file__).resolve().parent.parent / "outputs" / "top_genes_modelo1.json")
    TOP_GENES_MODEL2_JSON_PATH: Path = field(default_factory=lambda: Path(__file__).resolve().parent.parent / "outputs" / "top_genes_modelo2.json")
    TOP_GENES_MODEL1_CSV_PATH: Path = field(default_factory=lambda: Path(__file__).resolve().parent.parent / "reports" / "interpretability" / "top_genes_modelo1.csv")
    TOP_GENES_MODEL2_CSV_PATH: Path = field(default_factory=lambda: Path(__file__).resolve().parent.parent / "reports" / "interpretability" / "top_genes_modelo2.csv")
    CV_MODEL1_PATH: Path = field(default_factory=lambda: Path(__file__).resolve().parent.parent / "reports" / "metrics" / "results_modelo_1_cv.csv")
    CV_MODEL2_PATH: Path = field(default_factory=lambda: Path(__file__).resolve().parent.parent / "reports" / "metrics" / "results_modelo_2_cv.csv")

    METADATA_CSV_PATH: Path = field(default_factory=lambda: Path(__file__).resolve().parent.parent / "data" / "raw" / "oncoseq_metadatos.csv")
    EXPRESSION_PARQUET_PATH: Path = field(default_factory=lambda: Path(__file__).resolve().parent.parent / "data" / "raw" / "oncoseq_expresion.parquet")
    PCA_HTML_PATH: Path = field(default_factory=lambda: Path(__file__).resolve().parent / "pca" / "transcriptomic_space_explorer.html")
    PCA_DATA_CSV_PATH: Path = field(default_factory=lambda: Path(__file__).resolve().parent / "pca" / "pca_data.csv")

    DB_PATH: Path = field(default_factory=lambda: Path(__file__).resolve().parent.parent / "database" / "oncoseq.db")

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
        env_models_dir = os.getenv("ONCOSEQ_MODELS_DIR")

        self.BASE_DIR = self.PROJECT_ROOT
        self.ASSETS_DIR = _first_existing_dir([self.PROJECT_ROOT / "assets", self.APP_DIR / "assets"])
        self.DATA_DIR = _first_existing_dir([self.PROJECT_ROOT / "data", self.APP_DIR / "data"])
        self.RAW_DATA_DIR = _first_existing_dir([self.DATA_DIR / "raw", self.DATA_DIR])
        self.REPORTS_DIR = _first_existing_dir([self.PROJECT_ROOT / "reports", self.APP_DIR / "reports"])
        self.METRICS_DIR = _first_existing_dir([self.REPORTS_DIR / "metrics", self.PROJECT_ROOT / "outputs"])
        self.INTERPRETABILITY_DIR = _first_existing_dir([self.REPORTS_DIR / "interpretability", self.PROJECT_ROOT / "outputs"])
        self.PCA_DIR = _first_existing_dir([self.APP_DIR / "pca", self.REPORTS_DIR / "pca", self.DATA_DIR])

        models_candidates = [
            Path(env_models_dir) if env_models_dir else None,
            self.PROJECT_ROOT / "models",
            Path.home() / "Downloads" / "oncoseq_explorer_outputs (1)" / "models",
            Path.home() / "Downloads" / "oncoseq_explorer_outputs" / "models",
        ]
        self.MODELS_DIR = _first_existing_dir(models_candidates)

        self.OUTPUTS_DIR = _first_existing_dir([
            self.PROJECT_ROOT / "outputs",
            self.REPORTS_DIR / "metrics",
        ])

        self.LOGS_DIR = self.PROJECT_ROOT / "logs"
        self.CSS_DIR = self.ASSETS_DIR / "css"
        self.IMAGES_DIR = self.ASSETS_DIR / "images"
        self.UPLOADS_DIR = self.DATA_DIR / "uploads"
        self.TEMPLATES_DIR = self.DATA_DIR / "templates"
        self.PROCESSED_DIR = self.DATA_DIR / "processed"
        self.RETRAINING_DIR = self.DATA_DIR / "retraining"

        self.MODEL1_PATH = _first_existing_file([self.MODELS_DIR / "pipeline_modelo1.joblib"])
        self.MODEL2_PATH = _first_existing_file([self.MODELS_DIR / "pipeline_modelo2.joblib"])
        self.FEATURE_NAMES_PATH = _first_existing_file([self.MODELS_DIR / "feature_names.json"])
        self.METADATA_MODEL1_PATH = _first_existing_file([self.MODELS_DIR / "metadata_modelo1.json"])
        self.METADATA_MODEL2_PATH = _first_existing_file([self.MODELS_DIR / "metadata_modelo2.json"])

        self.METRICS_MODEL1_PATH = _first_existing_file([
            self.REPORTS_DIR / "final_metrics_modelo1.json",
            self.METRICS_DIR / "final_metrics_modelo1.json",
        ])
        self.METRICS_MODEL2_PATH = _first_existing_file([
            self.REPORTS_DIR / "final_metrics_modelo2.json",
            self.METRICS_DIR / "final_metrics_modelo2.json",
        ])
        self.CONFUSION_MODEL1_PATH = _first_existing_file([
            self.REPORTS_DIR / "matriz_confusion_modelo1.png",
            self.METRICS_DIR / "matriz_confusion_modelo1.png",
        ])
        self.CONFUSION_MODEL2_PATH = _first_existing_file([
            self.REPORTS_DIR / "matriz_confusion_modelo2.png",
            self.METRICS_DIR / "matriz_confusion_modelo2.png",
        ])

        self.TOP_GENES_MODEL1_JSON_PATH = _first_existing_file([
            self.PROJECT_ROOT / "outputs" / "top_genes_modelo1.json",
            self.OUTPUTS_DIR / "top_genes_modelo1.json",
        ])
        self.TOP_GENES_MODEL2_JSON_PATH = _first_existing_file([
            self.PROJECT_ROOT / "outputs" / "top_genes_modelo2.json",
            self.OUTPUTS_DIR / "top_genes_modelo2.json",
        ])
        self.TOP_GENES_MODEL1_CSV_PATH = _first_existing_file([
            self.INTERPRETABILITY_DIR / "top_genes_modelo1.csv",
            self.REPORTS_DIR / "interpretability" / "top_genes_modelo1.csv",
        ])
        self.TOP_GENES_MODEL2_CSV_PATH = _first_existing_file([
            self.INTERPRETABILITY_DIR / "top_genes_modelo2.csv",
            self.REPORTS_DIR / "interpretability" / "top_genes_modelo2.csv",
        ])
        self.CV_MODEL1_PATH = _first_existing_file([
            self.METRICS_DIR / "results_modelo_1_cv.csv",
            self.OUTPUTS_DIR / "results_modelo_1_cv.csv",
        ])
        self.CV_MODEL2_PATH = _first_existing_file([
            self.METRICS_DIR / "results_modelo_2_cv.csv",
            self.OUTPUTS_DIR / "results_modelo_2_cv.csv",
        ])

        self.METADATA_CSV_PATH = _first_existing_file([
            self.RAW_DATA_DIR / "oncoseq_metadatos.csv",
            self.DATA_DIR / "oncoseq_metadatos.csv",
        ])
        self.EXPRESSION_PARQUET_PATH = _first_existing_file([
            self.RAW_DATA_DIR / "oncoseq_expresion.parquet",
            self.DATA_DIR / "oncoseq_expresion.parquet",
        ])
        self.PCA_HTML_PATH = _first_existing_file([
            self.PCA_DIR / "transcriptomic_space_explorer.html",
            self.APP_DIR / "static" / "transcriptomic_space_explorer.html",
        ])
        self.PCA_DATA_CSV_PATH = _first_existing_file([
            self.PCA_DIR / "pca_data.csv",
            self.REPORTS_DIR / "pca" / "pca_data.csv",
            self.DATA_DIR / "pca_data.csv",
        ])

        self.DB_PATH = _first_existing_file([
            self.PROJECT_ROOT / "database" / "oncoseq.db",
            self.DATA_DIR / "predictions.db",
            self.APP_DIR / "database" / "oncoseq.db",
        ])

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
            self.METRICS_DIR,
            self.INTERPRETABILITY_DIR,
            self.PCA_DIR,
            self.LOGS_DIR,
            self.DB_PATH.parent,
        ):
            directory.mkdir(parents=True, exist_ok=True)


config = Config()