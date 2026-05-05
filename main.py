"""RivalSense — Streamlit entry point and navigation controller."""

import os

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

DEMO_MODE: bool = os.getenv("DEMO_MODE", "false").lower() == "true"

st.set_page_config(
    page_title="RivalSense",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Global CSS — use st.html() which bypasses Streamlit's HTML sanitizer
# (st.markdown unsafe_allow_html strips <style> tags in Streamlit 1.44+)
st.html(
    """
    <link
      href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700&family=Fraunces:ital,opsz,wght@0,9..144,300;0,9..144,400;1,9..144,300;1,9..144,400&display=swap"
      rel="stylesheet"
    >
    <style>
    /* Page background */
    html, body, .stApp,
    [data-testid="stApp"],
    [data-testid="stAppViewContainer"],
    [data-testid="stMain"],
    [data-testid="stMainBlockContainer"] {
        background-color: #F4F6F9 !important;
    }
    .block-container { padding-top: 1.5rem !important; }
    header[data-testid="stHeader"] {
        background-color: #F4F6F9 !important;
        box-shadow: none !important;
    }

    /* Sidebar background — target section + nested wrappers */
    section[data-testid="stSidebar"],
    section[data-testid="stSidebar"] > div,
    section[data-testid="stSidebar"] > div > div,
    section[data-testid="stSidebar"] > div > div > div {
        background-color: #003366 !important;
    }

    /* Sidebar text defaults */
    section[data-testid="stSidebar"] p,
    section[data-testid="stSidebar"] span,
    section[data-testid="stSidebar"] div,
    section[data-testid="stSidebar"] label {
        color: rgba(255,255,255,0.75);
    }

    /* Nav buttons */
    section[data-testid="stSidebar"] button {
        background: transparent !important;
        border: none !important;
        color: rgba(255,255,255,0.70) !important;
    }
    section[data-testid="stSidebar"] button p,
    section[data-testid="stSidebar"] button span {
        color: rgba(255,255,255,0.70) !important;
    }

    /* Active nav item */
    section[data-testid="stSidebar"] [aria-current="page"] button {
        background: rgba(200,152,42,0.12) !important;
        border-left: 3px solid #C8982A !important;
        border-radius: 0 6px 6px 0 !important;
    }
    section[data-testid="stSidebar"] [aria-current="page"] button p,
    section[data-testid="stSidebar"] [aria-current="page"] button span {
        color: #C8982A !important;
    }

    /* Nav section header label */
    section[data-testid="stSidebar"] [data-testid="stSidebarNavSections"] span {
        color: rgba(255,255,255,0.40) !important;
        font-size: 10px !important;
        letter-spacing: 2px !important;
        text-transform: uppercase !important;
    }

    /* Selectbox: the input area has navy secondaryBackgroundColor from the theme.
       Make all content inside white, then restore the label (on white page bg) to dark. */
    [data-testid="stSelectbox"] * {
        color: #ffffff !important;
    }
    [data-testid="stSelectbox"] label,
    [data-testid="stSelectbox"] label * {
        color: #1C1C2E !important;
    }
    [data-testid="stSelectbox"] svg {
        fill: #ffffff !important;
    }
    </style>
    """
)

# ── Sidebar brand header ──────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(
        """
        <div style="padding:20px 4px 4px;">
            <div style="font-family:'Fraunces',Georgia,serif;font-size:22px;font-weight:300;margin-bottom:8px;">
                <span style="color:#ffffff;">Rival</span
                ><em style="color:#C8982A;font-style:italic;">Sense</em>
            </div>
            <div style="font-size:9px;letter-spacing:3px;text-transform:uppercase;
                        color:rgba(255,255,255,0.35);margin-bottom:16px;">
                Competitive Intelligence
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if DEMO_MODE:
        st.markdown(
            '<span style="background:#FEF0E6;color:#7A3800;font-size:10px;'
            'letter-spacing:3px;text-transform:uppercase;padding:4px 12px;'
            'border-radius:20px;">DEMO DATA</span>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<span style="background:#E0F7EF;color:#0D5C3A;font-size:10px;'
            'letter-spacing:3px;text-transform:uppercase;padding:4px 12px;'
            'border-radius:20px;">LIVE DATA</span>',
            unsafe_allow_html=True,
        )

    st.markdown(
        '<div style="height:1px;background:rgba(255,255,255,.1);margin:16px 0;"></div>',
        unsafe_allow_html=True,
    )

# ── Page navigation ───────────────────────────────────────────────────────────
home = st.Page("ui/pages/0_home.py", title="Home", default=True)
pain_radar = st.Page("ui/pages/1_pain_point_radar.py", title="Pain Point Radar", url_path="pain-point-radar")
sentiment = st.Page("ui/pages/2_sentiment_timeline.py", title="Sentiment Timeline", url_path="sentiment-timeline")
wish_miner = st.Page("ui/pages/3_feature_wish_miner.py", title="Feature Wish Miner", url_path="feature-wish-miner")
battlecard = st.Page("ui/pages/4_battlecard_generator.py", title="Battlecard Generator", url_path="battlecard-generator")
alerts = st.Page("ui/pages/5_trigger_alerts.py", title="Trigger Alerts", url_path="trigger-alerts")
prospects = st.Page("ui/pages/6_hot_prospect_radar.py", title="Hot Prospect Finder", url_path="hot-prospect-finder")

pg = st.navigation(
    {
        "": [home],
        "Intelligence Modules": [pain_radar, sentiment, wish_miner, battlecard, alerts, prospects],
    }
)
pg.run()
