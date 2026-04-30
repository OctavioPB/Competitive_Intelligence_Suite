"""Page 1 — Pain Point Radar (M01)."""

import streamlit as st

from modules.pain_point_radar import get_pain_points
from ui.components.charts import render_bar_chart
from ui.components.competitor_selector import render_competitor_selector

# ── Brand CSS (injected once per page load) ───────────────────────────────────
_BRAND_CSS = """
<style>
.rivalsense-hero {
    background: #003366;
    background-image:
        linear-gradient(rgba(255,255,255,.025) 1px, transparent 1px),
        linear-gradient(90deg, rgba(255,255,255,.025) 1px, transparent 1px);
    background-size: 48px 48px;
    border-radius: 12px;
    padding: 40px 40px 32px;
    margin-bottom: 28px;
}
.rivalsense-hero h1 {
    font-family: 'Fraunces', Georgia, serif;
    font-weight: 300;
    font-size: 32px;
    color: #ffffff;
    margin: 0 0 8px;
}
.rivalsense-hero p {
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-size: 14px;
    color: rgba(255,255,255,0.55);
    margin: 0;
}
.kpi-row { display: flex; gap: 16px; margin-bottom: 28px; }
.kpi-card {
    flex: 1;
    background: #ffffff;
    border-radius: 12px;
    padding: 24px 20px 20px;
    border-top: 3px solid #C8982A;
    box-shadow: 0 1px 4px rgba(0,51,102,.08);
    text-align: center;
}
.kpi-card .kpi-value {
    font-family: 'Fraunces', Georgia, serif;
    font-size: 32px;
    font-weight: 300;
    color: #1C1C2E;
    line-height: 1.1;
}
.kpi-card .kpi-label {
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-size: 10px;
    font-weight: 500;
    letter-spacing: 3px;
    text-transform: uppercase;
    color: #6B7280;
    margin-top: 6px;
}
.section-eyebrow {
    display: flex;
    align-items: center;
    gap: 12px;
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-size: 9px;
    font-weight: 500;
    letter-spacing: 4px;
    text-transform: uppercase;
    color: #C8982A;
    margin-bottom: 6px;
}
.section-eyebrow::before {
    content: '';
    display: block;
    width: 24px;
    height: 1px;
    background: #C8982A;
}
.section-desc {
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-size: 13px;
    color: #6B7280;
    margin-bottom: 20px;
}
.trend-badge {
    display: inline-block;
    border-radius: 20px;
    padding: 3px 10px;
    font-size: 10px;
    font-weight: 500;
    letter-spacing: 1px;
}
.trend-rising  { background:#E0F7EF; color:#0D5C3A; }
.trend-stable  { background:#E0EAF4; color:#001F4D; }
.trend-declining { background:#FDEAEA; color:#7A1020; }
.section-divider {
    height: 1px;
    background: #E0EAF4;
    margin: 28px 0;
}
</style>
<link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700&family=Fraunces:ital,opsz,wght@0,9..144,300;0,9..144,400;1,9..144,300;1,9..144,400&display=swap" rel="stylesheet">
"""


def _severity_badge(severity: float) -> str:
    """Return an HTML badge string colored by severity level."""
    if severity >= 0.65:
        bg, fg = "#FDEAEA", "#7A1020"
        label = "High"
    elif severity >= 0.40:
        bg, fg = "#FEF0E6", "#7A3800"
        label = "Medium"
    else:
        bg, fg = "#E0F7EF", "#0D5C3A"
        label = "Low"
    return (
        f'<span style="background:{bg};color:{fg};font-size:10px;letter-spacing:1px;'
        f'padding:3px 10px;border-radius:20px;font-family:\'Plus Jakarta Sans\',sans-serif;">'
        f"{label}</span>"
    )


