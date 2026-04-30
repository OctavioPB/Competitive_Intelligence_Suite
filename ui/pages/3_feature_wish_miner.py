"""Page 3 — Feature Wish Miner (M03)."""

import streamlit as st

from ui.components.competitor_selector import render_competitor_selector

st.markdown("## Feature Wish Miner")
st.caption("Competitor feature requests clustered and matched against your product.")
render_competitor_selector(key="m03_competitor")
st.info("Sprint 3 — Day 8: implement wish table rendering here.")
