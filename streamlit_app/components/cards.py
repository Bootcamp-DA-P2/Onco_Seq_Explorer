"""Reusable card components."""

from __future__ import annotations

import streamlit as st

from config import config


def render_kpi_card(title: str, value: str, subtitle: str = "") -> None:
    colors = config.COLORS
    st.markdown(
        f"""
        <div style="background:{colors['surface']};padding:20px;border-radius:12px;box-shadow:0 4px 15px rgba(148,163,184,0.12);text-align:center;margin-bottom:15px;border-top:5px solid {colors['primary']};border:1px solid {colors['border']};">
            <div style="font-size:13px;text-transform:uppercase;letter-spacing:0.8px;color:{colors['muted']};font-weight:600;margin-bottom:8px;">{title}</div>
            <div style="font-size:28px;font-weight:700;color:{colors['primary']};">{value}</div>
            <div style="font-size:12px;color:{colors['muted']};margin-top:6px;">{subtitle}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_status_card(title: str, text: str, kind: str = "ok") -> None:
    palette = {
        "ok": ("#EEF9EF", config.COLORS["success"], "#1F5D26"),
        "warning": ("#FFF6E8", config.COLORS["warning"], "#7F4E00"),
        "error": ("#FDEEEE", config.COLORS["danger"], "#7F1D1D"),
    }
    background, border, color = palette.get(kind, palette["ok"])
    st.markdown(
        f"""
        <div style="border:1px solid {border};background:{background};color:{color};border-radius:10px;padding:0.85rem;margin-bottom:0.75rem;">
            <strong>{title}</strong><br>{text}
        </div>
        """,
        unsafe_allow_html=True,
    )