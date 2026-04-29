"""Plotly chart wrappers applying the RivalSense brand color system."""

import plotly.graph_objects as go
import streamlit as st

# Brand color series — apply in order for multi-series charts
BRAND_COLORS = ["#003366", "#27B97C", "#7C4DBD", "#F07020", "#E05080"]
SEVERITY_COLOR_SCALE = [[0, "#E0EAF4"], [0.5, "#F07020"], [1.0, "#E03448"]]


def render_bar_chart(
    df,
    x: str,
    y: str,
    title: str,
    color_column: str | None = None,
) -> None:
    """Render a horizontal bar chart with brand styling.

    Args:
        df: DataFrame with at least the x and y columns.
        x: Column name for the bar values (horizontal axis).
        y: Column name for the category labels (vertical axis).
        title: Chart title string.
        color_column: Optional column used to color bars (e.g. avg_severity).
    """
    raise NotImplementedError("Implement in Sprint 2 — Day 4")


def render_line_chart(
    df,
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
