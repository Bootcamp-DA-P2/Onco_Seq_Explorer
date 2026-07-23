from __future__ import annotations

from datetime import datetime
from io import BytesIO
from urllib.parse import quote
from typing import Any, Dict, Tuple

import pandas as pd
import plotly.express as px
import streamlit as st

from managers.prediction_manager import PredictionManager
from services.report_generator import ClinicalReport, ReportGeneratorService
from streamlit_app.components.cards import render_status_card
from streamlit_app.components.layout import render_page_header
from streamlit_app.config import config
from streamlit_app.database.cdss_database import CDSSDatabase
from utils.helpers import read_json_file


def _inject_page_style() -> None:
    st.markdown(
        """
        <style>
            .np-shell {
                background: radial-gradient(circle at 10% 0%, #eef6ff 0%, transparent 42%),
                            radial-gradient(circle at 95% 10%, #f2f9ff 0%, transparent 35%),
                            #f7fafc;
                border: 1px solid #dbe7f3;
                border-radius: 18px;
                padding: 16px;
                margin-bottom: 14px;
            }
            .np-card {
                background: #ffffff;
                border: 1px solid #dde7f2;
                border-radius: 14px;
                padding: 14px;
                margin-bottom: 12px;
                box-shadow: 0 10px 24px rgba(14, 28, 45, 0.04);
            }
            .np-title {
                margin: 0 0 8px 0;
                font-size: 15px;
                color: #0f3759;
                font-weight: 700;
            }
            .np-step {
                display:inline-flex;
                align-items:center;
                gap:8px;
                background:#edf6ff;
                color:#11406a;
                border:1px solid #cfe1f4;
                border-radius:999px;
                padding:4px 10px;
                font-size:11px;
                font-weight:600;
                text-transform:uppercase;
                letter-spacing:0.4px;
                margin-bottom:8px;
            }
            .np-kpi {
                background: linear-gradient(180deg, #ffffff 0%, #f8fbff 100%);
                border:1px solid #d8e8f8;
                border-radius:14px;
                padding:14px;
            }
            .np-kpi-label {
                font-size:11px;
                color:#516174;
                margin-bottom:5px;
                text-transform:uppercase;
                letter-spacing:0.45px;
            }
            .np-kpi-value {
                font-size:30px;
                font-weight:700;
                color:#0c3d66;
                line-height:1.1;
            }
            .np-kpi-sub { font-size:12px; color:#475569; margin-top:4px; }
        </style>
        """,
        unsafe_allow_html=True,
    )


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


def _format_pct(probability: float | None) -> str:
    value = float(probability or 0.0) * 100
    return f"{value:.1f}%"


