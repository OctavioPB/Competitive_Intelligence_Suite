"""RivalSense — Streamlit entry point."""

import os

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

DEMO_MODE: bool = os.getenv("DEMO_MODE", "false").lower() == "true"

st.set_page_config(
    page_title="RivalSense",
    layout="wide",
    initial_sidebar_state="expanded",
)

with st.sidebar:
    st.markdown(
        """
        <div style="font-family:'Fraunces',Georgia,serif; font-size:20px; font-weight:300; margin-bottom:4px;">
            <span style="color:#ffffff;">Rival</span
            ><em style="color:#C8982A; font-style:italic;">Sense</em>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if DEMO_MODE:
        st.markdown(
            '<span style="background:#FEF0E6;color:#7A3800;font-size:10px;'
            'letter-spacing:3px;text-transform:uppercase;padding:4px 12px;'
            'border-radius:20px;">DEMO DATA</span>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<span style="background:#E0F7EF;color:#0D5C3A;font-size:10px;'
            'letter-spacing:3px;text-transform:uppercase;padding:4px 12px;'
            'border-radius:20px;">LIVE DATA</span>',
            unsafe_allow_html=True,
        )
    st.divider()
    st.markdown(
        "Navigate using the **pages** in the sidebar above. "
        "Each module surfaces a different dimension of competitor intelligence."
    )

st.markdown(
    """
    <div style="background:#003366;padding:48px;border-radius:12px;margin-bottom:32px;
    background-image:linear-gradient(rgba(255,255,255,.025) 1px,transparent 1px),
    linear-gradient(90deg,rgba(255,255,255,.025) 1px,transparent 1px);
    background-size:48px 48px;">
        <h1 style="font-family:'Fraunces',Georgia,serif;font-weight:300;color:#ffffff;
        font-size:40px;margin:0;">
            Competitive intelligence that <em style="color:#C8982A;">decides.</em>
        </h1>
        <p style="color:rgba(255,255,255,0.6);font-size:15px;margin-top:12px;">
            Six modules. Public data. Actionable signals for your sales team.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown("Select a module from the sidebar to begin.")
