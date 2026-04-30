"""Plotly chart wrappers applying the RivalSense brand color system."""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# Brand multi-series color order (BRAND.md §Data Visualization Color Series)
BRAND_COLORS = ["#003366", "#27B97C", "#7C4DBD", "#F07020", "#E05080"]

# Severity colorscale: green (low pain) → orange → red (high pain)
_SEVERITY_COLORSCALE = [
    [0.0, "#27B97C"],   # green — low severity
    [0.5, "#F07020"],   # orange — medium
    [1.0, "#E03448"],   # red — high severity
]

_FONT_FAMILY = "Plus Jakarta Sans, sans-serif"
_TITLE_FONT = "Fraunces, Georgia, serif"

_LAYOUT_BASE = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="#F4F6F9",
    font=dict(family=_FONT_FAMILY, size=13, color="#1C1C2E"),
    margin=dict(l=0, r=24, t=48, b=16),
    hoverlabel=dict(bgcolor="#003366", font_color="white", font_family=_FONT_FAMILY),
)


def render_bar_chart(
    df: pd.DataFrame,
    x: str,
    y: str,
    title: str,
    color_column: str | None = None,
) -> None:
    """Render a horizontal bar chart with brand styling via Plotly.

    Args:
        df: DataFrame with at least the x and y columns.
        x: Column name for the bar values (horizontal axis — typically mention_count).
        y: Column name for the category labels (vertical axis — typically topic_label).
        title: Chart title string.
        color_column: Optional column used to color bars by severity (0–1 float).
                      When provided, applies the green→orange→red severity colorscale.
    """
    if df.empty:
        st.info("No data available. Run the ingestion and pipeline first.")
        return

    if color_column and color_column in df.columns:
        marker = dict(
            color=df[color_column],
            colorscale=_SEVERITY_COLORSCALE,
            cmin=0.0,
            cmax=1.0,
            showscale=True,
            colorbar=dict(
                title=dict(text="Severity", font=dict(size=11)),
                tickvals=[0, 0.5, 1.0],
                ticktext=["Low", "Medium", "High"],
                thickness=12,
                len=0.6,
            ),
        )
    else:
        marker = dict(color=BRAND_COLORS[0])

    fig = go.Figure(
        go.Bar(
            x=df[x],
            y=df[y],
            orientation="h",
            marker=marker,
            text=df[x].apply(lambda v: f"  {v}"),
            textposition="outside",
            textfont=dict(size=11, color="#6B7280"),
            hovertemplate=f"<b>%{{y}}</b><br>{x}: %{{x}}<extra></extra>",
        )
    )

    fig.update_layout(
        **_LAYOUT_BASE,
        title=dict(
            text=title,
            font=dict(family=_TITLE_FONT, size=18, color="#003366"),
            x=0,
            xanchor="left",
        ),
        yaxis=dict(
            autorange="reversed",
            tickfont=dict(size=12),
            gridcolor="rgba(0,0,0,0)",
        ),
        xaxis=dict(
            title=x.replace("_", " ").title(),
            gridcolor="#E0EAF4",
            zeroline=False,
        ),
        height=max(320, len(df) * 44),
    )

    st.plotly_chart(fig, use_container_width=True)


def render_line_chart(
    df: pd.DataFrame,
    x: str,
    y: str,
    title: str,
    color_column: str | None = None,
) -> None:
    """Render a line chart with brand styling and optional event markers.

    Args:
        df: DataFrame with at least x and y columns.
        x: Column name for the x-axis (typically month).
        y: Column name for the y-axis value.
        title: Chart title string.
        color_column: Optional grouping column for multi-series charts.
    """
    raise NotImplementedError("Implement in Sprint 3 — Day 7")
