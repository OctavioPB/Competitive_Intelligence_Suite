"""Prospects router — hot prospect finder."""

import logging
import sqlite3
from datetime import datetime, timedelta
from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.deps import json_safe
from config import SUBREDDITS
from modules.settings_store import competitor_names
from modules.hot_prospect_finder import enrich_lead, scan_reddit, score_urgency
from modules.prospect_pipeline import UnknownLeadError, get_pipeline, set_stage, upsert_leads

logger = logging.getLogger(__name__)
router = APIRouter(tags=["prospects"])


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
        "urgency_score": json_safe(float(lead.get("urgency_score", 0.0))) or 0.0,
        "complaint_summary": str(lead.get("complaint_summary", "")),
        "company_signals": [str(s) for s in company_signals],
        "suggested_angle": str(lead.get("suggested_angle", "")),
        "is_synthetic": bool(lead.get("is_synthetic", False)),
    }


# Deterministic sample leads for demo mode and for when Reddit is not configured.
_FIXTURE_BASE = datetime(2025, 12, 25)
_FIXTURE_POSTS: list[dict] = [
    {
        "source": "reddit",
        "post_id": "fix001",
        "username": "frustrated_admin_sf",
        "post_text": (
            "Switching from Salesforce after 3 years. The pricing keeps going up and "
            "support is terrible. Looking for alternative CRM recommendations."
        ),
        "post_url": "https://reddit.com/r/CRM/comments/example1",
        "created_at": (_FIXTURE_BASE - timedelta(days=2)).strftime("%Y-%m-%d"),
        "competitor_name": "Salesforce",
        "upvotes": 87,
        "num_comments": 34,
        "is_synthetic": True,
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
        "created_at": (_FIXTURE_BASE - timedelta(days=4)).strftime("%Y-%m-%d"),
        "competitor_name": "HubSpot",
        "upvotes": 43,
        "num_comments": 21,
        "is_synthetic": True,
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
        "created_at": (_FIXTURE_BASE - timedelta(days=6)).strftime("%Y-%m-%d"),
        "competitor_name": "Pipedrive",
        "upvotes": 29,
        "num_comments": 15,
        "is_synthetic": True,
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
        "created_at": (_FIXTURE_BASE - timedelta(days=3)).strftime("%Y-%m-%d"),
        "competitor_name": "Salesforce",
        "upvotes": 112,
        "num_comments": 56,
        "is_synthetic": True,
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
        "created_at": (_FIXTURE_BASE - timedelta(days=5)).strftime("%Y-%m-%d"),
        "competitor_name": "HubSpot",
        "upvotes": 38,
        "num_comments": 17,
        "is_synthetic": True,
        "sentiment_score": -0.50,
    },
]

# The CRM router refuses to sync these, whatever the browser claims.
FIXTURE_POST_URLS: frozenset[str] = frozenset(p["post_url"] for p in _FIXTURE_POSTS)


def _fixture_leads() -> list[dict]:
    """Return the 5 deterministic fixture leads."""
    return _rank([dict(p) for p in _FIXTURE_POSTS])


def _rank(posts: list[dict], limit: int | None = None) -> list[dict]:
    """Enrich, score and sort posts by urgency (highest first).

    Enrichment runs first because it fills in sentiment_score when the post has
    none (live Reddit rows) and score_urgency() weights that signal at up to 0.30.
    """
    enriched = []
    for post in posts:
        lead = enrich_lead(post)
        lead["urgency_score"] = score_urgency(lead)
        enriched.append(lead)

    enriched.sort(key=lambda x: x["urgency_score"], reverse=True)
    return [_lead_to_dict(lead) for lead in enriched[:limit]]


def _with_stages(leads: list[dict]) -> list[dict]:
    """Save the leads to the pipeline and return them with their stage.

    The scan result matters more than its bookkeeping: if the pipeline table
    cannot be written, the leads are still returned (without a stage).
    """
    try:
        return upsert_leads(leads)
    except sqlite3.Error as exc:
        logger.warning("Could not store leads in the pipeline: %s", exc)
        return [{**lead, "status": None, "note": None} for lead in leads]


@router.get("/prospects/demo")
def get_demo_prospects():
    """Return the 5 fixture leads enriched and sorted by urgency."""
    return _with_stages(_fixture_leads())


@router.post("/prospects/scan")
def scan_prospects():
    """Scan Reddit for live switching-intent posts and enrich them."""
    try:
        raw_df = scan_reddit(competitor_names(), SUBREDDITS[:3])
        if raw_df.empty:
            return []

        # The same thread can match several subreddit/competitor searches.
        raw_df = raw_df.drop_duplicates(subset=["post_id", "competitor_name"])
        return _with_stages(_rank(raw_df.to_dict(orient="records"), limit=20))
    except RuntimeError:
        # Reddit credentials not configured — return fixture data
        return _with_stages(_fixture_leads())


@router.get("/prospects/pipeline")
def pipeline(include_dismissed: bool = False):
    """Every lead found so far, most urgent first, with a count per stage."""
    return get_pipeline(include_dismissed=include_dismissed)


class StageRequest(BaseModel):
    post_url: str = Field(max_length=500)
    status: Literal["new", "contacted", "replied", "opportunity", "dismissed"]
    note: str | None = Field(None, max_length=2000)


@router.post("/prospects/stage")
def update_stage(body: StageRequest):
    """Move a lead to another pipeline stage (and optionally set its note)."""
    try:
        return set_stage(body.post_url, body.status, body.note)
    except UnknownLeadError as exc:
        raise HTTPException(status_code=404, detail="That lead is not in the pipeline yet — scan first.") from exc
