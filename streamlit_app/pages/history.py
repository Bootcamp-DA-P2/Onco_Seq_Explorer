from __future__ import annotations

import pandas as pd
import streamlit as st

from streamlit_app.database.cdss_database import CDSSDatabase
from managers.feedback_manager import FeedbackManager
from streamlit_app.components.cards import render_kpi_card, render_status_card
from streamlit_app.components.layout import render_page_header
from streamlit_app.components.tables import render_dataframe


def render() -> None:
	render_page_header("Histórico", "Persistencia y seguimiento clínico")
	database = CDSSDatabase()
	rows = database.get_predictions(limit=500)
	dataframe = pd.DataFrame(rows)

	kpi_cols = st.columns(3)
	with kpi_cols[0]:
		render_kpi_card("Predicciones registradas", str(len(dataframe)), "Histórico disponible")
	with kpi_cols[1]:
		tumor_count = int((dataframe["is_tumor"] == 1).sum()) if not dataframe.empty and "is_tumor" in dataframe.columns else 0
		render_kpi_card("Casos tumorales", str(tumor_count), "Modelo 1")
	with kpi_cols[2]:
		normal_count = max(len(dataframe) - tumor_count, 0)
		render_kpi_card("Casos normales", str(normal_count), "Modelo 1")

	st.markdown("### Registro histórico")
	render_dataframe(dataframe, "Todavía no hay predicciones almacenadas en la base de datos.")

	st.markdown("### Confirmación diagnóstica")
	if dataframe.empty:
		st.info("Cuando existan predicciones guardadas, aquí podrás registrar el diagnóstico confirmado y el feedback clínico.")
		return

	prediction_id = st.selectbox("Prediction ID", options=dataframe["id"].tolist())
	confirmed = st.text_input("Diagnóstico confirmado")
	notes = st.text_area("Notas del clínico")
	correct = st.selectbox("¿Coincide con la predicción?", ["No definido", "Sí", "No"], index=0)

	if st.button("Guardar feedback clínico", type="primary"):
		if not confirmed.strip():
			render_status_card("Dato requerido", "Debes indicar el diagnóstico confirmado antes de guardar.", "warning")
			return
		manager = FeedbackManager()
		is_correct = None if correct == "No definido" else (correct == "Sí")
		feedback_id = manager.submit_feedback(
			prediction_id=int(prediction_id),
			confirmed_diagnosis=confirmed.strip(),
			clinical_notes=notes,
			is_correct=is_correct,
		)
		render_status_card("Feedback guardado", f"Registro clínico almacenado con ID {feedback_id}", "ok")
