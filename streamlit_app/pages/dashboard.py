from __future__ import annotations

import json
import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st
import streamlit.components.v1 as components
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

from streamlit_app.config import config
from streamlit_app.components.cards import render_kpi_card
from streamlit_app.components.charts import style_figure
from streamlit_app.components.layout import render_page_header
from utils.helpers import read_csv_file, read_parquet_shape


def _load_metadata() -> pd.DataFrame:
    metadata_df = read_csv_file(config.METADATA_CSV_PATH)
    if metadata_df is None:
        return pd.DataFrame()

    renamed = metadata_df.rename(columns={"index": "muestra_id"}).copy()
    renamed["tipo"] = renamed.get("tipo", pd.Series(dtype="object")).astype(str).str.upper()
    renamed["cohorte"] = renamed.get("cohorte", pd.Series(dtype="object")).astype(str).str.upper()
    return renamed


def _sidebar_filters(df: pd.DataFrame) -> tuple[pd.DataFrame, list[str], list[str]]:
    if df.empty:
        return df, [], []

    cohort_options = sorted([value for value in df["cohorte"].dropna().unique().tolist() if value])
    tipo_options = sorted([value for value in df["tipo"].dropna().unique().tolist() if value])

    with st.sidebar.expander("Filtros del dashboard", expanded=True):
        selected_cohorts = st.multiselect(
            "Cohortes",
            options=cohort_options,
            default=cohort_options,
        )
        selected_tipos = st.multiselect(
            "Tipo de muestra",
            options=tipo_options,
            default=tipo_options,
        )

    filtered = df.copy()
    if selected_cohorts:
        filtered = filtered[filtered["cohorte"].isin(selected_cohorts)]
    if selected_tipos:
        filtered = filtered[filtered["tipo"].isin(selected_tipos)]

    return filtered, selected_cohorts, selected_tipos


def _render_kpis(filtered_df: pd.DataFrame, full_df: pd.DataFrame, expression_shape: tuple[int, int] | None) -> None:
    total_samples = int(filtered_df.shape[0])
    total_participants = int(filtered_df["participante"].nunique()) if "participante" in filtered_df.columns else 0
    total_cohorts = int(filtered_df["cohorte"].nunique()) if "cohorte" in filtered_df.columns else 0
    total_genes = int(expression_shape[1]) if expression_shape is not None else 0

    base_total = int(full_df.shape[0]) if not full_df.empty else 0

    kpi_cols = st.columns(4)
    with kpi_cols[0]:
        render_kpi_card("Muestras filtradas", f"{total_samples:,}", f"de {base_total:,}")
    with kpi_cols[1]:
        render_kpi_card("Participantes", f"{total_participants:,}", "Unicos")
    with kpi_cols[2]:
        render_kpi_card("Cohortes activas", f"{total_cohorts}", "Subtipos disponibles")
    with kpi_cols[3]:
        render_kpi_card("Genes de expresion", f"{total_genes:,}" if total_genes else "N/D", "Matriz transcriptomica")


def _render_cohort_chart(filtered_df: pd.DataFrame) -> None:
    st.markdown("### Muestras por cohorte")

    if filtered_df.empty or "cohorte" not in filtered_df.columns:
        st.info("No hay datos suficientes para visualizar cohortes.")
        return

    cohort_counts = (
        filtered_df["cohorte"]
        .value_counts()
        .rename_axis("Cohorte")
        .reset_index(name="Muestras")
        .sort_values("Muestras", ascending=False)
    )

    fig_coh = px.bar(
        cohort_counts,
        x="Cohorte",
        y="Muestras",
        color="Cohorte",
        color_discrete_sequence=[
            config.COLORS["primary"],
            config.COLORS["secondary"],
            config.COLORS["accent"],
            "#60A5FA",
            "#0F766E",
        ],
        text="Muestras",
    )
    fig_coh = style_figure(fig_coh, "Carga por cohorte clinica", "Muestras")
    fig_coh.update_layout(showlegend=False)
    fig_coh.update_traces(textposition="outside")
    st.plotly_chart(fig_coh, use_container_width=True)


