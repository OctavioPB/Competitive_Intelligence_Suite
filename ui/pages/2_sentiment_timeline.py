"""Page 2 — Sentiment Timeline (M02)."""

import streamlit as st

from ui.components.competitor_selector import render_competitor_selector

st.markdown("## Sentiment Timeline")
st.caption("Monthly competitor sentiment with news event overlay.")
render_competitor_selector(key="m02_competitor")
st.info("Sprint 3 — Day 7: implement timeline rendering here.")
