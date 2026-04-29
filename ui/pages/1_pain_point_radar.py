"""Page 1 — Pain Point Radar (M01)."""

import streamlit as st

from modules.pain_point_radar import get_pain_points
from ui.components.charts import render_bar_chart
from ui.components.competitor_selector import render_competitor_selector

st.set_page_config(page_title="Pain Point Radar · RivalSense", layout="wide")

st.title("Pain Point Radar")
st.caption("Top competitor pain points ranked by severity and trend direction.")

competitor = render_competitor_selector(key="m01_competitor")

# TODO Sprint 2 — Day 4: render bar chart and trend indicators
st.info("Sprint 2 — Day 4: implement chart rendering here.")