def _render_tumor_normal_bar(filtered_df: pd.DataFrame) -> None:
    st.markdown("### Muestras normales vs tumorales")

    if filtered_df.empty or "tipo" not in filtered_df.columns:
        st.info("No hay datos suficientes para visualizar tipo de muestra.")
        return

    tipo_counts = (
        filtered_df["tipo"]
        .value_counts()
        .rename_axis("Tipo")
        .reset_index(name="Muestras")
    )

    fig_tipo = px.bar(
        tipo_counts,
        x="Tipo",
        y="Muestras",
        color="Tipo",
        text="Muestras",
        color_discrete_map={"TUMOR": config.COLORS["primary"], "NORMAL": config.COLORS["secondary"]},
    )
    fig_tipo = style_figure(fig_tipo, "Balance de clases", "Muestras")
    fig_tipo.update_layout(showlegend=False)
    fig_tipo.update_traces(textposition="outside")
    st.plotly_chart(fig_tipo, use_container_width=True)


@st.cache_data(show_spinner=False)
def _compute_global_pca_projection() -> pd.DataFrame:
    metadata_df = _load_metadata()
    if metadata_df.empty or "muestra_id" not in metadata_df.columns:
        return pd.DataFrame()

    expression_df = pd.read_parquet(config.EXPRESSION_PARQUET_PATH)

    sample_ids = metadata_df["muestra_id"].astype(str)
    valid_ids = [sample_id for sample_id in sample_ids if sample_id in expression_df.index]
    if not valid_ids:
        return pd.DataFrame()

    meta_valid = metadata_df[metadata_df["muestra_id"].isin(valid_ids)].copy()
    matrix = expression_df.loc[valid_ids].astype(float)

    # Use high-variance genes to keep PCA responsive in Streamlit.
    gene_variance = matrix.var(axis=0).values
    top_gene_count = min(1500, matrix.shape[1])
    top_indices = np.argsort(gene_variance)[-top_gene_count:]
    matrix_reduced = matrix.iloc[:, top_indices]

    scaled = StandardScaler().fit_transform(matrix_reduced.values)
    pca_model = PCA(n_components=2, random_state=42, svd_solver="randomized")
    pca_values = pca_model.fit_transform(scaled)

    return pd.DataFrame(
        {
            "muestra_id": valid_ids,
            "PC1": pca_values[:, 0],
            "PC2": pca_values[:, 1],
        }
    ).merge(meta_valid[["muestra_id", "tipo", "cohorte"]], on="muestra_id", how="left")


def _render_global_pca_chart(filtered_df: pd.DataFrame) -> None:
    st.markdown("### PCA global (normales + tumorales)")

    pca_df = _compute_global_pca_projection()
    if pca_df.empty:
        st.info("No se pudo calcular PCA global.")
        return

    selected_ids = set(filtered_df["muestra_id"].astype(str).tolist()) if "muestra_id" in filtered_df.columns else set()
    filtered_pca = pca_df[pca_df["muestra_id"].isin(selected_ids)] if selected_ids else pca_df
    if filtered_pca.empty:
        st.info("No hay muestras para mostrar en PCA global con los filtros actuales.")
        return

    fig_pca = px.scatter(
        filtered_pca,
        x="PC1",
        y="PC2",
        color="tipo",
        hover_data={"muestra_id": False, "PC1": ":.3f", "PC2": ":.3f"},
        opacity=0.76,
        color_discrete_map={"TUMOR": config.COLORS["primary"], "NORMAL": config.COLORS["secondary"]},
    )
    fig_pca = style_figure(fig_pca, "Separacion transcriptomica global", "PC2")
    fig_pca.update_xaxes(title_text="PC1")
    st.plotly_chart(fig_pca, use_container_width=True)


