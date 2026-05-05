"""Page 3 — Feature Wish Miner (M03)."""

import ast

import streamlit as st

from config import OWN_FEATURES
from modules.feature_wish_miner import extract_wishes, flag_own_features
from ui.components.competitor_selector import render_competitor_selector

_BRAND_CSS = """
<link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600&family=Fraunces:ital,opsz,wght@0,9..144,300;1,9..144,300&display=swap" rel="stylesheet">
<style>
.rs-badge-covered {
    display: inline-block;
    background: #E0F7EF;
    color: #0D5C3A;
    font-size: 10px;
    letter-spacing: 2px;
    text-transform: uppercase;
    padding: 3px 10px;
    border-radius: 20px;
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-weight: 600;
}
.rs-badge-gap {
    display: inline-block;
    background: #FEF0E6;
    color: #7A3800;
    font-size: 10px;
    letter-spacing: 2px;
    text-transform: uppercase;
    padding: 3px 10px;
    border-radius: 20px;
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-weight: 600;
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
            Feature Wish Miner
        </div>
        <div style="color:rgba(255,255,255,0.6);font-size:14px;
                    font-family:'Plus Jakarta Sans',sans-serif;line-height:1.6;">
            Competitor feature requests clustered by semantic similarity.
            <span style="color:#E0F7EF;font-weight:600;">Green</span> = already in your product.
            <span style="color:#FEF0E6;font-weight:600;">Orange</span> = gap and sales opportunity.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ── Controls ──────────────────────────────────────────────────────────────────
col_sel, col_filter = st.columns([2, 1])
with col_sel:
    competitor = render_competitor_selector(key="m03_competitor")
with col_filter:
    show_gaps_only = st.toggle("Show gaps only", value=False)

# ── Data ──────────────────────────────────────────────────────────────────────
with st.spinner(f"Clustering feature requests for {competitor}…"):
    wish_df = extract_wishes(competitor)
    if not wish_df.empty:
        wish_df = flag_own_features(wish_df, OWN_FEATURES)

if wish_df.empty:
    st.warning(
        "No wish phrases found for this competitor. "
        "Confirm the pipeline has processed reviews with wish_phrases content."
    )
    st.stop()

# ── KPI row ───────────────────────────────────────────────────────────────────
total_clusters = len(wish_df)
covered_count = int(wish_df["your_product_has_it"].sum())
gap_count = total_clusters - covered_count
total_mentions = int(wish_df["count"].sum())

kpi_cols = st.columns(4)
kpi_data = [
    ("Feature Clusters", str(total_clusters), "unique request themes", "#003366"),
    ("Already Covered", str(covered_count), "your product has this", "#27B97C"),
    ("Gaps", str(gap_count), "sales talking points", "#E03448"),
    ("Total Mentions", f"{total_mentions:,}", "across all reviews", "#003366"),
]
for col, (label, value, sub, border) in zip(kpi_cols, kpi_data):
    with col:
        st.markdown(
            f"""
            <div style="background:#ffffff;border-radius:10px;padding:20px 24px;
                        border-top:3px solid {border};
                        box-shadow:0 1px 4px rgba(0,51,102,.08);">
                <div style="font-family:'Plus Jakarta Sans',sans-serif;font-size:11px;
                            letter-spacing:2px;text-transform:uppercase;
                            color:#6B7280;margin-bottom:4px;">{label}</div>
                <div style="font-family:'Fraunces',Georgia,serif;font-size:28px;
                            font-weight:300;color:#003366;">{value}</div>
                <div style="font-family:'Plus Jakarta Sans',sans-serif;font-size:12px;
                            color:#6B7280;margin-top:2px;">{sub}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

st.markdown("<div style='height:24px;'></div>", unsafe_allow_html=True)

# ── Wish table ────────────────────────────────────────────────────────────────
display_df = wish_df[~wish_df["your_product_has_it"]] if show_gaps_only else wish_df

if display_df.empty:
    st.info("No gaps found — your product covers all detected wish clusters. Toggle off the filter to see all clusters.")
else:
    st.markdown(
        "<div style='font-family:\"Plus Jakarta Sans\",sans-serif;font-size:12px;"
        "font-weight:600;color:#003366;margin-bottom:12px;letter-spacing:2px;"
        "text-transform:uppercase;'>Feature Request Clusters</div>",
        unsafe_allow_html=True,
    )

    rows_html = ""
    for _, row in display_df.iterrows():
        covered_flag = bool(row["your_product_has_it"])
        badge = (
            '<span class="rs-badge-covered">We have this</span>'
            if covered_flag
            else '<span class="rs-badge-gap">Gap</span>'
        )

        matched = row.get("matched_feature") or ""
        matched_html = (
            f'<div style="font-size:11px;color:#0D5C3A;margin-top:5px;">'
            f'Matched: <em>{matched}</em></div>'
            if matched
            else ""
        )

        quotes = row.get("sample_quotes") or []
        if isinstance(quotes, str):
            try:
                quotes = ast.literal_eval(quotes)
            except Exception:
                quotes = [quotes]

        quote_html = "".join(
            f'<div style="font-style:italic;color:#6B7280;font-size:12px;'
            f'margin-top:5px;line-height:1.5;">"{q}"</div>'
            for q in (quotes or [])[:2]
        )

        rows_html += f"""
            <tr style='border-bottom:1px solid #F0F4F8;'>
                <td style='padding:14px 16px;vertical-align:top;'>
                    <div style='font-family:"Plus Jakarta Sans",sans-serif;font-size:13px;
                                color:#1C1C2E;font-weight:500;line-height:1.4;'>
                        {row['wish_phrase_cluster']}
                    </div>
                    {quote_html}
                </td>
                <td style='padding:14px 16px;text-align:center;vertical-align:top;'>
                    <span style='font-family:"Plus Jakarta Sans",sans-serif;font-size:15px;
                                 font-weight:600;color:#003366;'>{row['count']}</span>
                </td>
                <td style='padding:14px 16px;vertical-align:top;'>
                    {badge}
                    {matched_html}
                </td>
            </tr>
        """

    st.markdown(
        f"""
        <table style='width:100%;border-collapse:collapse;
                      font-family:"Plus Jakarta Sans",sans-serif;font-size:13px;
                      background:#ffffff;border-radius:10px;overflow:hidden;
                      box-shadow:0 1px 4px rgba(0,51,102,.08);'>
            <thead>
                <tr style='background:#003366;'>
                    <th style='padding:12px 16px;text-align:left;color:rgba(255,255,255,0.8);
                               font-size:11px;letter-spacing:2px;text-transform:uppercase;
                               font-weight:500;'>Request Theme</th>
                    <th style='padding:12px 16px;text-align:center;color:rgba(255,255,255,0.8);
                               font-size:11px;letter-spacing:2px;text-transform:uppercase;
                               font-weight:500;'>Mentions</th>
                    <th style='padding:12px 16px;text-align:left;color:rgba(255,255,255,0.8);
                               font-size:11px;letter-spacing:2px;text-transform:uppercase;
                               font-weight:500;'>Coverage</th>
                </tr>
            </thead>
            <tbody>{rows_html}</tbody>
        </table>
        """,
        unsafe_allow_html=True,
    )
