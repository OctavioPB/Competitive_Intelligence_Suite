"""Page 6 — Hot Prospect Finder (M06)."""

import io
from datetime import datetime, timedelta

import pandas as pd
import streamlit as st

from config import COMPETITOR_NAMES, SUBREDDITS
from modules.hot_prospect_finder import enrich_lead, scan_reddit, score_urgency
from outputs.crm_export import export_leads_csv

_BRAND_CSS = """
<link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600&family=Fraunces:ital,opsz,wght@0,9..144,300;1,9..144,300&display=swap" rel="stylesheet">
<style>
.rs-urgency-high   { color: #E03448; font-weight: 600; }
.rs-urgency-medium { color: #F07020; font-weight: 600; }
.rs-urgency-low    { color: #27B97C; font-weight: 600; }
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
            Hot Prospect Finder
        </div>
        <div style="color:rgba(255,255,255,0.6);font-size:14px;
                    font-family:'Plus Jakarta Sans',sans-serif;line-height:1.6;">
            Reddit users actively expressing intent to switch from competitors —
            ranked by urgency and enriched with suggested outreach angles.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


# ── Fixture leads (shown when Reddit credentials are absent) ──────────────────

def _fixture_leads() -> pd.DataFrame:
    """Return a deterministic set of fixture prospect leads for demo mode."""
    base = datetime(2025, 12, 25)
    posts = [
        {
            "source": "reddit",
            "post_id": "fix001",
            "username": "frustrated_admin_sf",
            "post_text": (
                "Switching from Salesforce after 3 years. The pricing keeps going up and "
                "support is terrible. Looking for alternative CRM recommendations."
            ),
            "post_url": "https://reddit.com/r/CRM/comments/example1",
            "created_at": (base - timedelta(days=2)).strftime("%Y-%m-%d"),
            "competitor_name": "Salesforce",
            "upvotes": 87,
            "num_comments": 34,
            "sentiment_score": -0.72,
        },
        {
            "source": "reddit",
            "post_id": "fix002",
            "username": "saas_buyer_2025",
            "post_text": (
                "Fed up with HubSpot's contact limits on lower tiers. "
                "Alternative to HubSpot that doesn't charge per contact?"
            ),
            "post_url": "https://reddit.com/r/sales/comments/example2",
            "created_at": (base - timedelta(days=4)).strftime("%Y-%m-%d"),
            "competitor_name": "HubSpot",
            "upvotes": 43,
            "num_comments": 21,
            "sentiment_score": -0.55,
        },
        {
            "source": "reddit",
            "post_id": "fix003",
            "username": "revops_lead_co",
            "post_text": (
                "Moving away from Pipedrive — the reporting is just too limited for our team. "
                "We need something with better dashboards and workflow automation."
            ),
            "post_url": "https://reddit.com/r/entrepreneur/comments/example3",
            "created_at": (base - timedelta(days=6)).strftime("%Y-%m-%d"),
            "competitor_name": "Pipedrive",
            "upvotes": 29,
            "num_comments": 15,
            "sentiment_score": -0.48,
        },
        {
            "source": "reddit",
            "post_id": "fix004",
            "username": "startup_cto_nyc",
            "post_text": (
                "Salesforce is terrible for small teams. I'm leaving after 18 months. "
                "The learning curve is brutal and every customisation needs a consultant."
            ),
            "post_url": "https://reddit.com/r/SaaS/comments/example4",
            "created_at": (base - timedelta(days=3)).strftime("%Y-%m-%d"),
            "competitor_name": "Salesforce",
            "upvotes": 112,
            "num_comments": 56,
            "sentiment_score": -0.81,
        },
        {
            "source": "reddit",
            "post_id": "fix005",
            "username": "b2b_smb_owner",
            "post_text": (
                "Looking for alternative to HubSpot that has better integrations. "
                "We hit their API limits every week and it's frustrating our dev team."
            ),
            "post_url": "https://reddit.com/r/smallbusiness/comments/example5",
            "created_at": (base - timedelta(days=5)).strftime("%Y-%m-%d"),
            "competitor_name": "HubSpot",
            "upvotes": 38,
            "num_comments": 17,
            "sentiment_score": -0.50,
        },
    ]
    df = pd.DataFrame(posts)
    # Score urgency and enrich each lead
    enriched_rows = []
    for _, row in df.iterrows():
        post_dict = row.to_dict()
        post_dict["urgency_score"] = score_urgency(post_dict)
        enriched = enrich_lead(post_dict)
        enriched_rows.append(enriched)
    return pd.DataFrame(enriched_rows).sort_values("urgency_score", ascending=False)


# ── Controls ──────────────────────────────────────────────────────────────────
ctrl_cols = st.columns([1, 1, 2])
with ctrl_cols[0]:
    scan_clicked = st.button("Scan Reddit", use_container_width=True)
with ctrl_cols[1]:
    demo_clicked = st.button("Load Demo Leads", use_container_width=True)

if demo_clicked:
    with st.spinner("Loading fixture leads…"):
        st.session_state["prospects"] = _fixture_leads()

if scan_clicked:
    with st.spinner("Scanning Reddit for switching-intent posts…"):
        try:
            raw_df = scan_reddit(COMPETITOR_NAMES, SUBREDDITS[:3])
            if raw_df.empty:
                st.warning("No posts matched the search criteria.")
            else:
                enriched_rows = []
                for _, row in raw_df.iterrows():
                    post_dict = row.to_dict()
                    post_dict["urgency_score"] = score_urgency(post_dict)
                    enriched_rows.append(enrich_lead(post_dict))
                prospects_df = (
                    pd.DataFrame(enriched_rows)
                    .sort_values("urgency_score", ascending=False)
                    .head(20)
                )
                st.session_state["prospects"] = prospects_df
        except RuntimeError as exc:
            st.warning(
                f"Reddit credentials not configured ({exc}). "
                "Click **Load Demo Leads** to see fixture data."
            )

prospects_df: pd.DataFrame | None = st.session_state.get("prospects")

if prospects_df is None or prospects_df.empty:
    st.info(
        "No leads loaded yet. Click **Scan Reddit** for live data "
        "or **Load Demo Leads** to preview fixture prospects."
    )
    st.stop()

# ── KPI row ───────────────────────────────────────────────────────────────────
high_urgency = int((prospects_df["urgency_score"] >= 0.7).sum())
med_urgency = int(((prospects_df["urgency_score"] >= 0.4) & (prospects_df["urgency_score"] < 0.7)).sum())
competitors_seen = prospects_df["competitor_name"].nunique()

kpi_cols = st.columns(4)
kpi_data = [
    ("Total Prospects", str(len(prospects_df)), "switching-intent posts", "#003366"),
    ("High Urgency (≥0.7)", str(high_urgency), "act now", "#E03448"),
    ("Medium Urgency", str(med_urgency), "follow up this week", "#F07020"),
    ("Competitors Flagged", str(competitors_seen), "unique competitors", "#27B97C"),
]
for col, (label, value, sub, border) in zip(kpi_cols, kpi_data):
    with col:
        st.markdown(
            f"""
            <div style="background:#ffffff;border-radius:10px;padding:18px 22px;
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

