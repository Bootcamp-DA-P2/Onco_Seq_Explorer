from __future__ import annotations

from io import BytesIO
from typing import Any, Dict, Tuple

import pandas as pd
import plotly.express as px
import streamlit as st

from managers.prediction_manager import PredictionManager
from services.report_generator import ClinicalReport, ReportGeneratorService
from streamlit_app.components.cards import render_kpi_card, render_status_card
from streamlit_app.components.layout import render_page_header
from streamlit_app.config import config
from streamlit_app.database.cdss_database import CDSSDatabase
from utils.helpers import read_json_file


def _calculate_bmi(weight_kg: float, height_cm: float) -> tuple[float | None, str]:
    if height_cm <= 0 or weight_kg <= 0:
        return None, "No disponible"
    bmi = weight_kg / ((height_cm / 100.0) ** 2)
    if bmi < 18.5:
        classification = "Bajo peso"
    elif bmi < 25:
        classification = "Normopeso"
    elif bmi < 30:
        classification = "Sobrepeso"
    else:
        classification = "Obesidad"
    return round(bmi, 2), classification


def _normalize_gene_name(value: Any) -> str:
    return str(value).strip()


def _build_excel_template(feature_names: list[str]) -> bytes:
    instructions = pd.DataFrame(
        {
            "Instrucciones": [
                "1) Rellena la hoja Muestra en formato vertical: columnas gene y expression.",
                "2) No modifiques los nombres de columnas ni borres genes de la plantilla.",
                "3) Completa la columna expression con valores numericos.",
                "4) Si dejas celdas vacias, se imputaran como 0.0 para mantener compatibilidad.",
                "5) Guarda el archivo en formato .xlsx antes de subirlo.",
            ]
        }
    )
    sample_df = pd.DataFrame(
        {
            "gene": feature_names,
            "expression": ["" for _ in feature_names],
        }
    )

    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        instructions.to_excel(writer, index=False, sheet_name="Instrucciones")
        sample_df.to_excel(writer, index=False, sheet_name="Muestra")
    buffer.seek(0)
    return buffer.getvalue()


def _validate_uploaded_sample(uploaded_file, feature_names: list[str]) -> Tuple[pd.DataFrame | None, Dict[str, Any]]:
    summary = {
        "genes_found": 0,
        "missing_count": 0,
        "extra_count": 0,
        "missing_genes": [],
        "extra_genes": [],
        "non_numeric_count": 0,
        "null_count": 0,
        "status": "INVALIDA",
        "message": "No se ha podido validar la muestra.",
    }

    try:
        df = pd.read_excel(uploaded_file, sheet_name="Muestra")
    except Exception:
        summary["message"] = "No se pudo leer la hoja Muestra del archivo Excel."
        return None, summary

    if df.empty:
        summary["message"] = "La hoja Muestra no contiene filas de datos."
        return None, summary

    df.columns = [_normalize_gene_name(col) for col in df.columns]
    feature_names = [_normalize_gene_name(gene) for gene in feature_names]

    # Support both formats:
    # - vertical template: columns [gene, expression]
    # - horizontal legacy: genes as columns in first row
    sample_row: pd.DataFrame
    if {"gene", "expression"}.issubset(set(c.lower() for c in df.columns)):
        cols = {c.lower(): c for c in df.columns}
        gene_col = cols["gene"]
        expression_col = cols["expression"]

        long_df = df[[gene_col, expression_col]].copy()
        long_df[gene_col] = long_df[gene_col].astype(str).str.strip()
        long_df = long_df[long_df[gene_col] != ""]

        if long_df.empty:
            summary["message"] = "La hoja Muestra no contiene genes en la columna gene."
            return None, summary

        long_df = long_df.drop_duplicates(subset=[gene_col], keep="first")
        sample_map = dict(zip(long_df[gene_col], long_df[expression_col]))
        sample_row = pd.DataFrame([sample_map])
    else:
        sample_row = df.iloc[[0]].copy()

    sample_row.columns = [_normalize_gene_name(col) for col in sample_row.columns]
    found = list(sample_row.columns)
    missing = [gene for gene in feature_names if gene not in found]
    extra = [gene for gene in found if gene not in feature_names]

    summary["genes_found"] = len(found)
    summary["missing_count"] = len(missing)
    summary["extra_count"] = len(extra)
    summary["missing_genes"] = missing[:20]
    summary["extra_genes"] = extra[:20]

    for gene in missing:
        sample_row[gene] = 0.0

    ordered = sample_row[[gene for gene in feature_names if gene in sample_row.columns]]
    if ordered.shape[1] != len(feature_names):
        summary["message"] = "No fue posible reordenar completamente la muestra."
        return None, summary

    numeric = ordered.apply(pd.to_numeric, errors="coerce")
    summary["non_numeric_count"] = int((numeric.isna() & ~ordered.isna()).sum().sum())
    summary["null_count"] = int(numeric.isna().sum().sum())

    numeric = numeric.fillna(0.0)

    is_valid = (
        summary["missing_count"] == 0
        and summary["extra_count"] == 0
        and summary["non_numeric_count"] == 0
        and summary["null_count"] == 0
    )

    summary["status"] = "VALIDA" if is_valid else "VALIDA_CON_AJUSTES"
    summary["message"] = (
        "Muestra valida y lista para analisis."
        if is_valid
        else "Muestra validada con ajustes automaticos. Revisa el resumen antes de analizar."
    )
    return numeric, summary


