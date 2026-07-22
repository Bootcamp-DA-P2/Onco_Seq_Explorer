"""Backward-compatible exports for legacy imports."""

from components.cards import render_kpi_card, render_status_card
from components.layout import apply_theme as apply_cdss_theme
from components.tables import render_dataframe as render_prediction_dataframe


def render_info_box(title: str, text: str, kind: str = "ok") -> None:
    render_status_card(title, text, kind)


def render_model_info(info: dict) -> None:
    import streamlit as st

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Algoritmo", str(info.get("algorithm", "N/D")))
    c2.metric("N features", str(info.get("n_features", "N/D")))
    c3.metric("Accuracy", f"{float(info.get('accuracy', 0)):.4f}" if info.get("accuracy") is not None else "N/D")
    c4.metric("ROC-AUC", f"{float(info.get('roc_auc', 0)):.4f}" if info.get("roc_auc") is not None else "N/D")
