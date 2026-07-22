"""Chart helpers for Plotly figures."""

from __future__ import annotations

import plotly.graph_objects as go


def style_figure(figure: go.Figure, title: str = "", y_title: str | None = None) -> go.Figure:
    figure.update_layout(
        template="plotly_white",
        title={"text": title, "x": 0.02, "xanchor": "left"},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#FFFFFF",
        margin={"l": 25, "r": 20, "t": 60, "b": 25},
        legend={"orientation": "h", "y": -0.18, "x": 0},
    )
    if y_title is not None:
        figure.update_yaxes(title_text=y_title, gridcolor="#E2E8F0")
    figure.update_xaxes(gridcolor="#E2E8F0")
    return figure