def _render_tumor_pca_chart(selected_cohorts: list[str]) -> None:
    st.markdown("### PCA de muestras tumorales (sin normales)")

    pca_df = _compute_global_pca_projection()
    if pca_df.empty:
        st.info("No se pudo calcular PCA para muestras tumorales.")
        return

    tumor_only = pca_df[pca_df["tipo"] == "TUMOR"]
    filtered_pca = tumor_only[tumor_only["cohorte"].isin(selected_cohorts)] if selected_cohorts else tumor_only
    if filtered_pca.empty:
        st.info("No hay muestras tumorales para los filtros de cohorte seleccionados.")
        return

    fig_pca = px.scatter(
        filtered_pca,
        x="PC1",
        y="PC2",
        color="cohorte",
        hover_data={"muestra_id": False, "PC1": ":.3f", "PC2": ":.3f"},
        opacity=0.78,
        color_discrete_sequence=[
            config.COLORS["primary"],
            config.COLORS["secondary"],
            config.COLORS["accent"],
            "#60A5FA",
            "#0F766E",
        ],
    )
    fig_pca = style_figure(fig_pca, "Proyeccion PCA de subtipos tumorales", "PC2")
    fig_pca.update_xaxes(title_text="PC1")
    st.plotly_chart(fig_pca, use_container_width=True)

def _render_transcriptomic_html_preview() -> None:
    st.markdown("### Vista embebida: transcriptomic_space_explorer.html")

    html_path = config.PCA_HTML_PATH
    pca_csv_path = config.PCA_DATA_CSV_PATH

    if not html_path.exists():
        st.info("No se encontró transcriptomic_space_explorer.html en streamlit_app/pca.")
        return

    if not pca_csv_path.exists():
        st.warning("No se encontró pca_data.csv para la previsualización transcriptómica.")
        return

    # 1) Leer el HTML base y el CSV de PCA
    html_content = html_path.read_text(encoding="utf-8")
    pca_df = pd.read_csv(pca_csv_path)

    # 2) Convertir a JSON para inyectar datos sin fetch externo
    json_data = json.dumps(pca_df.to_dict(orient="records"))

    # 3) Inyectar datos en el head para que el HTML los consuma antes de su inicializacion
    injected_data_script = f"<script>window.__PCA_DATA__ = {json_data};</script>"
    if "<head>" in html_content:
        html_content = html_content.replace("<head>", "<head>\n" + injected_data_script, 1)
    else:
        html_content = injected_data_script + html_content

    # 4) Renderizar el HTML con datos incrustados
    components.html(html_content, height=760, scrolling=True)


def render() -> None:
    render_page_header(
        "Dashboard",
        "Vista ejecutiva del dataset oncologico con distribucion de cohortes y proyeccion PCA tumoral.",
    )

    metadata_df = _load_metadata()
    expression_shape = read_parquet_shape(config.EXPRESSION_PARQUET_PATH)

    if metadata_df.empty:
        st.warning("No se pudo cargar oncoseq_metadatos.csv. Revisa la ruta de datos en configuración.")
        return

    filtered_df, selected_cohorts, selected_tipos = _sidebar_filters(metadata_df)

    if not selected_cohorts or not selected_tipos:
        st.warning("Selecciona al menos una cohorte y un tipo de muestra para continuar.")
        return

    _render_kpis(filtered_df, metadata_df, expression_shape)
    st.markdown("---")

    top_row_col_1, top_row_col_2 = st.columns(2)
    with top_row_col_1:
        _render_tumor_normal_bar(filtered_df)
    with top_row_col_2:
        _render_cohort_chart(filtered_df)

    st.markdown("---")
    bottom_row_col_1, bottom_row_col_2 = st.columns(2)
    with bottom_row_col_1:
        _render_global_pca_chart(filtered_df)
    with bottom_row_col_2:
        _render_tumor_pca_chart(selected_cohorts)

    with st.expander("Previsualizar espacio transcriptomico HTML", expanded=True):
        _render_transcriptomic_html_preview()
