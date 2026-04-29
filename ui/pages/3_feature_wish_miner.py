"""Page 3 — Feature Wish Miner (M03)."""

import streamlit as st

from config import OWN_FEATURES
from modules.feature_wish_miner import extract_wishes, flag_own_features
from ui.components.competitor_selector import render_competitor_selector

st.set_page_config(page_title="Feature Wish Miner · RivalSense", layout="wide")

st.title("Feature Wish Miner")
st.caption("Competitor feature requests clustered and matched against your product.")

competitor = render_competitor_selector(key="m03_competitor")

# TODO Sprint 3 — Day 8: render wish table with filter toggle
st.info("Sprint 3 — Day 8: implement wish table rendering here.")
