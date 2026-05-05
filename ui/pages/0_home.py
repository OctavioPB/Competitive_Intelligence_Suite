"""Home page — RivalSense overview."""

import streamlit as st

st.html("""
<link
  href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600&family=Fraunces:ital,opsz,wght@0,9..144,300;1,9..144,300&display=swap"
  rel="stylesheet"
>
<style>
.rs-hero {
    background: #003366;
    background-image:
        linear-gradient(rgba(255,255,255,.025) 1px, transparent 1px),
        linear-gradient(90deg, rgba(255,255,255,.025) 1px, transparent 1px);
    background-size: 48px 48px;
    border-radius: 12px;
    padding: 48px;
    margin-bottom: 32px;
}
.rs-hero h1 {
    font-family: 'Fraunces', Georgia, serif;
    font-weight: 300;
    color: #ffffff;
    font-size: 40px;
    margin: 0 0 12px;
}
.rs-hero p {
    color: rgba(255,255,255,0.6);
    font-size: 15px;
    margin: 0;
    font-family: 'Plus Jakarta Sans', sans-serif;
    line-height: 1.7;
}
.rs-card {
    background: #ffffff;
    border-radius: 12px;
    border-top: 3px solid #C8982A;
    box-shadow: 0 1px 4px rgba(0,51,102,.08);
    margin-bottom: 20px;
    overflow: hidden;
}
.rs-card-body {
    padding: 24px 24px 20px;
}
.rs-card-title {
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-weight: 600;
    font-size: 14px;
    color: #003366;
    margin-bottom: 6px;
}
.rs-card-desc {
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-size: 13px;
    color: #6B7280;
    line-height: 1.6;
}
.rs-card-btn {
    display: block;
    background: #003366;
    color: #ffffff !important;
    text-align: center;
    padding: 12px 20px;
    text-decoration: none !important;
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-size: 13px;
    font-weight: 500;
    transition: background 0.15s ease;
}
.rs-card-btn:hover {
    background: #004c99;
    color: #ffffff !important;
    text-decoration: none !important;
}
</style>

<div class="rs-hero">
    <h1>Competitive intelligence that <em style="color:#C8982A;">decides.</em></h1>
    <p>Six modules. Public data. Actionable signals for your sales team.</p>
</div>
""")

modules = [
    (
        "Pain Point Radar",
        "Rank competitor pain points by severity and trend direction.",
        "pain-point-radar",
    ),
    (
        "Sentiment Timeline",
        "18-month competitor sentiment with news event overlay.",
        "sentiment-timeline",
    ),
    (
        "Feature Wish Miner",
        "Cluster feature requests and flag your product's advantages.",
        "feature-wish-miner",
    ),
    (
        "Battlecard Generator",
        "AI-powered sales battlecards from live competitor data.",
        "battlecard-generator",
    ),
    (
        "Trigger Alerts",
        "Detect vulnerability signals and draft outreach instantly.",
        "trigger-alerts",
    ),
    (
        "Hot Prospect Finder",
        "Surface Reddit users actively switching away from competitors.",
        "hot-prospect-finder",
    ),
]

cols = st.columns(3)
for i, (name, desc, url_path) in enumerate(modules):
    with cols[i % 3]:
        st.html(f"""
        <div class="rs-card">
            <div class="rs-card-body">
                <div class="rs-card-title">{name}</div>
                <div class="rs-card-desc">{desc}</div>
            </div>
            <a class="rs-card-btn" href="/{url_path}" target="_top">Open {name}</a>
        </div>
        """)
