"""Page 6 — Hot Prospect Finder (M06)."""

import streamlit as st

from modules.hot_prospect_finder import scan_reddit
from ui.components.competitor_selector import render_competitor_selector

st.set_page_config(page_title="Hot Prospect Finder · RivalSense", layout="wide")

st.title("Hot Prospect Finder")
st.caption("Reddit users actively switching away from competitors — ranked by urgency.")

competitor = render_competitor_selector(key="m06_competitor")

# TODO Sprint 5 — Day 13: lead table, urgency indicators, CRM export button
st.info("Sprint 5 — Day 13: implement lead table and export here.")
