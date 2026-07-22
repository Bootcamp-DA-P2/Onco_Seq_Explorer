from __future__ import annotations

from io import StringIO

import pandas as pd
import streamlit as st

from components.cards import render_kpi_card, render_status_card
from components.layout import render_page_header
from streamlit_app.config import config
from services.loaders import ArtifactLoader
from utils.helpers import read_json_file


def render() -> None:
	render_page_header("Nuevo Paciente", "Flujo guiado de incorporación clínica")
	loader = ArtifactLoader()
	status = loader.validate_required_artifacts()
	required_ready = all(item.get("status") == "ok" for item in status.values())

	if not required_ready:
		render_status_card(
			"Artefactos incompletos",
			"Faltan archivos necesarios para validar o inferir muestras nuevas. Revisa la pestaña Modelos.",
			"warning",
		)

	st.markdown("### Paso 1. Información clínica")
	col_1, col_2, col_3 = st.columns(3)
	patient_id = col_1.text_input("Patient ID")
	age = col_2.number_input("Edad", min_value=0, max_value=120, value=50)
	sex = col_3.selectbox("Sexo", ["F", "M", "Otro"])
	clinical_notes = st.text_area("Notas clínicas")

	st.markdown("### Paso 2. Carga RNA-Seq")
	upload = st.file_uploader("Subir CSV de expresión RNA", type=["csv"])

	feature_names = read_json_file(config.FEATURE_NAMES_PATH)
	expected_feature_count = len(feature_names) if isinstance(feature_names, list) else 0

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
			st.markdown("### Paso 4. Informe clínico")
			st.info("La generación y descarga del informe clínico se integrará después de la inferencia.")
		except Exception as exc:
			render_status_card("Error al leer el CSV", str(exc), "error")
	else:
		st.info("Sube un archivo CSV para iniciar la validación estructural frente a feature_names.json.")
