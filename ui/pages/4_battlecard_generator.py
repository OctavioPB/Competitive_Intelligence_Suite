"""Page 4 — Battlecard Generator (M04)."""

from datetime import datetime

import streamlit as st

from modules.battlecard_generator import (
    battlecard_to_markdown,
    generate_battlecard,
    load_cached_battlecard,
)
from outputs.pdf_export import _WEASYPRINT_AVAILABLE, generate_pdf_bytes
from ui.components.competitor_selector import render_competitor_selector

_BRAND_CSS = """
<link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600&family=Fraunces:ital,opsz,wght@0,9..144,300;1,9..144,300&display=swap" rel="stylesheet">
<style>
.rs-objection {
    background: #ffffff;
    border-radius: 10px;
    padding: 20px 22px;
    margin-bottom: 14px;
    box-shadow: 0 1px 4px rgba(0,51,102,.08);
    border-top: 3px solid #003366;
}
.rs-objection-title {
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-size: 13px;
    font-weight: 600;
    color: #003366;
    margin-bottom: 12px;
}
.rs-label {
    font-size: 10px;
    letter-spacing: 2px;
    text-transform: uppercase;
    color: #6B7280;
    font-family: 'Plus Jakarta Sans', sans-serif;
    margin-bottom: 3px;
}
.rs-text {
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-size: 13px;
    color: #374151;
    line-height: 1.6;
    margin-bottom: 12px;
}
.rs-quote {
    font-style: italic;
    color: #6B7280;
    font-size: 12px;
    border-left: 3px solid #E0EAF4;
    padding-left: 12px;
    line-height: 1.5;
    font-family: 'Plus Jakarta Sans', sans-serif;
}
.rs-pitch-box {
    background: #FEF8EC;
    border-left: 4px solid #C8982A;
    padding: 18px 22px;
    border-radius: 6px;
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-size: 14px;
    line-height: 1.7;
    color: #3D2A00;
    margin-bottom: 28px;
}
</style>
"""

st.markdown(_BRAND_CSS, unsafe_allow_html=True)

