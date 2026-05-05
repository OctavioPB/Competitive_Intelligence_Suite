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

_mode_badge = (
    '<span class="rs-mode-badge rs-mode-demo">DEMO DATA</span>'
    if DEMO_MODE
    else '<span class="rs-mode-badge rs-mode-live">LIVE DATA</span>'
)

# ── Global CSS + Fixed Navigation Bar ─────────────────────────────────────────
# To use an image logo: place your file at ui/static/logo.png and replace the
# <a class="rs-topnav-logo"> block with:
#   <img src="app/static/logo.png" style="height:32px;" alt="RivalSense">
st.html(
    f"""
    <link
      href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700&family=Fraunces:ital,opsz,wght@0,9..144,300;0,9..144,400;1,9..144,300;1,9..144,400&display=swap"
      rel="stylesheet"
    >
    <style>
    /* === Page background === */
    html, body, .stApp,
    [data-testid="stApp"],
    [data-testid="stAppViewContainer"],
    [data-testid="stMain"],
    [data-testid="stMainBlockContainer"] {{
        background-color: #F4F6F9 !important;
    }}
    .block-container {{ padding-top: 1.5rem !important; }}

    /* === Hide Streamlit's native header and sidebar collapse toggle === */
    header[data-testid="stHeader"] {{ display: none !important; }}
    [data-testid="stSidebarCollapseButton"] {{ display: none !important; }}
    [data-testid="stToolbar"] {{ display: none !important; }}

    /* === Push main content below the fixed nav bar === */
    [data-testid="stMain"] {{
        padding-top: 60px !important;
    }}

    /* === Sidebar — anchored below nav bar === */
    section[data-testid="stSidebar"] {{
        top: 60px !important;
        height: calc(100vh - 60px) !important;
        background-color: #003366 !important;
    }}
    section[data-testid="stSidebar"] > div,
    section[data-testid="stSidebar"] > div > div,
    section[data-testid="stSidebar"] > div > div > div {{
        background-color: #003366 !important;
    }}

    /* Sidebar text defaults */
    section[data-testid="stSidebar"] p,
    section[data-testid="stSidebar"] span,
    section[data-testid="stSidebar"] div,
    section[data-testid="stSidebar"] label {{
        color: rgba(255,255,255,0.75);
    }}

    /* Nav buttons */
    section[data-testid="stSidebar"] button {{
        background: transparent !important;
        border: none !important;
        color: rgba(255,255,255,0.70) !important;
    }}
    section[data-testid="stSidebar"] button p,
    section[data-testid="stSidebar"] button span {{
        color: rgba(255,255,255,0.70) !important;
    }}

    /* Active nav item */
    section[data-testid="stSidebar"] [aria-current="page"] button {{
        background: rgba(200,152,42,0.12) !important;
        border-left: 3px solid #C8982A !important;
        border-radius: 0 6px 6px 0 !important;
    }}
    section[data-testid="stSidebar"] [aria-current="page"] button p,
    section[data-testid="stSidebar"] [aria-current="page"] button span {{
        color: #C8982A !important;
    }}

    /* Nav section header label */
    section[data-testid="stSidebar"] [data-testid="stSidebarNavSections"] span {{
        color: rgba(255,255,255,0.40) !important;
        font-size: 10px !important;
        letter-spacing: 2px !important;
        text-transform: uppercase !important;
    }}

    /* Selectbox white text fix */
    [data-testid="stSelectbox"] * {{ color: #ffffff !important; }}
    [data-testid="stSelectbox"] label,
    [data-testid="stSelectbox"] label * {{ color: #1C1C2E !important; }}
    [data-testid="stSelectbox"] svg {{ fill: #ffffff !important; }}

    /* ── Fixed Top Navigation Bar ── */
    .rs-topnav {{
        position: fixed;
        top: 0; left: 0; right: 0;
        height: 60px;
        background: #003366;
        z-index: 999990;
        display: flex;
        align-items: center;
        padding: 0 28px;
        gap: 20px;
        box-shadow: 0 1px 0 rgba(255,255,255,0.07), 0 2px 16px rgba(0,0,0,0.20);
        font-family: 'Plus Jakarta Sans', sans-serif;
    }}
    .rs-topnav-logo {{
        font-family: 'Fraunces', Georgia, serif;
        font-size: 20px;
        font-weight: 300;
        text-decoration: none;
        white-space: nowrap;
        margin-right: 4px;
        flex-shrink: 0;
    }}
    .rs-mode-badge {{
        font-family: 'Plus Jakarta Sans', sans-serif;
        font-size: 10px;
        letter-spacing: 2px;
        text-transform: uppercase;
        padding: 3px 10px;
        border-radius: 20px;
        white-space: nowrap;
        flex-shrink: 0;
    }}
    .rs-mode-demo {{ background: #FEF0E6; color: #7A3800; }}
    .rs-mode-live {{ background: #E0F7EF; color: #0D5C3A; }}
    .rs-topnav-sep {{
        width: 1px;
        height: 22px;
        background: rgba(255,255,255,0.14);
        flex-shrink: 0;
    }}
    .rs-topnav-links {{
        display: flex;
        gap: 2px;
        align-items: center;
        flex: 1;
        justify-content: flex-end;
    }}
    .rs-topnav-links a {{
        font-size: 12px;
        font-weight: 500;
        color: #C8982A;
        text-decoration: none;
        padding: 6px 12px;
        border-radius: 6px;
        white-space: nowrap;
        letter-spacing: 0.2px;
        transition: color 0.15s ease, background 0.15s ease;
    }}
    .rs-topnav-links a:hover {{
        color: #E8B840;
        background: rgba(200,152,42,0.12);
    }}

    /* ── Fixed Full-Width Footer ── */
    .rs-footer {{
        position: fixed;
        bottom: 0; left: 0; right: 0;
        height: 52px;
        padding: 0 32px;
        background: #003366;
        border-top: 1px solid rgba(255,255,255,0.10);
        display: flex;
        align-items: center;
        justify-content: space-between;
        z-index: 99989;
        font-family: 'Plus Jakarta Sans', sans-serif;
        box-shadow: 0 -1px 8px rgba(0,0,0,0.15);
    }}
    .rs-footer-logo {{
        font-family: 'Fraunces', Georgia, serif;
        font-size: 15px;
        font-weight: 300;
        text-decoration: none;
        flex-shrink: 0;
    }}
    .rs-footer-center {{
        font-size: 12px;
        color: rgba(255,255,255,0.30);
        text-align: center;
        flex: 1;
        letter-spacing: 0.2px;
    }}
    .rs-footer-right {{
        font-size: 11px;
        color: rgba(255,255,255,0.28);
        text-align: right;
        white-space: nowrap;
        flex-shrink: 0;
    }}
    /* Prevent page content from sliding under the fixed footer */
    [data-testid="stMainBlockContainer"] {{
        padding-bottom: 68px !important;
    }}
    </style>

    <nav class="rs-topnav">
      <a class="rs-topnav-logo" href="/" target="_top">
        <span style="color:#ffffff;">OP</span><em style="color:#C8982A;font-style:italic;">B</em>
      </a>
      {_mode_badge}
      <div class="rs-topnav-sep"></div>
      <div class="rs-topnav-links">
        <a href="/" target="_top">Home</a>
        <a href="/pain-point-radar" target="_top">Pain Radar</a>
        <a href="/sentiment-timeline" target="_top">Sentiment</a>
        <a href="/feature-wish-miner" target="_top">Wish Miner</a>
        <a href="/battlecard-generator" target="_top">Battlecard</a>
        <a href="/trigger-alerts" target="_top">Alerts</a>
        <a href="/hot-prospect-finder" target="_top">Prospects</a>
      </div>
    </nav>
    """
)

# ── Sidebar brand header ───────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(
        """
        <div style="padding:20px 4px 4px;">
            <div style="font-family:'Fraunces',Georgia,serif;font-size:22px;font-weight:300;margin-bottom:8px;">
                <span style="color:#ffffff;">Rival</span
                ><em style="color:#C8982A;font-style:italic;">Sense</em>
            </div>
            <div style="font-size:9px;letter-spacing:3px;text-transform:uppercase;
                        color:rgba(255,255,255,0.35);margin-bottom:12px;">
                Competitive Intelligence
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div style="height:1px;background:rgba(255,255,255,.1);margin:0 0 16px;"></div>',
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

# ── Static Footer ─────────────────────────────────────────────────────────────
st.html(
    """
    <div class="rs-footer">
      <a class="rs-footer-logo" href="/" target="_top">
        <span style="color:#ffffff;">OP</span><em style="color:#C8982A;font-style:italic;">B</em>
      </a>
      <div class="rs-footer-center">
        Competitive Intelligence Platform &mdash; turning competitor signals into revenue opportunities.
      </div>
      <div class="rs-footer-right">
        &copy; 2026 Octavio Perez Bravo
      </div>
    </div>
    """
)
