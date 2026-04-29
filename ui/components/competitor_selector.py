"""Reusable competitor selector widget — single source of truth for all pages."""

import streamlit as st

from config import COMPETITOR_NAMES


def render_competitor_selector(key: str = "competitor") -> str:
    """Render a selectbox populated from config.COMPETITORS.

    Persists the selection in st.session_state under the given key so the
    choice survives page navigation.

    Args:
        key: Session state key to store the selection under.

    Returns:
        The currently selected competitor name string.
    """
    return st.selectbox(
        "Select competitor",
        options=COMPETITOR_NAMES,
        key=key,
    )