# ── Hero ──────────────────────────────────────────────────────────────────────
st.markdown(
    """
    <div style="background:#003366;padding:32px 40px;border-radius:12px;margin-bottom:28px;
    background-image:linear-gradient(rgba(255,255,255,.025) 1px,transparent 1px),
    linear-gradient(90deg,rgba(255,255,255,.025) 1px,transparent 1px);
    background-size:48px 48px;">
        <div style="font-family:'Fraunces',Georgia,serif;font-weight:300;
                    color:#ffffff;font-size:28px;margin:0 0 8px;">
            Battlecard Generator
        </div>
        <div style="color:rgba(255,255,255,0.6);font-size:14px;
                    font-family:'Plus Jakarta Sans',sans-serif;line-height:1.6;">
            AI-powered sales battlecards built from live competitor review data.
            Pain points, objection handlers, and feature gaps — ready for your reps.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ── Controls ──────────────────────────────────────────────────────────────────
col_sel, col_btn = st.columns([2, 1])
with col_sel:
    competitor = render_competitor_selector(key="m04_competitor")

# ── Load cached card or generate ──────────────────────────────────────────────
card_key = f"battlecard_{competitor}"

if card_key not in st.session_state:
    cached = load_cached_battlecard(competitor)
    if cached:
        st.session_state[card_key] = cached

card: dict | None = st.session_state.get(card_key)

with col_btn:
    st.markdown("<div style='height:28px;'></div>", unsafe_allow_html=True)
    btn_label = "Regenerate" if card else "Generate Battlecard"
    generate_clicked = st.button(btn_label, use_container_width=True)

if generate_clicked:
    with st.spinner(f"Claude is generating the {competitor} battlecard — this takes ~10s…"):
        try:
            card = generate_battlecard(competitor)
            st.session_state[card_key] = card
        except Exception as exc:
            st.error(f"Generation failed: {exc}")
            st.stop()

if card is None:
    st.info(
        f"No battlecard found for {competitor}. "
        "Click **Generate Battlecard** to create one using the Claude API."
    )
    st.stop()

# ── Timestamp ─────────────────────────────────────────────────────────────────
generated_at_raw = card.get("generated_at", "")
try:
    generated_at = datetime.fromisoformat(generated_at_raw).strftime("%B %d, %Y at %H:%M UTC")
except (ValueError, TypeError):
    generated_at = generated_at_raw

st.markdown(
    f"<div style='font-family:\"Plus Jakarta Sans\",sans-serif;font-size:12px;"
    f"color:#6B7280;margin-bottom:24px;'>Last generated: {generated_at}</div>",
    unsafe_allow_html=True,
)

# ── Recommended Pitch ─────────────────────────────────────────────────────────
st.markdown(
    "<div style='font-family:\"Plus Jakarta Sans\",sans-serif;font-size:12px;"
    "font-weight:600;color:#003366;margin-bottom:10px;letter-spacing:2px;"
    "text-transform:uppercase;'>Recommended Pitch</div>",
    unsafe_allow_html=True,
)
st.markdown(
    f'<div class="rs-pitch-box">{card.get("recommended_pitch", "")}</div>',
    unsafe_allow_html=True,
)

# ── Objection Handlers ────────────────────────────────────────────────────────
st.markdown(
    "<div style='font-family:\"Plus Jakarta Sans\",sans-serif;font-size:12px;"
    "font-weight:600;color:#003366;margin-bottom:14px;letter-spacing:2px;"
    "text-transform:uppercase;'>Objection Handlers</div>",
    unsafe_allow_html=True,
)

objections = card.get("objections", [])
if not objections:
    st.caption("No objections generated.")
else:
    for i, obj in enumerate(objections, 1):
        st.markdown(
            f"""
            <div class="rs-objection">
                <div class="rs-objection-title">{i}. {obj.get('objection', '')}</div>
                <div class="rs-label">Evidence</div>
                <div class="rs-text">{obj.get('evidence', '')}</div>
                <div class="rs-label">Counter</div>
                <div class="rs-text">{obj.get('counter', '')}</div>
                <div class="rs-quote">"{obj.get('proof_quote', '')}"</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

# ── Feature Gaps ──────────────────────────────────────────────────────────────
st.markdown(
    "<div style='font-family:\"Plus Jakarta Sans\",sans-serif;font-size:12px;"
    "font-weight:600;color:#003366;margin:24px 0 14px;letter-spacing:2px;"
    "text-transform:uppercase;'>Feature Gaps — We Win Here</div>",
    unsafe_allow_html=True,
)

feature_gaps = card.get("feature_gaps", [])
if not feature_gaps:
    st.caption("No feature gaps identified.")
else:
    gap_rows = ""
    for gap in feature_gaps:
        gap_rows += f"""
            <tr style='border-bottom:1px solid #F0F4F8;'>
                <td style='padding:12px 14px;font-weight:500;color:#1C1C2E;'>
                    {gap.get('gap', '')}
                </td>
                <td style='padding:12px 14px;text-align:center;font-weight:600;color:#003366;'>
                    {gap.get('frequency', 0)}
                </td>
                <td style='padding:12px 14px;color:#374151;line-height:1.5;'>
                    {gap.get('your_advantage', '')}
                </td>
            </tr>
        """
    st.markdown(
        f"""
        <table style='width:100%;border-collapse:collapse;font-family:"Plus Jakarta Sans",sans-serif;
                      font-size:13px;background:#ffffff;border-radius:10px;overflow:hidden;
                      box-shadow:0 1px 4px rgba(0,51,102,.08);'>
            <thead>
                <tr style='background:#003366;'>
                    <th style='padding:10px 14px;text-align:left;color:rgba(255,255,255,0.8);
                               font-size:11px;letter-spacing:2px;text-transform:uppercase;
                               font-weight:500;'>Feature Gap</th>
                    <th style='padding:10px 14px;text-align:center;color:rgba(255,255,255,0.8);
                               font-size:11px;letter-spacing:2px;text-transform:uppercase;
                               font-weight:500;'>Mentions</th>
                    <th style='padding:10px 14px;text-align:left;color:rgba(255,255,255,0.8);
                               font-size:11px;letter-spacing:2px;text-transform:uppercase;
                               font-weight:500;'>Our Advantage</th>
                </tr>
            </thead>
            <tbody>{gap_rows}</tbody>
        </table>
        """,
        unsafe_allow_html=True,
    )

# ── Download buttons ──────────────────────────────────────────────────────────
st.markdown("<div style='height:24px;'></div>", unsafe_allow_html=True)
dl_cols = st.columns(3)

with dl_cols[0]:
    md_bytes = battlecard_to_markdown(card).encode("utf-8")
    st.download_button(
        label="Download Markdown",
        data=md_bytes,
        file_name=f"battlecard_{competitor.lower().replace(' ', '_')}.md",
        mime="text/markdown",
        use_container_width=True,
    )

with dl_cols[1]:
    content_bytes, mime_type = generate_pdf_bytes(card)
    ext = "pdf" if _WEASYPRINT_AVAILABLE else "html"
    label = "Download PDF" if _WEASYPRINT_AVAILABLE else "Download HTML"
    st.download_button(
        label=label,
        data=content_bytes,
        file_name=f"battlecard_{competitor.lower().replace(' ', '_')}.{ext}",
        mime=mime_type,
        use_container_width=True,
    )

with dl_cols[2]:
    if not _WEASYPRINT_AVAILABLE:
        st.caption("PDF requires weasyprint + GTK+")
