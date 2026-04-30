"""Page 5 — Trigger Alerts (M05)."""

import streamlit as st

from ui.components.competitor_selector import render_competitor_selector

st.markdown("## Trigger Alerts")
st.caption("Real-time competitor vulnerability signals with pre-drafted outreach.")
render_competitor_selector(key="m05_competitor")
st.info("Sprint 5 — Day 12: implement alert feed rendering here.")
