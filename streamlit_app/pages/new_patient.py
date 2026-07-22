from __future__ import annotations

from io import StringIO
from typing import Any

import pandas as pd
import streamlit as st

from streamlit_app.config import config
from streamlit_app.database.cdss_database import CDSSDatabase
from services.loaders import ArtifactLoader
from services.report_generator import ReportGeneratorService
from streamlit_app.components.cards import render_kpi_card, render_status_card
from streamlit_app.components.layout import render_page_header
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


def _build_template_csv(feature_names: list[str]) -> bytes:
    if not feature_names:
        return "".encode("utf-8")
    template_df = pd.DataFrame([{gene: "" for gene in feature_names}])
    return template_df.to_csv(index=False).encode("utf-8")


def _build_patient_payload(
    patient_id: str,
    age: int,
    sex: str,
    nationality: str,
    weight_kg: float,
    height_cm: float,
    bmi: float | None,
    bmi_classification: str,
    smoker_status: str,
    clinical_notes: str,
) -> dict[str, Any]:
    return {
        "patient_id": patient_id.strip(),
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


def render() -> None:
    render_page_header("Nuevo Paciente", "Flujo guiado de incorporación clínica")

    loader = ArtifactLoader()
    database = CDSSDatabase()
    report_service = ReportGeneratorService()

    status = loader.validate_required_artifacts()
    required_ready = all(item.get("status") == "ok" for item in status.values())

    if not required_ready:
        render_status_card(
            "Artefactos incompletos",
            "Faltan archivos necesarios para validar o inferir muestras nuevas. Revisa la pestaña Modelos.",
            "warning",
        )

    feature_names = read_json_file(config.FEATURE_NAMES_PATH)
    expected_feature_count = len(feature_names) if isinstance(feature_names, list) else 0

    st.markdown("### Paso 1. Información clínica")
    col_1, col_2, col_3, col_4 = st.columns(4)
    patient_id = col_1.text_input("Patient ID")
    age = col_2.number_input("Edad", min_value=0, max_value=120, value=50)
    sex = col_3.selectbox("Sexo", ["F", "M", "Otro"])
    nationality = col_4.text_input("Nacionalidad")

    col_5, col_6, col_7, col_8 = st.columns(4)
    weight_kg = col_5.number_input("Peso (kg)", min_value=0.0, max_value=400.0, value=0.0, step=0.1)
    height_cm = col_6.number_input("Altura (cm)", min_value=0.0, max_value=250.0, value=0.0, step=0.1)

    bmi_value, bmi_classification = _calculate_bmi(float(weight_kg), float(height_cm))
    col_7.text_input("IMC", value=f"{bmi_value:.2f}" if bmi_value is not None else "No disponible", disabled=True)
    col_8.text_input("Clasificación IMC", value=bmi_classification, disabled=True)

    smoker_status = st.selectbox("Estado de fumador", ["No", "Sí", "Exfumador"], index=0)
    clinical_notes = st.text_area("Notas clínicas")

    if st.button("Guardar datos clínicos", type="secondary"):
        if not patient_id.strip():
            render_status_card("Dato requerido", "Debes indicar Patient ID para guardar datos clínicos.", "warning")
        else:
            patient_payload = _build_patient_payload(
                patient_id=patient_id,
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
            database.save_or_update_patient(patient_payload)
            render_status_card("Datos clínicos guardados", f"Paciente {patient_id.strip()} actualizado en base de datos.", "ok")

    st.markdown("### Paso 2. Carga RNA-Seq")

    template_bytes = _build_template_csv(feature_names if isinstance(feature_names, list) else [])
    st.download_button(
        label="Descargar plantilla CSV",
        data=template_bytes,
        file_name="plantilla_rnaseq.csv",
        mime="text/csv",
        disabled=not bool(template_bytes),
    )

    upload = st.file_uploader("Subir CSV de expresión RNA", type=["csv"])

    info_cols = st.columns(3)
    with info_cols[0]:
        render_kpi_card("Genes esperados", str(expected_feature_count or "N/D"), "feature_names.json")
    with info_cols[1]:
        render_kpi_card("Modelo 1", "Disponible" if status["pipeline_modelo1.joblib"]["status"] == "ok" else "No disponible")
    with info_cols[2]:
        render_kpi_card("Modelo 2", "Disponible" if status["pipeline_modelo2.joblib"]["status"] == "ok" else "No disponible")

    if upload is not None:
        try:
            dataframe = pd.read_csv(StringIO(upload.getvalue().decode("utf-8")))
            st.markdown("### Validación preliminar del archivo")
            st.dataframe(dataframe.head(20), use_container_width=True, hide_index=True)

            column_names = list(dataframe.columns)
            if feature_names and isinstance(feature_names, list):
                missing_genes = [gene for gene in feature_names if gene not in column_names][:25]
                extra_genes = [gene for gene in column_names if gene not in feature_names][:25]
                order_matches = column_names[: min(len(column_names), len(feature_names))] == feature_names[: min(len(column_names), len(feature_names))]

                validation_cols = st.columns(3)
                validation_cols[0].metric("Genes faltantes", str(len([gene for gene in feature_names if gene not in column_names])))
                validation_cols[1].metric("Genes adicionales", str(len([gene for gene in column_names if gene not in feature_names])))
                validation_cols[2].metric("Orden correcto", "Sí" if order_matches else "No")

                if missing_genes:
                    render_status_card("Genes faltantes", ", ".join(missing_genes), "warning")
                if extra_genes:
                    render_status_card("Genes adicionales", ", ".join(extra_genes), "warning")
                if not missing_genes and not extra_genes:
                    render_status_card("Validación estructural", "El archivo contiene todos los genes esperados del modelado.", "ok")

            st.markdown("### Paso 3. Inferencia")
            st.info("La inferencia jerárquica se activará en la siguiente fase sobre esta misma pantalla.")
        except Exception as exc:
            render_status_card("Error al leer el CSV", str(exc), "error")
    else:
        st.info("Sube un archivo CSV para iniciar la validación estructural frente a feature_names.json.")

    st.markdown("### Paso 4. Informe clínico")
    if report_service.is_available():
        patient_payload = _build_patient_payload(
            patient_id=patient_id,
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
        pdf_bytes = report_service.build_patient_intake_pdf_bytes(patient_payload)
        st.download_button(
            label="Descargar informe PDF",
            data=pdf_bytes,
            file_name=f"informe_clinico_{patient_id.strip() or 'paciente'}.pdf",
            mime="application/pdf",
            disabled=not bool(patient_id.strip()),
        )
    else:
        st.info("Generación PDF no disponible en este entorno. Instala reportlab para habilitarla.")
