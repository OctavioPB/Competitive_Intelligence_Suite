"""Page 5 — Trigger Alerts (M05)."""

from datetime import datetime

import streamlit as st

from config import COMPETITOR_NAMES
from modules.trigger_alerts import Alert, check_triggers, generate_outreach

_BRAND_CSS = """
<link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600&family=Fraunces:ital,opsz,wght@0,9..144,300;1,9..144,300&display=swap" rel="stylesheet">
<style>
.rs-alert-card {
    background: #ffffff;
    border-radius: 10px;
    padding: 18px 22px;
    margin-bottom: 14px;
    box-shadow: 0 1px 4px rgba(0,51,102,.08);
    border-left: 4px solid #003366;
}
.rs-alert-card.sentiment_drop { border-left-color: #E03448; }
.rs-alert-card.negative_news  { border-left-color: #F07020; }
.rs-alert-card.review_spike   { border-left-color: #C8982A; }
.rs-badge {
    display: inline-block;
    font-size: 10px;
    letter-spacing: 2px;
    text-transform: uppercase;
    padding: 3px 10px;
    border-radius: 20px;
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-weight: 600;
}
.rs-badge-drop     { background:#FDE8EB; color:#7A0017; }
.rs-badge-news     { background:#FEF0E6; color:#7A3800; }
.rs-badge-spike    { background:#FEF8EC; color:#3D2A00; }
</style>
"""

st.markdown(_BRAND_CSS, unsafe_allow_html=True)