def _build_patient_payload(
    patient_id: str,
    first_name: str,
    last_name: str,
    age: int,
    sex: str,
    nationality: str,
    weight_kg: float,
    height_cm: float,
    bmi: float | None,
    bmi_classification: str,
    smoker_status: str,
    clinical_notes: str,
) -> Dict[str, Any]:
    return {
        "patient_id": patient_id.strip(),
        "first_name": first_name.strip(),
        "last_name": last_name.strip(),
        "age": int(age),
        "sex": sex,
        "nationality": nationality.strip(),
        "weight_kg": float(weight_kg) if weight_kg > 0 else None,
        "height_cm": float(height_cm) if height_cm > 0 else None,
        "bmi": float(bmi) if bmi is not None else None,
        "bmi_classification": bmi_classification,
        "smoker_status": smoker_status,
        "cohort": None,
        "clinical_notes": clinical_notes.strip(),
    }


def _render_report_results(report: ClinicalReport, prediction_payload: Dict[str, Any]) -> None:
    st.markdown("### Paso 4. Resultado del modelo")
    col_a, col_b, col_c = st.columns(3)

    model1_label = str(prediction_payload.get("stage1_prediction", "")).upper()
    model1_normal_tumoral = "Tumoral" if prediction_payload.get("is_tumor") else "Normal"
    model1_probability = float(prediction_payload.get("stage1_probability", 0.0))

    col_a.metric("Clase predicha (Modelo 1)", model1_label or "N/D")
    col_b.metric("Normal / Tumoral", model1_normal_tumoral)
    col_c.metric("Probabilidad Modelo 1", f"{model1_probability:.4f}")

    if prediction_payload.get("is_tumor"):
        st.markdown("#### Resultado Modelo 2")
        probs_map = prediction_payload.get("model2_probabilities", {}) or {}
        st.write(f"Tipo de cancer estimado: **{prediction_payload.get('stage2_prediction', 'N/D')}**")
        st.write(f"Probabilidad: **{float(prediction_payload.get('stage2_probability') or 0.0):.4f}**")

        if probs_map:
            probs_df = pd.DataFrame(
                [{"Clase": k, "Probabilidad": v} for k, v in probs_map.items()]
            ).sort_values(by="Probabilidad", ascending=False)
            st.dataframe(probs_df, use_container_width=True, hide_index=True)

            fig = px.bar(
                probs_df.sort_values(by="Probabilidad", ascending=True),
                x="Probabilidad",
                y="Clase",
                orientation="h",
                color="Probabilidad",
                color_continuous_scale=["#DBEAFE", "#1068DA"],
            )
            fig.update_layout(title="Distribucion de probabilidades - Modelo 2", showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Modelo 2 no se ejecuta para muestras clasificadas como Normal en Modelo 1.")

    st.markdown("### Paso 5. Informe de resultados")
    report_service = ReportGeneratorService()
    html = report_service.render_html_report(report)
    st.markdown(html, unsafe_allow_html=True)

    pdf_bytes = report_service.build_pdf_from_report(report)
    if pdf_bytes is not None:
        st.download_button(
            label="Descargar informe PDF",
            data=pdf_bytes,
            file_name=f"informe_resultados_{report.patient.get('patient_id', 'paciente')}.pdf",
            mime="application/pdf",
        )


def render() -> None:
    render_page_header(
        "Nuevo Paciente",
        "Asistente guiado para validacion de muestra RNA-Seq y prediccion IA (no diagnostico confirmado).",
    )

    db = CDSSDatabase()
    prediction_manager = PredictionManager()

    feature_names = read_json_file(config.FEATURE_NAMES_PATH)
    if not isinstance(feature_names, list) or not feature_names:
        render_status_card("Configuracion incompleta", "No se encontro feature_names.json valido.", "error")
        return

    if "new_patient_validated_df" not in st.session_state:
        st.session_state.new_patient_validated_df = None
    if "new_patient_validation_summary" not in st.session_state:
        st.session_state.new_patient_validation_summary = {}
    if "new_patient_prediction" not in st.session_state:
        st.session_state.new_patient_prediction = None
    if "new_patient_report" not in st.session_state:
        st.session_state.new_patient_report = None

    st.markdown("### Paso 1. Informacion clinica")
    p1, p2, p3 = st.columns(3)
    patient_id = p1.text_input("ID del paciente")
    first_name = p2.text_input("Nombre (opcional)")
    last_name = p3.text_input("Apellidos (opcional)")

    p4, p5, p6 = st.columns(3)
    age = p4.number_input("Edad", min_value=0, max_value=120, value=50)
    sex = p5.selectbox("Sexo", ["F", "M", "Otro"])
    nationality = p6.text_input("Nacionalidad")

    p7, p8, p9, p10 = st.columns(4)
    weight_kg = p7.number_input("Peso (kg)", min_value=0.0, max_value=400.0, value=0.0, step=0.1)
    height_cm = p8.number_input("Altura (cm)", min_value=0.0, max_value=250.0, value=0.0, step=0.1)
    bmi_value, bmi_classification = _calculate_bmi(float(weight_kg), float(height_cm))
    p9.text_input("IMC", value=f"{bmi_value:.2f}" if bmi_value is not None else "No disponible", disabled=True)
    p10.text_input("Clasificacion IMC", value=bmi_classification, disabled=True)

    smoker_status = st.selectbox("Estado de fumador", ["No fumador", "Fumador", "Exfumador"], index=0)
    clinical_notes = st.text_area("Observaciones clinicas")

    st.markdown("### Paso 2. Plantilla y carga de muestra RNA-Seq")
    col_template, col_upload = st.columns(2)

    with col_template:
        st.markdown("#### Descargar plantilla Excel")
        template_xlsx = _build_excel_template(feature_names)
        st.download_button(
            label="Descargar plantilla Excel",
            data=template_xlsx,
            file_name="plantilla_rnaseq.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

    with col_upload:
        st.markdown("#### Subir muestra RNA-Seq")
        upload = st.file_uploader("Subir plantilla completada", type=["xlsx"])
        if upload is not None:
            validated_df, validation_summary = _validate_uploaded_sample(upload, feature_names)
            st.session_state.new_patient_validated_df = validated_df
            st.session_state.new_patient_validation_summary = validation_summary

            v1, v2, v3 = st.columns(3)
            v1.metric("Genes encontrados", str(validation_summary.get("genes_found", 0)))
            v2.metric("Genes faltantes", str(validation_summary.get("missing_count", 0)))
            v3.metric("Genes adicionales", str(validation_summary.get("extra_count", 0)))

            v4, v5 = st.columns(2)
            v4.metric("Valores no numericos", str(validation_summary.get("non_numeric_count", 0)))
            v5.metric("Valores nulos", str(validation_summary.get("null_count", 0)))

            status_kind = "ok" if validation_summary.get("status") == "VALIDA" else "warning"
            render_status_card("Estado de validacion", validation_summary.get("message", ""), status_kind)

            missing_genes = validation_summary.get("missing_genes", [])
            extra_genes = validation_summary.get("extra_genes", [])
            if missing_genes:
                st.caption("Genes faltantes (muestra): " + ", ".join(missing_genes))
            if extra_genes:
                st.caption("Genes adicionales (muestra): " + ", ".join(extra_genes))

    st.markdown("### Paso 3. Ejecutar analisis")
    analyze_clicked = st.button("Analizar muestra", type="primary", use_container_width=True)

    if analyze_clicked:
        if not patient_id.strip():
            render_status_card("Dato requerido", "Debes indicar el ID del paciente.", "warning")
            return

        validated_df = st.session_state.new_patient_validated_df
        validation_summary = st.session_state.new_patient_validation_summary or {}

        if validated_df is None or validated_df.empty:
            render_status_card("Muestra no valida", "Primero debes cargar y validar una muestra RNA-Seq.", "warning")
            return

        patient_payload = _build_patient_payload(
            patient_id=patient_id,
            first_name=first_name,
            last_name=last_name,
            age=int(age),
            sex=sex,
            nationality=nationality,
            weight_kg=float(weight_kg),
            height_cm=float(height_cm),
            bmi=bmi_value,
            bmi_classification=bmi_classification,
            smoker_status=smoker_status,
            clinical_notes=clinical_notes,
        )
        db.save_or_update_patient(patient_payload)

        progress = st.progress(0, text="Validando muestra")
        progress.progress(25, text="Ejecutando Modelo 1")

        prediction_payload = prediction_manager.run_prediction(
            sample_df=validated_df,
            sample_name=f"sample_{patient_id.strip()}",
            user_notes=clinical_notes,
            patient_context=patient_payload,
            validation_summary=validation_summary,
        )

        progress.progress(60, text="Ejecutando Modelo 2")
        progress.progress(85, text="Generando informe de resultados")

        model1_result = {
            "predicted_label": str(prediction_payload.get("stage1_prediction", "")).upper(),
            "normal_tumoral": "Tumoral" if prediction_payload.get("is_tumor") else "Normal",
            "probability": f"{float(prediction_payload.get('stage1_probability', 0.0)):.4f}",
        }
        model2_result = {
            "predicted_cancer": prediction_payload.get("stage2_prediction") or "No aplica",
            "probability": (
                f"{float(prediction_payload.get('stage2_probability') or 0.0):.4f}"
                if prediction_payload.get("is_tumor")
                else "No aplica"
            ),
        }

        report_service = ReportGeneratorService()
        report = report_service.create_clinical_report(
            patient={
                "patient_id": patient_payload["patient_id"],
                "first_name": patient_payload["first_name"],
                "last_name": patient_payload["last_name"],
                "age": patient_payload["age"],
                "sex": patient_payload["sex"],
                "nationality": patient_payload["nationality"],
            },
            clinical_info={
                "weight_kg": patient_payload["weight_kg"],
                "height_cm": patient_payload["height_cm"],
                "bmi": patient_payload["bmi"],
                "bmi_classification": patient_payload["bmi_classification"],
                "smoker_status": patient_payload["smoker_status"],
            },
            sample_validation=validation_summary,
            model1_result=model1_result,
            model2_result=model2_result,
            probabilities=prediction_payload.get("model2_probabilities", {}),
            observations=clinical_notes,
        )

        st.session_state.new_patient_prediction = prediction_payload
        st.session_state.new_patient_report = report
        progress.progress(100, text="Analisis completado")
        render_status_card(
            "Analisis completado",
            "La prediccion IA ha sido registrada como Pendiente de validacion clinica en Historico.",
            "ok",
        )

    if st.session_state.new_patient_prediction and st.session_state.new_patient_report:
        _render_report_results(
            report=st.session_state.new_patient_report,
            prediction_payload=st.session_state.new_patient_prediction,
        )

    stats = db.get_statistics()
    k1, k2, k3 = st.columns(3)
    with k1:
        render_kpi_card("Casos registrados", str(stats.get("total_predictions", 0)), "Base de datos CDSS")
    with k2:
        render_kpi_card("Pendientes de validacion", str(stats.get("pending_cases", 0)), "Revision clinica")
    with k3:
        render_kpi_card("Casos confirmados", str(stats.get("confirmed_cases", 0)), "Validacion sanitaria")
