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

# ── Global CSS ────────────────────────────────────────────────────────────────
st.markdown(
    """
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700&family=Fraunces:ital,opsz,wght@0,9..144,300;0,9..144,400;1,9..144,300;1,9..144,400&display=swap" rel="stylesheet">
    <style>
    /* ── Sidebar background ────────────────────────────── */
    section[data-testid="stSidebar"] {
        background-color: #003366;
    }

    /* ── Our injected markdown (logo, badge, divider) ──── */
    section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
    section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] div,
    section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] span {
        color: rgba(255,255,255,0.75) !important;
    }

    /* ── Streamlit nav links — white text on dark blue ─── */
    section[data-testid="stSidebar"] [data-testid="stSidebarNavItems"] button,
    section[data-testid="stSidebar"] [data-testid="stSidebarNavItems"] button p,
    section[data-testid="stSidebar"] [data-testid="stSidebarNavItems"] button span {
        color: rgba(255,255,255,0.70) !important;
    }

    /* Active nav item — gold */
    section[data-testid="stSidebar"] [data-testid="stSidebarNavItems"] button[kind="secondary"],
    section[data-testid="stSidebar"] [data-testid="stSidebarNavItems"] [aria-current="page"] button {
        color: #C8982A !important;
        border-left: 2px solid #C8982A;
        background: rgba(200,152,42,0.08) !important;
    }

    /* Nav group label (section header "Intelligence Modules") */
    section[data-testid="stSidebar"] [data-testid="stSidebarNavItems"] span {
        color: rgba(255,255,255,0.40) !important;
        font-size: 10px;
        letter-spacing: 2px;
        text-transform: uppercase;
    }

    /* ── Page background ───────────────────────────────── */
    .stApp { background-color: #F4F6F9; }
    .block-container { padding-top: 1.5rem !important; }
    header[data-testid="stHeader"] { background: transparent; }
    </style>
    """,
    unsafe_allow_html=True,
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
            'border-radius:20px;">● DEMO DATA</span>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<span style="background:#E0F7EF;color:#0D5C3A;font-size:10px;'
            'letter-spacing:3px;text-transform:uppercase;padding:4px 12px;'
            'border-radius:20px;">● LIVE DATA</span>',
            unsafe_allow_html=True,
        )

    st.markdown(
        '<div style="height:1px;background:rgba(255,255,255,.1);margin:16px 0;"></div>',
        unsafe_allow_html=True,
    )

# ── Page navigation ───────────────────────────────────────────────────────────
home = st.Page("ui/pages/0_home.py", title="Home", icon="🏠", default=True)
pain_radar = st.Page("ui/pages/1_pain_point_radar.py", title="Pain Point Radar", icon="🎯")
sentiment = st.Page("ui/pages/2_sentiment_timeline.py", title="Sentiment Timeline", icon="📈")
wish_miner = st.Page("ui/pages/3_feature_wish_miner.py", title="Feature Wish Miner", icon="💡")
battlecard = st.Page("ui/pages/4_battlecard_generator.py", title="Battlecard Generator", icon="🃏")
alerts = st.Page("ui/pages/5_trigger_alerts.py", title="Trigger Alerts", icon="🔔")
prospects = st.Page("ui/pages/6_hot_prospect_radar.py", title="Hot Prospect Finder", icon="🔥")

pg = st.navigation(
    {
        "": [home],
        "Intelligence Modules": [pain_radar, sentiment, wish_miner, battlecard, alerts, prospects],
    }
)
pg.run()
