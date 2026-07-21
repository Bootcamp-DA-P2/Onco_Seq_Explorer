"""Layout and theme primitives for Streamlit pages."""

from __future__ import annotations

import streamlit as st

from config import config


def apply_theme() -> None:
    colors = config.COLORS
    st.markdown(
        f"""
        <style>
        .stApp {{
            background-color: {colors['background']};
            color: {colors['text']} !important;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        }}
        .stMarkdown, p, span, label, .stCaption {{ color: #334155 !important; }}
        h1, h2, h3, h4, h5, h6 {{ color: {colors['text']} !important; font-weight: 700 !important; }}
        [data-testid="stSidebar"] {{
            background-color: {colors['sidebar']} !important;
            border-right: 1px solid #334155;
        }}
        [data-testid="stSidebar"] * {{ color: #F1F5F9 !important; }}
        .oncoseq-section-card {{
            background: rgba(255,255,255,0.88);
            border: 1px solid {colors['border']};
            border-radius: 14px;
            box-shadow: 0 6px 20px rgba(148, 163, 184, 0.10);
            padding: 18px;
            margin-bottom: 16px;
            backdrop-filter: blur(4px);
        }}
        .oncoseq-section-title {{
            font-size: 18px;
            font-weight: 700;
            color: {colors['text']};
            margin-bottom: 8px;
            border-left: 4px solid {colors['primary']};
            padding-left: 12px;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_page_header(title: str, subtitle: str) -> None:
    st.title(title)
    st.caption(subtitle)


def render_section(title: str, body: str) -> None:
    st.markdown(
        f"""
        <div class="oncoseq-section-card">
            <div class="oncoseq-section-title">{title}</div>
            <div>{body}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )