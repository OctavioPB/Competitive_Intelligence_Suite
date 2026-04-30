"""Page 6 — Hot Prospect Finder (M06)."""

import streamlit as st

from ui.components.competitor_selector import render_competitor_selector

st.markdown("## Hot Prospect Finder")
st.caption("Reddit users actively switching away from competitors — ranked by urgency.")
render_competitor_selector(key="m06_competitor")
st.info("Sprint 5 — Day 13: implement lead table and export here.")
