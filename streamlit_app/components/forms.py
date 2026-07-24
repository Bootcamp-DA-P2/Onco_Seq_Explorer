"""Form placeholders for guided clinical workflows."""

from __future__ import annotations

import streamlit as st


def render_placeholder_form(title: str, message: str) -> None:
    st.subheader(title)
    st.info(message)