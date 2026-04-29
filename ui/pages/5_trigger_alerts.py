"""Page 5 — Trigger Alerts (M05)."""

import streamlit as st

from modules.trigger_alerts import check_triggers
from config import COMPETITOR_NAMES

st.set_page_config(page_title="Trigger Alerts · RivalSense", layout="wide")

st.title("Trigger Alerts")
st.caption("Real-time competitor vulnerability signals with pre-drafted outreach.")

# TODO Sprint 5 — Day 12: alert feed, simulate bad week button
st.info("Sprint 5 — Day 12: implement alert feed rendering here.")
