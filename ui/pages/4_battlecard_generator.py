"""Page 4 — Battlecard Generator (M04)."""

import streamlit as st

from modules.battlecard_generator import generate_battlecard
from ui.components.competitor_selector import render_competitor_selector

st.set_page_config(page_title="Battlecard Generator · RivalSense", layout="wide")

st.title("Battlecard Generator")
st.caption("AI-powered sales battlecards generated from live competitor intelligence.")

competitor = render_competitor_selector(key="m04_competitor")

# TODO Sprint 4 — Day 10: generate button, spinner, rendered card, PDF download
st.info("Sprint 4 — Day 10: implement battlecard rendering and PDF export here.")
