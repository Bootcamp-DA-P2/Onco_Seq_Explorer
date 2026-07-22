from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from streamlit_app.config import config
from services.loaders import ArtifactLoader
from streamlit_app.components.charts import style_figure
from streamlit_app.components.layout import render_page_header
from streamlit_app.components.tables import render_dataframe
from utils.helpers import read_csv_file, read_json_file


def _pick_metric(primary: dict, secondary: dict, keys: list[str], default: float = 0.0) -> float:
    for source in (primary, secondary):
        if not isinstance(source, dict):
            continue
        for key in keys:
            value = source.get(key)
            if value is None:
                continue
            try:
                return float(value)
            except (TypeError, ValueError):
                continue
    return float(default)


def _load_top_genes_model1() -> pd.DataFrame:
    data = read_json_file(config.TOP_GENES_MODEL1_JSON_PATH)
    if isinstance(data, dict):
        try:
            return pd.DataFrame(data)
        except Exception:
            pass

    csv_df = read_csv_file(config.TOP_GENES_MODEL1_CSV_PATH)
    return csv_df if csv_df is not None else pd.DataFrame()


def _load_top_genes_model2() -> pd.DataFrame:
    data = read_json_file(config.TOP_GENES_MODEL2_JSON_PATH)
    if isinstance(data, list):
        return pd.DataFrame(data)

    csv_df = read_csv_file(config.TOP_GENES_MODEL2_CSV_PATH)
    return csv_df if csv_df is not None else pd.DataFrame()


def _build_comparison_dataframe(metrics_1: dict, metrics_2: dict, metadata_1: dict, metadata_2: dict) -> pd.DataFrame:
    metadata_1 = metadata_1 if isinstance(metadata_1, dict) else {}
    metadata_2 = metadata_2 if isinstance(metadata_2, dict) else {}
    metrics_1 = metrics_1 if isinstance(metrics_1, dict) else {}
    metrics_2 = metrics_2 if isinstance(metrics_2, dict) else {}

    if not metrics_1:
        metrics_1 = metadata_1.get("metrics", {}) if isinstance(metadata_1.get("metrics"), dict) else {}
    if not metrics_2:
        metrics_2 = metadata_2.get("metrics", {}) if isinstance(metadata_2.get("metrics"), dict) else {}

    metadata_metrics_1 = metadata_1.get("metrics", {}) if isinstance(metadata_1.get("metrics"), dict) else {}
    metadata_metrics_2 = metadata_2.get("metrics", {}) if isinstance(metadata_2.get("metrics"), dict) else {}

    rows = [
        {
            "Modelo": "Modelo 1: Tumor vs Normal",
            "Problema": "Clasificacion binaria",
            "Balanced Accuracy": _pick_metric(metrics_1, metadata_metrics_1, ["balanced_accuracy", "balancedAccuracy"]),
            "F1 Macro": _pick_metric(metrics_1, metadata_metrics_1, ["f1_macro", "f1Macro", "f1"]),
            "ROC AUC": _pick_metric(metrics_1, metadata_metrics_1, ["roc_auc", "rocAuc", "auc"]),
            "Kappa": _pick_metric(metrics_1, metadata_metrics_1, ["kappa", "cohen_kappa"]),
            "CV F1 Macro": float(metadata_1.get("cv_f1_macro", 0.0)),
            "Genes seleccionados": int(metadata_1.get("selected_features", 0) or 0),
            "Algoritmo": str(metadata_1.get("algorithm", "N/D")),
        },
        {
            "Modelo": "Modelo 2: Subtipo tumoral",
            "Problema": "Clasificacion multiclase",
            "Balanced Accuracy": _pick_metric(metrics_2, metadata_metrics_2, ["balanced_accuracy", "balancedAccuracy"]),
            "F1 Macro": _pick_metric(metrics_2, metadata_metrics_2, ["f1_macro", "f1Macro", "f1_weighted", "f1"]),
            "ROC AUC": _pick_metric(metrics_2, metadata_metrics_2, ["roc_auc_ovr", "roc_auc", "rocAuc", "auc"]),
            "Kappa": _pick_metric(metrics_2, metadata_metrics_2, ["kappa", "cohen_kappa"]),
            "CV F1 Macro": float(metadata_2.get("cv_f1_macro", 0.0)),
            "Genes seleccionados": int(metadata_2.get("selected_features", 0) or 0),
            "Algoritmo": str(metadata_2.get("algorithm", "N/D")),
        },
    ]
    return pd.DataFrame(rows)


def _render_kpi_strip(comparison_df: pd.DataFrame) -> None:
    best_idx = comparison_df["F1 Macro"].idxmax()
    best_model = comparison_df.loc[best_idx, "Modelo"]
    best_f1 = comparison_df.loc[best_idx, "F1 Macro"]

    delta_f1 = abs(comparison_df.loc[0, "F1 Macro"] - comparison_df.loc[1, "F1 Macro"])
    delta_auc = abs(comparison_df.loc[0, "ROC AUC"] - comparison_df.loc[1, "ROC AUC"])
    total_features = int(comparison_df["Genes seleccionados"].sum())

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Mejor F1 Macro", f"{best_f1:.4f}", best_model)
    col2.metric("Brecha F1 entre modelos", f"{delta_f1:.4f}")
    col3.metric("Brecha ROC AUC", f"{delta_auc:.4f}")
    col4.metric("Genes usados (M1 + M2)", f"{total_features:,}")