def _build_excel_template(feature_names: list[str]) -> bytes:
    instructions = pd.DataFrame(
        {
            "Instrucciones": [
                "1) Completa la hoja Muestra en formato vertical (gene, expression).",
                "2) No cambies nombres de columnas ni elimines genes.",
                "3) Introduce valores numericos en expression.",
                "4) Celdas vacias se imputaran como 0.0 para compatibilidad.",
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
        else "Muestra validada con ajustes automaticos."
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


def _build_storage_context(patient_payload: Dict[str, Any], consent: bool) -> Dict[str, Any]:
    if consent:
        return patient_payload

    return {
        "patient_id": f"ANON-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "first_name": None,
        "last_name": None,
        "age": None,
        "sex": None,
        "nationality": None,
        "weight_kg": None,
        "height_cm": None,
        "bmi": None,
        "bmi_classification": None,
        "smoker_status": None,
        "cohort": None,
        "clinical_notes": None,
    }


def _render_primary_results(prediction_payload: Dict[str, Any]) -> None:
    st.markdown('<div class="np-card"><div class="np-step">Resultado principal</div><h3 class="np-title">Prediccion clinica IA</h3>', unsafe_allow_html=True)

    model1_text = "Tumoral" if prediction_payload.get("is_tumor") else "Normal"
    cancer_type = prediction_payload.get("stage2_prediction") if prediction_payload.get("is_tumor") else "No aplica"
    probability = prediction_payload.get("stage2_probability") if prediction_payload.get("is_tumor") else prediction_payload.get("stage1_probability")

    c1, c2, c3 = st.columns(3)
    c1.markdown(
        f'<div class="np-kpi"><div class="np-kpi-label">Clasificacion inicial</div><div class="np-kpi-value">{model1_text}</div><div class="np-kpi-sub">Modelo 1 (Normal vs Tumoral)</div></div>',
        unsafe_allow_html=True,
    )
    c2.markdown(
        f'<div class="np-kpi"><div class="np-kpi-label">Tipo de cancer estimado</div><div class="np-kpi-value">{cancer_type}</div><div class="np-kpi-sub">Resultado clinico principal</div></div>',
        unsafe_allow_html=True,
    )
    c3.markdown(
        f'<div class="np-kpi"><div class="np-kpi-label">Probabilidad</div><div class="np-kpi-value">{_format_pct(probability)}</div><div class="np-kpi-sub">Confianza del resultado</div></div>',
        unsafe_allow_html=True,
    )

    st.markdown('</div>', unsafe_allow_html=True)


def _render_advanced_analysis(prediction_payload: Dict[str, Any]) -> None:
    st.markdown("### Detalles IA")
    st.caption("Vista técnica para análisis de comportamiento del modelo. Esta información no forma parte del flujo clínico principal.")

    probabilities = prediction_payload.get("model2_probabilities", {}) or {}
    if not probabilities:
        st.info("No hay distribucion de probabilidades multiclase para este caso.")
        return

    probs_df = pd.DataFrame(
        [{"Clase": cls, "Probabilidad": float(prob)} for cls, prob in probabilities.items()]
    ).sort_values(by="Probabilidad", ascending=False)
    probs_df["Probabilidad (%)"] = probs_df["Probabilidad"].map(lambda val: round(val * 100, 2))

    st.dataframe(probs_df[["Clase", "Probabilidad (%)"]], width="stretch", hide_index=True)

    fig = px.bar(
        probs_df.sort_values(by="Probabilidad", ascending=True),
        x="Probabilidad",
        y="Clase",
        orientation="h",
        color="Probabilidad",
        color_continuous_scale=["#e2e8f0", "#1068DA"],
    )
    fig.update_layout(title="Distribucion de probabilidades", showlegend=False)
    st.plotly_chart(fig, width="stretch")

    st.markdown("### Explicacion del modelo")
    top_class = probs_df.iloc[0]["Clase"] if not probs_df.empty else "N/D"
    top_prob = probs_df.iloc[0]["Probabilidad (%)"] if not probs_df.empty else 0
    st.info(
        f"La prediccion final se asigna a la clase con mayor probabilidad posterior. "
        f"En este caso, la clase dominante es {top_class} con {top_prob:.2f}%."
    )


def _render_report(report: ClinicalReport, report_service: ReportGeneratorService) -> None:
    st.markdown("### Informe clinico")
    html = report_service.render_html_report(report)

    pdf_bytes = report_service.build_pdf_from_html(html)
    if pdf_bytes is not None:
        st.download_button(
            label="Descargar informe PDF",
            data=pdf_bytes,
            file_name=f"informe_resultados_{report.patient.get('patient_id', 'paciente')}.pdf",
            mime="application/pdf",
        )
    else:
        st.info("No fue posible generar el PDF en este entorno. El informe HTML permanece disponible.")

    html_data_url = "data:text/html;charset=utf-8," + quote(html)
    st.iframe(html_data_url, height=980)


def render() -> None:
    _inject_page_style()
    render_page_header(
        "Nuevo Paciente",
        "Registro clinico, validacion de muestra y prediccion IA en una sola vista.",
    )

    db = CDSSDatabase()
    prediction_manager = PredictionManager()
    report_service = ReportGeneratorService()

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

    if st.button("Nueva evaluacion", width="content"):
        st.session_state.new_patient_validated_df = None
        st.session_state.new_patient_validation_summary = {}
        st.session_state.new_patient_prediction = None
        st.session_state.new_patient_report = None
        st.rerun()

    st.markdown('<div class="np-shell">', unsafe_allow_html=True)

    st.markdown('<div class="np-card"><div class="np-step">Paso 1</div><h3 class="np-title">Datos del paciente</h3>', unsafe_allow_html=True)

    p1, p2, p3 = st.columns(3)
    patient_id = p1.text_input("ID del paciente")
    first_name = p2.text_input("Nombre")
    last_name = p3.text_input("Apellidos")

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
    clinical_notes = st.text_area("Observaciones clinicas", height=80)

    consent = st.checkbox(
        "Autorizo el almacenamiento anonimizado de mis datos clinicos y resultados para fines de investigacion y mejora del sistema de IA.",
        value=False,
    )

    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="np-card"><div class="np-step">Paso 2</div><h3 class="np-title">Muestra RNA-Seq</h3>', unsafe_allow_html=True)

    c1, c2 = st.columns([1, 1])
    with c1:
        template_xlsx = _build_excel_template(feature_names)
        st.download_button(
            label="Descargar plantilla Excel",
            data=template_xlsx,
            file_name="plantilla_rnaseq.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

    with c2:
        upload = st.file_uploader("Subir muestra RNA-Seq (.xlsx)", type=["xlsx"])

    if upload is not None:
        validated_df, validation_summary = _validate_uploaded_sample(upload, feature_names)
        st.session_state.new_patient_validated_df = validated_df
        st.session_state.new_patient_validation_summary = validation_summary

        if validation_summary.get("status") in {"VALIDA", "VALIDA_CON_AJUSTES"}:
            render_status_card("Muestra procesada", validation_summary.get("message", ""), "ok")
        else:
            render_status_card("Muestra no valida", validation_summary.get("message", ""), "warning")

        with st.expander("Ver detalles de la validacion"):
            st.write(f"Genes encontrados: {validation_summary.get('genes_found', 0)}")
            st.write(f"Genes faltantes: {validation_summary.get('missing_count', 0)}")
            st.write(f"Genes adicionales: {validation_summary.get('extra_count', 0)}")
            st.write(f"Valores no numericos: {validation_summary.get('non_numeric_count', 0)}")
            st.write(f"Valores nulos: {validation_summary.get('null_count', 0)}")
            missing_genes = validation_summary.get("missing_genes", [])
            extra_genes = validation_summary.get("extra_genes", [])
            if missing_genes:
                st.caption("Genes faltantes: " + ", ".join(missing_genes))
            if extra_genes:
                st.caption("Genes adicionales: " + ", ".join(extra_genes))

    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="np-card"><div class="np-step">Paso 3</div><h3 class="np-title">Ejecutar prediccion</h3>', unsafe_allow_html=True)
    analyze_clicked = st.button("Analizar muestra", type="primary", width="stretch")
    st.markdown('</div>', unsafe_allow_html=True)

    if analyze_clicked:
        if not patient_id.strip():
            render_status_card("Dato requerido", "Debes indicar el ID del paciente.", "warning")
            return

        validated_df = st.session_state.new_patient_validated_df
        validation_summary = st.session_state.new_patient_validation_summary or {}

        if validated_df is None or validated_df.empty:
            render_status_card("Muestra no valida", "Sube y valida una muestra antes de analizar.", "warning")
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

        progress = st.progress(0, text="Validando muestra")
        progress.progress(25, text="Ejecutando Modelo 1")

        storage_context = _build_storage_context(patient_payload, consent=consent)
        if consent:
            db.save_or_update_patient(patient_payload)

        prediction_payload = prediction_manager.run_prediction(
            sample_df=validated_df,
            sample_name=f"sample_{patient_id.strip()}",
            user_notes=clinical_notes if consent else "",
            patient_context=storage_context,
            validation_summary=validation_summary,
        )

        progress.progress(60, text="Ejecutando Modelo 2")
        progress.progress(85, text="Generando informe de resultados")

        model1_result = {
            "predicted_label": str(prediction_payload.get("stage1_prediction", "")).upper(),
            "normal_tumoral": "Tumoral" if prediction_payload.get("is_tumor") else "Normal",
            "probability": _format_pct(prediction_payload.get("stage1_probability")),
        }
        model2_result = {
            "predicted_cancer": prediction_payload.get("stage2_prediction") or "No aplica",
            "probability": (
                _format_pct(prediction_payload.get("stage2_probability"))
                if prediction_payload.get("is_tumor")
                else "No aplica"
            ),
        }

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
        if consent:
            render_status_card("Analisis completado", "Prediccion registrada con consentimiento para investigacion.", "ok")
        else:
            render_status_card("Analisis completado", "Prediccion ejecutada sin almacenar datos personales.", "ok")

    if st.session_state.new_patient_prediction and st.session_state.new_patient_report:
        result_tab, advanced_tab = st.tabs(["Resultado clinico", "Analisis avanzado"])
        with result_tab:
            _render_primary_results(st.session_state.new_patient_prediction)
            _render_report(st.session_state.new_patient_report, report_service)
        with advanced_tab:
            _render_advanced_analysis(st.session_state.new_patient_prediction)

    st.markdown('</div>', unsafe_allow_html=True)
