"""Main Streamlit entrypoint for UI package."""

import streamlit as st

from config import config
from streamlit_app.components.layout import apply_theme
from streamlit_app.components.sidebar import render_sidebar
from streamlit_app.pages import dashboard, history, models, new_patient


def run() -> None:
    st.set_page_config(**config.PAGE_CONFIG)
    apply_theme()

    section = render_sidebar()

    if section == "Dashboard":
        dashboard.render()
    elif section == "Modelos":
        models.render()
    elif section == "Nuevo Paciente":
        new_patient.render()
    elif section == "Histórico":
        history.render()
