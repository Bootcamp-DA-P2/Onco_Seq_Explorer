from __future__ import annotations

import json
import os
from time import perf_counter

import pandas as pd
import streamlit as st

from managers.feedback_manager import FeedbackManager
from services.retraining import RetrainingService
from streamlit_app.components.cards import render_kpi_card, render_status_card
from streamlit_app.components.layout import render_page_header
from database.cdss_database import CDSSDatabase


VALID_DIAGNOSES = ["NORMAL", "BRCA", "COAD", "KIRC", "LUAD", "PRAD"]


def _is_dev_mode() -> bool:
    secret_flag = bool(st.secrets.get("DEV_MODE", False))
    env_flag = os.getenv("ONCOSEQ_DEV_MODE", "0").strip().lower() in {"1", "true", "yes", "on"}
    return secret_flag or env_flag


def _render_perf_metrics(perf: dict[str, float]) -> None:
    if not perf:
        return
    with st.expander("Metricas de rendimiento (dev)"):
        rows = [{"Etapa": key, "Tiempo (ms)": round(float(value), 2)} for key, value in perf.items()]
        st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)


def _human_status(status: str) -> str:
    if status == "CONFIRMADO":
        return "Confirmado"
    return "Pendiente de validacion"


def _human_result(value: str | None) -> str:
    if value == "CORRECTO":
        return "✅ Correcto"
    if value == "INCORRECTO":
        return "❌ Incorrecto"
    return "-"


def _display_prediction(row: pd.Series) -> str:
    stage1 = str(row.get("stage1_prediction", "")).upper()
    stage2 = row.get("stage2_prediction")
    if stage2:
        return str(stage2).upper()
    if stage1 in {"1", "TUMOR"}:
        return "TUMOR"
    return "NORMAL"


def _prepare_table(dataframe: pd.DataFrame) -> pd.DataFrame:
    if dataframe.empty:
        return dataframe

    view = pd.DataFrame()
    view["ID del paciente"] = dataframe["patient_id"].fillna("N/D")
    view["Fecha del analisis"] = dataframe["timestamp"].fillna("")
    view["Prediccion IA"] = dataframe.apply(_display_prediction, axis=1)
    view["Diagnostico confirmado"] = dataframe["confirmed_diagnosis"].fillna("")
    view["Estado"] = dataframe["case_status"].fillna("PENDIENTE_VALIDACION").apply(_human_status)
    view["Resultado"] = dataframe["comparison_result"].apply(_human_result)
    view["Acciones"] = dataframe["case_status"].apply(lambda s: "Confirmar diagnostico" if s != "CONFIRMADO" else "Caso confirmado")
    view["prediction_id"] = dataframe["id"]
    return view


def _render_confirmation_forms(dataframe: pd.DataFrame) -> None:
    pending = dataframe[dataframe["case_status"] != "CONFIRMADO"]
    if pending.empty:
        st.info("No hay casos pendientes de validacion clinica.")
        return

    manager = FeedbackManager()

    for _, row in pending.iterrows():
        case_id = int(row["id"])
        patient_id = str(row.get("patient_id") or "N/D")
        predicted = _display_prediction(row)

        with st.expander(f"Confirmar diagnostico | Caso #{case_id} | Paciente: {patient_id}"):
            st.write(f"Prediccion IA registrada: **{predicted}**")
            diagnosis = st.selectbox(
                "Diagnostico definitivo",
                options=VALID_DIAGNOSES,
                key=f"diagnosis_{case_id}",
            )
            notes = st.text_area("Notas de validacion", key=f"notes_{case_id}")

            if st.button("Guardar validacion", key=f"save_validation_{case_id}", type="primary"):
                result = manager.submit_feedback(
                    prediction_id=case_id,
                    confirmed_diagnosis=diagnosis,
                    clinical_notes=notes,
                )
                if result.get("ok"):
                    readable = "✅ Correcto" if result.get("is_correct") else "❌ Incorrecto"
                    render_status_card(
                        "Validacion guardada",
                        f"Prediccion IA: {result.get('prediction')} | Diagnostico confirmado: {result.get('confirmed')} | Resultado: {readable}",
                        "ok",
                    )
                    st.rerun()
                else:
                    render_status_card("No se pudo guardar", "No se encontro el caso seleccionado.", "warning")


def _render_retraining_panel(database: CDSSDatabase) -> None:
    st.markdown("### Preparacion para reentrenamiento")
    eligible_cases = database.get_confirmed_retraining_cases()

    col_a, col_b = st.columns(2)
    with col_a:
        render_kpi_card("Casos aptos para reentrenamiento", str(len(eligible_cases)), "Confirmados y con muestra")
    with col_b:
        if st.button("Ejecutar reentrenamiento manual", type="secondary", width="stretch"):
            service = RetrainingService()
            result = service.run_manual_retraining()
            if result.get("ok"):
                render_status_card(
                    "Nueva version generada",
                    f"Version {result.get('version_id')} creada con {result.get('source_cases')} casos confirmados.",
                    "ok",
                )
            else:
                render_status_card("Reentrenamiento no ejecutado", result.get("message", "No fue posible ejecutar el proceso."), "warning")

    versions = database.get_model_versions(limit=10)
    if versions:
        rows = []
        for version in versions:
            metrics_json = version.get("metrics_json")
            metrics = {}
            if metrics_json:
                try:
                    metrics = json.loads(metrics_json)
                except Exception:
                    metrics = {}
            rows.append(
                {
                    "Version": version.get("version_id"),
                    "Fecha": version.get("created_at"),
                    "Casos": version.get("source_cases"),
                    "F1 Macro M1": (metrics.get("model1") or {}).get("f1_macro"),
                    "F1 Macro M2": (metrics.get("model2") or {}).get("f1_macro"),
                }
            )
        st.markdown("#### Historial de versiones")
        st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)


def render() -> None:
    render_page_header(
        "Historico",
        "Validacion clinica posterior de predicciones IA y preparacion de mejora continua.",
    )

    database = CDSSDatabase()
    perf: dict[str, float] = {}

    t0 = perf_counter()
    rows = database.get_predictions(limit=1000)
    perf["history_get_predictions_ms"] = (perf_counter() - t0) * 1000.0

    t0 = perf_counter()
    dataframe = pd.DataFrame(rows)
    perf["history_dataframe_build_ms"] = (perf_counter() - t0) * 1000.0

    if dataframe.empty:
        render_status_card("Sin casos", "Aun no hay casos analizados en el sistema.", "warning")
        return

    total = len(dataframe)
    confirmed = int((dataframe["case_status"] == "CONFIRMADO").sum())
    pending = max(total - confirmed, 0)

    kpi_cols = st.columns(3)
    with kpi_cols[0]:
        render_kpi_card("Casos analizados", str(total), "Predicciones IA registradas")
    with kpi_cols[1]:
        render_kpi_card("Pendientes de validacion", str(pending), "Revision clinica")
    with kpi_cols[2]:
        render_kpi_card("Confirmados", str(confirmed), "Con diagnostico definitivo")

    st.markdown("### Tabla principal")
    table_df = _prepare_table(dataframe)
    st.dataframe(
        table_df[[
            "ID del paciente",
            "Fecha del analisis",
            "Prediccion IA",
            "Diagnostico confirmado",
            "Estado",
            "Resultado",
            "Acciones",
        ]],
        width="stretch",
        hide_index=True,
    )

    st.markdown("### Validacion clinica")
    _render_confirmation_forms(dataframe)

    _render_retraining_panel(database)

    if _is_dev_mode():
        _render_perf_metrics(perf)
