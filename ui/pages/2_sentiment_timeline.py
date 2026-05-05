"""Page 2 — Sentiment Timeline (M02)."""

import streamlit as st

from modules.sentiment_timeline import build_timeline
from ui.components.charts import render_sentiment_timeline
from ui.components.competitor_selector import render_competitor_selector

_BRAND_CSS = """
<link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600&family=Fraunces:ital,opsz,wght@0,9..144,300;1,9..144,300&display=swap" rel="stylesheet">
<style>
.rs-kpi {
    background: #ffffff;
    border-radius: 10px;
    padding: 20px 24px;
    border-top: 3px solid #003366;
    box-shadow: 0 1px 4px rgba(0,51,102,.08);
}
.rs-kpi-label {
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-size: 11px;
    letter-spacing: 2px;
    text-transform: uppercase;
    color: #6B7280;
    margin-bottom: 4px;
}
.rs-kpi-value {
    font-family: 'Fraunces', Georgia, serif;
    font-size: 28px;
    font-weight: 300;
    color: #003366;
}
.rs-kpi-sub {
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-size: 12px;
    color: #6B7280;
    margin-top: 2px;
}
</style>
"""

st.html(_BRAND_CSS)

# ── Hero ──────────────────────────────────────────────────────────────────────
st.markdown(
    """
    <div style="background:#003366;padding:32px 40px;border-radius:12px;margin-bottom:28px;
    background-image:linear-gradient(rgba(255,255,255,.025) 1px,transparent 1px),
    linear-gradient(90deg,rgba(255,255,255,.025) 1px,transparent 1px);
    background-size:48px 48px;">
        <div style="font-family:'Fraunces',Georgia,serif;font-weight:300;
                    color:#ffffff;font-size:28px;margin:0 0 8px;">
            Sentiment Timeline
        </div>
        <div style="color:rgba(255,255,255,0.6);font-size:14px;
                    font-family:'Plus Jakarta Sans',sans-serif;line-height:1.6;">
            18-month competitor sentiment trend with news event overlay.
            Gold stars mark months with the most negative news coverage.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ── Controls ──────────────────────────────────────────────────────────────────
col_sel, col_months = st.columns([2, 1])
with col_sel:
    competitor = render_competitor_selector(key="m02_competitor")
with col_months:
    months = st.slider("Months of history", min_value=1, max_value=18, value=18, step=1)

# ── Data ──────────────────────────────────────────────────────────────────────
with st.spinner(f"Loading sentiment data for {competitor}…"):
    timeline_df = build_timeline(competitor, months=months)

if timeline_df.empty:
    st.warning(
        "No processed data found for this competitor. "
        "Run `python ingestion/run_ingestion.py` then `python pipeline/run_pipeline.py` first."
    )
    st.stop()

# ── KPI row ───────────────────────────────────────────────────────────────────
overall_sent = float(timeline_df["avg_sentiment"].mean())
latest_sent = float(timeline_df["avg_sentiment"].iloc[-1])
delta_sent = (
    float(timeline_df["avg_sentiment"].iloc[-1] - timeline_df["avg_sentiment"].iloc[0])
    if len(timeline_df) > 1
    else 0.0
)
total_reviews = int(timeline_df["review_count"].sum())
n_events = int(timeline_df["top_event"].notna().sum())


def _sentiment_label(v: float) -> str:
    if v >= 0.3:
        return "Positive"
    if v >= 0.0:
        return "Neutral"
    if v >= -0.3:
        return "Slightly negative"
    return "Negative"


kpi_cols = st.columns(4)
kpi_data = [
    ("Overall Sentiment", f"{overall_sent:+.3f}", _sentiment_label(overall_sent)),
    ("Latest Month", f"{latest_sent:+.3f}", _sentiment_label(latest_sent)),
    (
        "Trend (first→last)",
        f"{delta_sent:+.3f}",
        "improving" if delta_sent > 0 else "declining",
    ),
    ("Reviews Analyzed", f"{total_reviews:,}", f"{n_events} news events marked"),
]
for col, (label, value, sub) in zip(kpi_cols, kpi_data):
    with col:
        st.markdown(
            f"""
            <div class="rs-kpi">
                <div class="rs-kpi-label">{label}</div>
                <div class="rs-kpi-value">{value}</div>
                <div class="rs-kpi-sub">{sub}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

st.markdown("<div style='height:24px;'></div>", unsafe_allow_html=True)

# ── Timeline chart ────────────────────────────────────────────────────────────
render_sentiment_timeline(
    timeline_df,
    title=f"{competitor} — Sentiment Over Time",
)

# ── News events table ─────────────────────────────────────────────────────────
event_df = timeline_df[timeline_df["top_event"].notna()].copy()
if not event_df.empty:
    st.markdown(
        "<div style='font-family:\"Plus Jakarta Sans\",sans-serif;font-size:12px;"
        "font-weight:600;color:#003366;margin:24px 0 12px;letter-spacing:2px;"
        "text-transform:uppercase;'>News Events Detected</div>",
        unsafe_allow_html=True,
    )

    rows_html = ""
    for _, row in event_df.iterrows():
        sent = float(row["avg_sentiment"])
        sent_color = "#27B97C" if sent >= 0 else "#E03448"
        rows_html += f"""
            <tr style='border-bottom:1px solid #F0F4F8;'>
                <td style='padding:10px 14px;font-weight:600;color:#003366;
                           white-space:nowrap;'>{row['month']}</td>
                <td style='padding:10px 14px;color:#374151;line-height:1.5;'>
                    {row['top_event']}
                </td>
                <td style='padding:10px 14px;font-weight:600;color:{sent_color};
                           text-align:right;white-space:nowrap;'>{sent:+.3f}</td>
            </tr>
        """

    st.html(
        f"""
        <table style='width:100%;border-collapse:collapse;
                      font-family:"Plus Jakarta Sans",sans-serif;font-size:13px;
                      background:#ffffff;border-radius:10px;overflow:hidden;
                      box-shadow:0 1px 4px rgba(0,51,102,.08);'>
            <thead>
                <tr style='background:#003366;'>
                    <th style='padding:10px 14px;text-align:left;color:rgba(255,255,255,0.8);
                               font-size:11px;letter-spacing:2px;text-transform:uppercase;
                               font-weight:500;white-space:nowrap;'>Month</th>
                    <th style='padding:10px 14px;text-align:left;color:rgba(255,255,255,0.8);
                               font-size:11px;letter-spacing:2px;text-transform:uppercase;
                               font-weight:500;'>Top News Headline</th>
                    <th style='padding:10px 14px;text-align:right;color:rgba(255,255,255,0.8);
                               font-size:11px;letter-spacing:2px;text-transform:uppercase;
                               font-weight:500;white-space:nowrap;'>Month Sentiment</th>
                </tr>
            </thead>
            <tbody>{rows_html}</tbody>
        </table>
        """
    )
