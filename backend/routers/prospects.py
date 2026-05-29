"""Prospects router — hot prospect finder."""

import math
from datetime import datetime, timedelta

from fastapi import APIRouter

from config import COMPETITOR_NAMES, SUBREDDITS
from modules.hot_prospect_finder import enrich_lead, scan_reddit, score_urgency

router = APIRouter(tags=["prospects"])


def _safe(value):
    if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
        return None
    return value


def _lead_to_dict(lead: dict) -> dict:
    """Convert a raw lead dict to a JSON-safe representation."""
    company_signals = lead.get("company_signals", [])
    if not isinstance(company_signals, list):
        company_signals = []

    return {
        "username": str(lead.get("username", "")),
        "post_url": str(lead.get("post_url", "")),
        "created_at": str(lead.get("created_at", "")),
        "competitor_name": str(lead.get("competitor_name", "")),
        "urgency_score": _safe(float(lead.get("urgency_score", 0.0))) or 0.0,
        "complaint_summary": str(lead.get("complaint_summary", "")),
        "company_signals": [str(s) for s in company_signals],
        "suggested_angle": str(lead.get("suggested_angle", "")),
    }


def _fixture_leads() -> list[dict]:
    """Return the 5 deterministic fixture leads (same as Streamlit page)."""
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

    enriched = []
    for post in posts:
        post["urgency_score"] = score_urgency(post)
        enriched.append(enrich_lead(post))

    enriched.sort(key=lambda x: x.get("urgency_score", 0), reverse=True)
    return [_lead_to_dict(lead) for lead in enriched]


@router.get("/prospects/demo")
def get_demo_prospects():
    """Return the 5 fixture leads enriched and sorted by urgency."""
    return _fixture_leads()


@router.post("/prospects/scan")
def scan_prospects():
    """Scan Reddit for live switching-intent posts and enrich them."""
    try:
        raw_df = scan_reddit(COMPETITOR_NAMES, SUBREDDITS[:3])
        if raw_df.empty:
            return []

        enriched = []
        for _, row in raw_df.iterrows():
            post_dict = row.to_dict()
            post_dict["urgency_score"] = score_urgency(post_dict)
            enriched.append(enrich_lead(post_dict))

        enriched.sort(key=lambda x: x.get("urgency_score", 0), reverse=True)
        return [_lead_to_dict(lead) for lead in enriched[:20]]
    except RuntimeError:
        # Reddit credentials not configured — return fixture data
        return _fixture_leads()
