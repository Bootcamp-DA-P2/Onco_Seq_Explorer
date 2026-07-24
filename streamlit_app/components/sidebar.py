"""Sidebar navigation rendering."""

from __future__ import annotations

import streamlit as st

from utils.constants import NAV_ITEMS


def render_sidebar() -> str:
    st.sidebar.title("OncoLens")
    st.sidebar.markdown("Panel de navegación clínica")
    return st.sidebar.radio("Navegación", NAV_ITEMS, index=0)