def render() -> None:
    """Render the Pain Point Radar page."""
    st.markdown(_BRAND_CSS, unsafe_allow_html=True)

    # ── Hero ──────────────────────────────────────────────────────────────────
    st.markdown(
        """
        <div class="rivalsense-hero">
            <h1>Pain Point <em style="color:#C8982A;">Radar</em></h1>
            <p>Competitor pain points ranked by mention volume and severity — updated from live review data.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── Competitor selector ───────────────────────────────────────────────────
    competitor = render_competitor_selector(key="m01_competitor")

    df = get_pain_points(competitor, top_n=10)

    if df.empty:
        st.warning(
            f"No processed data found for **{competitor}**. "
            "Run `python ingestion/run_ingestion.py --use-fixtures` then `python pipeline/run_pipeline.py`."
        )
        return

    # ── KPI row ───────────────────────────────────────────────────────────────
    total_mentions = int(df["mention_count"].sum())
    avg_severity = float(df["avg_severity"].mean())
    rising_count = int((df["trend_direction"] == "rising").sum())

    st.markdown(
        f"""
        <div class="kpi-row">
            <div class="kpi-card">
                <div class="kpi-value">{total_mentions:,}</div>
                <div class="kpi-label">Total Mentions</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-value">{avg_severity:.0%}</div>
                <div class="kpi-label">Avg Severity</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-value">{rising_count}</div>
                <div class="kpi-label">Rising Topics</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-value">{len(df)}</div>
                <div class="kpi-label">Pain Clusters</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── Chart ─────────────────────────────────────────────────────────────────
    st.markdown(
        '<div class="section-eyebrow">Pain Points</div>'
        '<div class="section-desc">Ranked by severity (high pain → top). '
        "Bar color indicates severity level.</div>",
        unsafe_allow_html=True,
    )

    chart_df = df.copy()
    chart_df["topic_label"] = chart_df["topic_label"] + "  " + chart_df["trend_icon"]

    render_bar_chart(chart_df, x="mention_count", y="topic_label",
                     title=f"{competitor} — Top Pain Points", color_column="avg_severity")

    # ── Divider ───────────────────────────────────────────────────────────────
    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

    # ── Detail table ──────────────────────────────────────────────────────────
    st.markdown(
        '<div class="section-eyebrow">Detail</div>'
        '<div class="section-desc">All pain clusters with severity rating and trend.</div>',
        unsafe_allow_html=True,
    )

    # Build HTML table for brand styling
    rows_html = ""
    for i, row in df.iterrows():
        trend_css = f"trend-{row['trend_direction']}"
        rows_html += f"""
        <tr style="background:{'#ffffff' if i % 2 == 0 else '#E0EAF4'}">
            <td style="padding:12px 16px;font-family:'Plus Jakarta Sans',sans-serif;font-size:13px;">{row['topic_label']}</td>
            <td style="padding:12px 16px;text-align:center;font-family:'Plus Jakarta Sans',sans-serif;">{row['mention_count']:,}</td>
            <td style="padding:12px 16px;text-align:center;">{_severity_badge(row['avg_severity'])}</td>
            <td style="padding:12px 16px;text-align:center;">
                <span class="trend-badge {trend_css}">{row['trend_icon']} {row['trend_direction'].title()}</span>
            </td>
        </tr>"""

    table_html = f"""
    <table style="width:100%;border-collapse:collapse;border-radius:12px;overflow:hidden;
                  box-shadow:0 1px 4px rgba(0,51,102,.08);">
        <thead>
            <tr style="background:#003366;">
                <th style="padding:12px 16px;text-align:left;color:#ffffff;font-family:'Plus Jakarta Sans',sans-serif;
                           font-size:10px;letter-spacing:2px;text-transform:uppercase;font-weight:500;">Pain Point</th>
                <th style="padding:12px 16px;text-align:center;color:#ffffff;font-family:'Plus Jakarta Sans',sans-serif;
                           font-size:10px;letter-spacing:2px;text-transform:uppercase;font-weight:500;">Mentions</th>
                <th style="padding:12px 16px;text-align:center;color:#ffffff;font-family:'Plus Jakarta Sans',sans-serif;
                           font-size:10px;letter-spacing:2px;text-transform:uppercase;font-weight:500;">Severity</th>
                <th style="padding:12px 16px;text-align:center;color:#ffffff;font-family:'Plus Jakarta Sans',sans-serif;
                           font-size:10px;letter-spacing:2px;text-transform:uppercase;font-weight:500;">Trend</th>
            </tr>
        </thead>
        <tbody>{rows_html}</tbody>
    </table>
    """
    st.markdown(table_html, unsafe_allow_html=True)


# Entry point when Streamlit runs this file via st.navigation()
render()