# ── Lead table ────────────────────────────────────────────────────────────────
st.markdown(
    "<div style='font-family:\"Plus Jakarta Sans\",sans-serif;font-size:12px;"
    "font-weight:600;color:#003366;margin-bottom:12px;letter-spacing:2px;"
    "text-transform:uppercase;'>Top Prospects</div>",
    unsafe_allow_html=True,
)


def _urgency_badge(score: float) -> str:
    if score >= 0.7:
        color, label = "#E03448", "HIGH"
    elif score >= 0.4:
        color, label = "#F07020", "MED"
    else:
        color, label = "#27B97C", "LOW"
    return (
        f'<span style="background:{color}1A;color:{color};font-size:10px;'
        f'letter-spacing:2px;text-transform:uppercase;padding:2px 8px;'
        f'border-radius:20px;font-weight:600;font-family:\'Plus Jakarta Sans\',sans-serif;">'
        f'{label} {score:.2f}</span>'
    )


rows_html = ""
for _, row in prospects_df.head(10).iterrows():
    company_sigs = row.get("company_signals", [])
    if isinstance(company_sigs, list):
        sigs_str = ", ".join(company_sigs[:3]) if company_sigs else "—"
    else:
        sigs_str = str(company_sigs)[:60]

    post_url = row.get("post_url", "#")
    link = f'<a href="{post_url}" target="_blank" style="color:#003366;font-size:12px;">View</a>'

    rows_html += f"""
        <tr style='border-bottom:1px solid #F0F4F8;'>
            <td style='padding:12px 14px;vertical-align:top;'>
                <div style='font-weight:600;color:#003366;font-size:12px;'>
                    {row.get('username', '—')}
                </div>
                <div style='font-size:11px;color:#9CA3AF;'>{row.get('created_at', '')}</div>
            </td>
            <td style='padding:12px 14px;vertical-align:top;font-size:12px;color:#374151;
                       line-height:1.5;max-width:260px;'>
                {row.get('complaint_summary', '')[:100]}
            </td>
            <td style='padding:12px 14px;vertical-align:top;font-size:12px;color:#6B7280;'>
                {sigs_str}
            </td>
            <td style='padding:12px 14px;vertical-align:top;font-size:12px;color:#374151;
                       line-height:1.5;max-width:200px;'>
                {row.get('suggested_angle', '')[:100]}
            </td>
            <td style='padding:12px 14px;text-align:center;vertical-align:top;'>
                {_urgency_badge(float(row.get('urgency_score', 0)))}
            </td>
            <td style='padding:12px 14px;text-align:center;vertical-align:middle;'>
                {link}
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
                <th style='padding:10px 14px;text-align:left;color:rgba(255,255,255,0.8);
                           font-size:11px;letter-spacing:2px;text-transform:uppercase;
                           font-weight:500;'>User</th>
                <th style='padding:10px 14px;text-align:left;color:rgba(255,255,255,0.8);
                           font-size:11px;letter-spacing:2px;text-transform:uppercase;
                           font-weight:500;'>Complaint</th>
                <th style='padding:10px 14px;text-align:left;color:rgba(255,255,255,0.8);
                           font-size:11px;letter-spacing:2px;text-transform:uppercase;
                           font-weight:500;'>Company Signals</th>
                <th style='padding:10px 14px;text-align:left;color:rgba(255,255,255,0.8);
                           font-size:11px;letter-spacing:2px;text-transform:uppercase;
                           font-weight:500;'>Angle</th>
                <th style='padding:10px 14px;text-align:center;color:rgba(255,255,255,0.8);
                           font-size:11px;letter-spacing:2px;text-transform:uppercase;
                           font-weight:500;'>Urgency</th>
                <th style='padding:10px 14px;text-align:center;color:rgba(255,255,255,0.8);
                           font-size:11px;letter-spacing:2px;text-transform:uppercase;
                           font-weight:500;'>Link</th>
            </tr>
        </thead>
        <tbody>{rows_html}</tbody>
    </table>
    """,
    unsafe_allow_html=True,
)

# ── Export buttons ────────────────────────────────────────────────────────────
st.markdown("<div style='height:20px;'></div>", unsafe_allow_html=True)
export_cols = st.columns([1, 1, 3])

with export_cols[0]:
    csv_buf = io.StringIO()
    prospects_df.to_csv(csv_buf, index=False)
    st.download_button(
        label="Export CSV",
        data=csv_buf.getvalue().encode("utf-8"),
        file_name="hot_prospects.csv",
        mime="text/csv",
        use_container_width=True,
    )

with export_cols[1]:
    json_data = prospects_df.to_json(orient="records", indent=2, force_ascii=False)
    st.download_button(
        label="Export JSON",
        data=json_data.encode("utf-8"),
        file_name="hot_prospects.json",
        mime="application/json",
        use_container_width=True,
    )
