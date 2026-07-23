"""Helpers to normalize model metrics for UI consumption."""

from __future__ import annotations

from typing import Any, Dict


def build_binary_metrics_summary(metrics: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "balanced_accuracy": metrics.get("balanced_accuracy"),
        "f1": metrics.get("f1_macro"),
        "roc_auc": metrics.get("roc_auc"),
        "kappa": metrics.get("kappa"),
    }


def build_multiclass_metrics_summary(metrics: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "balanced_accuracy": metrics.get("balanced_accuracy"),
        "f1": metrics.get("f1_macro"),
        "roc_auc": metrics.get("roc_auc_ovr"),
        "kappa": metrics.get("kappa"),
    }