# ── Hero ──────────────────────────────────────────────────────────────────────
st.markdown(
    """
    <div style="background:#003366;padding:32px 40px;border-radius:12px;margin-bottom:28px;
    background-image:linear-gradient(rgba(255,255,255,.025) 1px,transparent 1px),
    linear-gradient(90deg,rgba(255,255,255,.025) 1px,transparent 1px);
    background-size:48px 48px;">
        <div style="font-family:'Fraunces',Georgia,serif;font-weight:300;
                    color:#ffffff;font-size:28px;margin:0 0 8px;">
            🔔 Trigger Alerts
        </div>
        <div style="color:rgba(255,255,255,0.6);font-size:14px;
                    font-family:'Plus Jakarta Sans',sans-serif;line-height:1.6;">
            Real-time competitor vulnerability signals — sentiment drops, negative news,
            and review spikes — with pre-drafted outreach ready to send.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ── Demo bad-week fixture ─────────────────────────────────────────────────────

def _demo_alerts() -> list[Alert]:
    ts = datetime(2025, 12, 27, 9, 0, 0)
    return [
        Alert(
            trigger_type="sentiment_drop",
            competitor="Salesforce",
            evidence_summary="Avg sentiment delta -0.71 in last 7 days (threshold: -0.5)",
            timestamp=ts,
            outreach_draft=(
                "Hi [Name],\n\n"
                "Salesforce has been receiving significantly more negative feedback this week — "
                "many customers cite cost and support response times. If your team is feeling "
                "that friction, we'd love to show you how we compare.\n\n"
                "Open to a quick 15-minute call?\n\nBest,"
            ),
        ),
        Alert(
            trigger_type="negative_news",
            competitor="Salesforce",
            evidence_summary=(
                "News article with keywords ['outage'] on 2025-12-26: "
                '"Major Salesforce outage affecting thousands of enterprise customers..."'
            ),
            timestamp=ts,
            outreach_draft=(
                "Hi [Name],\n\n"
                "I saw the news around Salesforce's outage this week — moments like these "
                "often prompt teams to review their CRM vendor. We've helped several "
                "Salesforce customers transition smoothly and I'd be happy to share how.\n\n"
                "Worth a brief conversation?\n\nBest,"
            ),
        ),
        Alert(
            trigger_type="review_spike",
            competitor="HubSpot",
            evidence_summary="42 reviews in last 7 days vs expected 18.0 (2× spike threshold)",
            timestamp=ts,
            outreach_draft=(
                "Hi [Name],\n\n"
                "There's been an unusual spike in HubSpot customer complaints this week — "
                "typically a sign of broader platform friction. If your team is considering "
                "alternatives, we'd love to show you what we offer.\n\n"
                "Open to a quick call?\n\nBest,"
            ),
        ),
    ]


# ── Controls ──────────────────────────────────────────────────────────────────
ctrl_cols = st.columns([1, 1, 2])
with ctrl_cols[0]:
    scan_clicked = st.button("🔍 Scan All Competitors", use_container_width=True)
with ctrl_cols[1]:
    demo_clicked = st.button("🎭 Simulate Bad Week", use_container_width=True)

if demo_clicked:
    st.session_state["alerts"] = _demo_alerts()

if scan_clicked:
    with st.spinner("Scanning for vulnerability signals across all competitors…"):
        try:
            alerts = check_triggers(COMPETITOR_NAMES)
            st.session_state["alerts"] = alerts
        except Exception as exc:
            st.error(f"Scan failed: {exc}")

alerts: list[Alert] = st.session_state.get("alerts", [])

# ── KPI row ───────────────────────────────────────────────────────────────────
if alerts:
    n_drop = sum(1 for a in alerts if a.trigger_type == "sentiment_drop")
    n_news = sum(1 for a in alerts if a.trigger_type == "negative_news")
    n_spike = sum(1 for a in alerts if a.trigger_type == "review_spike")

    kpi_cols = st.columns(4)
    kpi_data = [
        ("Total Alerts", str(len(alerts)), "detected this scan", "#003366"),
        ("Sentiment Drops", str(n_drop), "competitors declining", "#E03448"),
        ("Negative News", str(n_news), "press events flagged", "#F07020"),
        ("Review Spikes", str(n_spike), "unusual volume detected", "#C8982A"),
    ]
    for col, (label, value, sub, border) in zip(kpi_cols, kpi_data):
        with col:
            st.markdown(
                f"""
                <div style="background:#ffffff;border-radius:10px;padding:18px 22px;
                            border-top:3px solid {border};
                            box-shadow:0 1px 4px rgba(0,51,102,.08);">
                    <div style="font-family:'Plus Jakarta Sans',sans-serif;font-size:11px;
                                letter-spacing:2px;text-transform:uppercase;
                                color:#6B7280;margin-bottom:4px;">{label}</div>
                    <div style="font-family:'Fraunces',Georgia,serif;font-size:28px;
                                font-weight:300;color:#003366;">{value}</div>
                    <div style="font-family:'Plus Jakarta Sans',sans-serif;font-size:12px;
                                color:#6B7280;margin-top:2px;">{sub}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
    st.markdown("<div style='height:24px;'></div>", unsafe_allow_html=True)

# ── Alert feed ────────────────────────────────────────────────────────────────
if not alerts:
    st.info(
        "No alerts yet. Click **Scan All Competitors** to check for live signals, "
        "or **Simulate Bad Week** to preview a demo scenario."
    )
else:
    _BADGE_MAP = {
        "sentiment_drop": ("📉 Sentiment Drop", "rs-badge-drop"),
        "negative_news": ("📰 Negative News", "rs-badge-news"),
        "review_spike": ("🔔 Review Spike", "rs-badge-spike"),
    }
    _BORDER_MAP = {
        "sentiment_drop": "sentiment_drop",
        "negative_news": "negative_news",
        "review_spike": "review_spike",
    }

    # Sort by timestamp descending, show latest 10
    sorted_alerts = sorted(alerts, key=lambda a: a.timestamp, reverse=True)[:10]

    for alert in sorted_alerts:
        badge_text, badge_class = _BADGE_MAP.get(
            alert.trigger_type, (alert.trigger_type, "rs-badge-drop")
        )
        border_class = _BORDER_MAP.get(alert.trigger_type, "")
        ts_str = alert.timestamp.strftime("%Y-%m-%d %H:%M UTC")

        st.markdown(
            f"""
            <div class="rs-alert-card {border_class}">
                <div style="display:flex;justify-content:space-between;
                            align-items:flex-start;margin-bottom:10px;">
                    <span class="rs-badge {badge_class}">{badge_text}</span>
                    <span style="font-family:'Plus Jakarta Sans',sans-serif;
                                 font-size:11px;color:#9CA3AF;">{ts_str}</span>
                </div>
                <div style="font-family:'Plus Jakarta Sans',sans-serif;font-weight:600;
                            font-size:14px;color:#003366;margin-bottom:6px;">
                    {alert.competitor}
                </div>
                <div style="font-family:'Plus Jakarta Sans',sans-serif;font-size:13px;
                            color:#374151;line-height:1.5;">
                    {alert.evidence_summary}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Outreach section (per-alert state key)
        state_key = f"outreach_{alert.competitor}_{alert.trigger_type}"

        if alert.outreach_draft:
            with st.expander("View outreach draft", expanded=False):
                st.text_area(
                    "Outreach draft",
                    value=alert.outreach_draft,
                    height=180,
                    key=f"ta_{state_key}",
                    label_visibility="collapsed",
                )
        else:
            outreach_cols = st.columns([1, 1, 3])
            with outreach_cols[0]:
                if st.button("Template draft", key=f"tmpl_{state_key}", use_container_width=True):
                    alert.outreach_draft = generate_outreach(alert, llm=False)
                    st.session_state["alerts"] = sorted_alerts
                    st.rerun()
            with outreach_cols[1]:
                if st.button("✨ Claude draft", key=f"llm_{state_key}", use_container_width=True):
                    with st.spinner("Generating personalised outreach…"):
                        alert.outreach_draft = generate_outreach(alert, llm=True)
                    st.session_state["alerts"] = sorted_alerts
                    st.rerun()
