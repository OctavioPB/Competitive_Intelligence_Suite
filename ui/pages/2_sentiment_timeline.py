"""Page 2 — Sentiment Timeline (M02)."""

import streamlit as st

from modules.sentiment_timeline import build_timeline
from ui.components.charts import render_line_chart
from ui.components.competitor_selector import render_competitor_selector

st.set_page_config(page_title="Sentiment Timeline · RivalSense", layout="wide")

st.title("Sentiment Timeline")
st.caption("Monthly competitor sentiment with news event overlay.")

competitor = render_competitor_selector(key="m02_competitor")

# TODO Sprint 3 — Day 7: render timeline + news markers + date slider
st.info("Sprint 3 — Day 7: implement timeline rendering here.")
