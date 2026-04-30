"""Page 4 — Battlecard Generator (M04)."""

import streamlit as st

from ui.components.competitor_selector import render_competitor_selector

st.markdown("## Battlecard Generator")
st.caption("AI-powered sales battlecards generated from live competitor intelligence.")
render_competitor_selector(key="m04_competitor")
st.info("Sprint 4 — Day 10: implement battlecard rendering and PDF export here.")
