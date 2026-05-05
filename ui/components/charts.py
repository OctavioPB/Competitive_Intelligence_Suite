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

    st.plotly_chart(fig, width="stretch")


def render_line_chart(
    df: pd.DataFrame,
    x: str,
    y: str,
    title: str,
    color_column: str | None = None,
) -> None:
    """Render a multi-series line chart with brand styling.

    Args:
        df: DataFrame with at least x and y columns.
        x: Column name for the x-axis (e.g. month).
        y: Column name for the y-axis value.
        title: Chart title string.
        color_column: Optional column that defines series grouping.
                      Each unique value becomes a separate colored line.
    """
    if df.empty:
        st.info("No data available. Run the ingestion and pipeline first.")
        return

    fig = go.Figure()

    if color_column and color_column in df.columns:
        for i, group in enumerate(df[color_column].unique()):
            gdf = df[df[color_column] == group]
            fig.add_trace(
                go.Scatter(
                    x=gdf[x],
                    y=gdf[y],
                    mode="lines+markers",
                    name=str(group),
                    line=dict(color=BRAND_COLORS[i % len(BRAND_COLORS)], width=2),
                    marker=dict(size=6),
                    hovertemplate=(
                        f"<b>{group}</b><br>{x}: %{{x}}<br>{y}: %{{y:.3f}}<extra></extra>"
                    ),
                )
            )
    else:
        fig.add_trace(
            go.Scatter(
                x=df[x],
                y=df[y],
                mode="lines+markers",
                line=dict(color=BRAND_COLORS[0], width=2),
                marker=dict(size=6, color=BRAND_COLORS[0]),
                hovertemplate=f"{x}: %{{x}}<br>{y}: %{{y:.3f}}<extra></extra>",
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
        xaxis=dict(gridcolor="#E0EAF4", zeroline=False, tickangle=-30),
        yaxis=dict(gridcolor="#E0EAF4", zeroline=False, tickfont=dict(size=12)),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        height=380,
    )

    st.plotly_chart(fig, width="stretch")


def render_sentiment_timeline(df: pd.DataFrame, title: str) -> None:
    """Render a sentiment timeline with stddev band and news event star markers.

    Args:
        df: Output of modules.sentiment_timeline.build_timeline().
            Required columns: month, avg_sentiment, stddev, review_count, top_event.
        title: Chart title string.
    """
    if df.empty:
        st.info("No data available. Run the ingestion and pipeline first.")
        return

    months = df["month"].tolist()
    avg = df["avg_sentiment"].tolist()
    std = df["stddev"].tolist()

    upper = [min(1.0, a + s) for a, s in zip(avg, std)]
    lower = [max(-1.0, a - s) for a, s in zip(avg, std)]

    fig = go.Figure()

    # Stddev band — polygon formed by [upper fwd] + [lower reversed]
    fig.add_trace(
        go.Scatter(
            x=months + months[::-1],
            y=upper + lower[::-1],
            fill="toself",
            fillcolor="rgba(0,51,102,0.10)",
            line=dict(color="rgba(255,255,255,0)"),
            showlegend=False,
            hoverinfo="skip",
            name="stddev band",
        )
    )

    # Main sentiment line
    fig.add_trace(
        go.Scatter(
            x=months,
            y=avg,
            mode="lines+markers",
            name="Avg Sentiment",
            line=dict(color="#003366", width=2.5),
            marker=dict(size=7, color="#003366"),
            customdata=list(
                zip(df["review_count"].tolist(), df["top_event"].fillna("").tolist())
            ),
            hovertemplate=(
                "<b>%{x}</b><br>"
                "Sentiment: %{y:.3f}<br>"
                "Reviews: %{customdata[0]}<br>"
                "%{customdata[1]}<extra></extra>"
            ),
        )
    )

    # Gold star markers for months with news events
    event_df = df[df["top_event"].notna()]
    if not event_df.empty:
        fig.add_trace(
            go.Scatter(
                x=event_df["month"].tolist(),
                y=event_df["avg_sentiment"].tolist(),
                mode="markers",
                name="News event",
                marker=dict(
                    symbol="star",
                    size=16,
                    color="#C8982A",
                    line=dict(color="#7A3800", width=1),
                ),
                customdata=event_df["top_event"].tolist(),
                hovertemplate="<b>News:</b> %{customdata}<extra></extra>",
            )
        )

    # Neutral reference line
    fig.add_hline(
        y=0,
        line_dash="dot",
        line_color="rgba(0,0,0,0.2)",
        annotation_text="Neutral",
        annotation_position="right",
        annotation_font_size=11,
    )

    fig.update_layout(
        **{**_LAYOUT_BASE, "margin": dict(l=0, r=80, t=56, b=16)},
        title=dict(
            text=title,
            font=dict(family=_TITLE_FONT, size=18, color="#003366"),
            x=0,
            xanchor="left",
        ),
        xaxis=dict(
            title="Month",
            gridcolor="#E0EAF4",
            zeroline=False,
            tickangle=-30,
        ),
        yaxis=dict(
            title="Avg Sentiment",
            range=[-1.15, 1.15],
            gridcolor="#E0EAF4",
            zeroline=False,
            tickvals=[-1.0, -0.5, 0.0, 0.5, 1.0],
            ticktext=["Very Neg", "Negative", "Neutral", "Positive", "Very Pos"],
        ),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        height=440,
    )

    st.plotly_chart(fig, width="stretch")
