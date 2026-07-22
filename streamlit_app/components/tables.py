"""Table rendering helpers."""

from __future__ import annotations

import pandas as pd
import streamlit as st


def render_dataframe(dataframe: pd.DataFrame, empty_message: str = "No hay registros disponibles.") -> None:
    if dataframe.empty:
        st.info(empty_message)
        return
    st.dataframe(dataframe, use_container_width=True, hide_index=True)