"""Home page — RivalSense overview."""

import streamlit as st

st.markdown(
    """
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600&family=Fraunces:ital,opsz,wght@0,9..144,300;1,9..144,300&display=swap" rel="stylesheet">
    <style>
    /* Remove default padding/margin Streamlit adds around page_link elements */
    .rs-nav-link a {
        text-decoration: none !important;
    }
    </style>
    <div style="background:#003366;padding:48px;border-radius:12px;margin-bottom:32px;
    background-image:linear-gradient(rgba(255,255,255,.025) 1px,transparent 1px),
    linear-gradient(90deg,rgba(255,255,255,.025) 1px,transparent 1px);
    background-size:48px 48px;">
        <h1 style="font-family:'Fraunces',Georgia,serif;font-weight:300;color:#ffffff;
        font-size:40px;margin:0 0 12px;">
            Competitive intelligence that <em style="color:#C8982A;">decides.</em>
        </h1>
        <p style="color:rgba(255,255,255,0.6);font-size:15px;margin:0;
                  font-family:'Plus Jakarta Sans',sans-serif;line-height:1.7;">
            Six modules. Public data. Actionable signals for your sales team.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

modules = [
    (
        "🎯", "Pain Point Radar",
        "Rank competitor pain points by severity and trend direction.",
        "ui/pages/1_pain_point_radar.py",
    ),
    (
        "📈", "Sentiment Timeline",
        "18-month competitor sentiment with news event overlay.",
        "ui/pages/2_sentiment_timeline.py",
    ),
    (
        "💡", "Feature Wish Miner",
        "Cluster feature requests and flag your product's advantages.",
        "ui/pages/3_feature_wish_miner.py",
    ),
    (
        "🃏", "Battlecard Generator",
        "AI-powered sales battlecards from live competitor data.",
        "ui/pages/4_battlecard_generator.py",
    ),
    (
        "🔔", "Trigger Alerts",
        "Detect vulnerability signals and draft outreach instantly.",
        "ui/pages/5_trigger_alerts.py",
    ),
    (
        "🔥", "Hot Prospect Finder",
        "Surface Reddit users actively switching away from competitors.",
        "ui/pages/6_hot_prospect_radar.py",
    ),
]

cols = st.columns(3)
for i, (icon, name, desc, page_path) in enumerate(modules):
    with cols[i % 3]:
        st.markdown(
            f"""
            <div style="background:#ffffff;border-radius:12px;
                        padding:24px 24px 12px;
                        border-top:3px solid #C8982A;margin-bottom:4px;
                        box-shadow:0 1px 4px rgba(0,51,102,.08);">
                <div style="font-size:24px;margin-bottom:8px;">{icon}</div>
                <div style="font-family:'Plus Jakarta Sans',sans-serif;font-weight:600;
                            font-size:14px;color:#003366;margin-bottom:6px;">{name}</div>
                <div style="font-family:'Plus Jakarta Sans',sans-serif;font-size:13px;
                            color:#6B7280;line-height:1.6;">{desc}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.page_link(page_path, label=f"Open {name} →", use_container_width=True)
        st.markdown("<div style='margin-bottom:20px;'></div>", unsafe_allow_html=True)