def _render_metric_comparison_charts(comparison_df: pd.DataFrame) -> None:
    st.markdown("### Comparativa global de metricas")

    metric_columns = ["Balanced Accuracy", "F1 Macro", "ROC AUC", "Kappa", "CV F1 Macro"]
    chart_df = comparison_df[["Modelo"] + metric_columns].melt(
        id_vars="Modelo",
        var_name="Metrica",
        value_name="Valor",
    )

    fig = px.bar(
        chart_df,
        x="Metrica",
        y="Valor",
        color="Modelo",
        barmode="group",
        color_discrete_map={
            "Modelo 1: Tumor vs Normal": config.COLORS["primary"],
            "Modelo 2: Subtipo tumoral": config.COLORS["secondary"],
        },
    )
    fig = style_figure(fig, "Comparativa de rendimiento por metrica", "Valor")
    fig.update_yaxes(range=[0, 1.05])
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("### Tabla de comparacion")
    render_dataframe(comparison_df)


def _render_cv_panel(csv_path, section_title: str, metric_col: str, color: str) -> None:
    df_cv = read_csv_file(csv_path)
    st.markdown(f"#### {section_title}")

    if df_cv is None or df_cv.empty or metric_col not in df_cv.columns or "modelo" not in df_cv.columns:
        st.info(f"No hay datos disponibles en {csv_path.name} para esta comparacion.")
        return

    top_df = df_cv.sort_values(by=metric_col, ascending=False).head(7).copy()

    fig = px.bar(
        top_df.sort_values(by=metric_col, ascending=True),
        x=metric_col,
        y="modelo",
        orientation="h",
        color=metric_col,
        color_continuous_scale=["#DBEAFE", color],
    )
    fig = style_figure(fig, f"Top algoritmos por {metric_col}", metric_col)
    fig.update_layout(showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

    render_dataframe(top_df)


def _render_interpretability(top_genes_model1: pd.DataFrame, top_genes_model2: pd.DataFrame) -> None:
    left_col, right_col = st.columns(2)

    with left_col:
        st.markdown("### Modelo 1: genes con mayor peso")
        if top_genes_model1.empty:
            st.info("No hay archivo de top genes para modelo 1.")
        else:
            plot_df = top_genes_model1.copy().head(15)
            plot_df["magnitud"] = plot_df["coeficiente"].abs()
            fig_m1 = px.bar(
                plot_df.sort_values(by="magnitud", ascending=True),
                x="magnitud",
                y="gene",
                orientation="h",
                color="clase_asociada",
                color_discrete_map={"NORMAL": config.COLORS["secondary"], "TUMOR": config.COLORS["primary"]},
            )
            fig_m1 = style_figure(fig_m1, "Importancia local - Modelo 1", "|coeficiente|")
            st.plotly_chart(fig_m1, use_container_width=True)
            render_dataframe(top_genes_model1.head(20))

    with right_col:
        st.markdown("### Modelo 2: genes con mayor importancia")
        if top_genes_model2.empty:
            st.info("No hay archivo de top genes para modelo 2.")
        else:
            plot_df = top_genes_model2.copy().head(15)
            fig_m2 = px.bar(
                plot_df.sort_values(by="importancia_global", ascending=True),
                x="importancia_global",
                y="gene",
                orientation="h",
                color="clase_mas_asociada",
                color_discrete_sequence=[config.COLORS["primary"], config.COLORS["secondary"], config.COLORS["accent"], "#60A5FA", "#0F766E"],
            )
            fig_m2 = style_figure(fig_m2, "Importancia global - Modelo 2", "Importancia")
            st.plotly_chart(fig_m2, use_container_width=True)
            render_dataframe(top_genes_model2.head(20))


def render() -> None:
    render_page_header(
        "Modelos",
        "Comparativa estructurada de rendimiento, validacion cruzada e interpretabilidad usando artefactos del proyecto.",
    )

    loader = ArtifactLoader()
    metrics_1 = loader.load_report_metrics(config.METRICS_MODEL1_PATH) or {}
    metrics_2 = loader.load_report_metrics(config.METRICS_MODEL2_PATH) or {}
    metadata_1 = read_json_file(config.METADATA_MODEL1_PATH) or {}
    metadata_2 = read_json_file(config.METADATA_MODEL2_PATH) or {}

    comparison_df = _build_comparison_dataframe(metrics_1, metrics_2, metadata_1, metadata_2)
    _render_kpi_strip(comparison_df)

    overview_tab, cv_tab, interp_tab = st.tabs([
        "Resumen comparativo",
        "Benchmark CV",
        "Interpretabilidad",
    ])

    with overview_tab:
        _render_metric_comparison_charts(comparison_df)

    with cv_tab:
        col_a, col_b = st.columns(2)
        with col_a:
            _render_cv_panel(
                config.CV_MODEL1_PATH,
                "Modelo 1 - Tumor vs Normal",
                "f1_macro_mean",
                config.COLORS["primary"],
            )
        with col_b:
            _render_cv_panel(
                config.CV_MODEL2_PATH,
                "Modelo 2 - Subtipo tumoral",
                "f1_macro_mean",
                config.COLORS["secondary"],
            )

    with interp_tab:
        top_genes_model1 = _load_top_genes_model1()
        top_genes_model2 = _load_top_genes_model2()
        _render_interpretability(top_genes_model1, top_genes_model2)
