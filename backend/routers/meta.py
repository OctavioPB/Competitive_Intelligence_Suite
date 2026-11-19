"""Meta router — competitor names, own-feature list and data provenance."""

import os

from fastapi import APIRouter

from config import COMPETITOR_NAMES, OWN_FEATURES
from modules.review_evidence import get_data_status

router = APIRouter(tags=["meta"])


@router.get("/meta/competitors")
def get_competitors():
    return {"competitors": COMPETITOR_NAMES}


@router.get("/meta/own-features")
def get_own_features():
    return {"features": OWN_FEATURES}


@router.get("/meta/data-status")
def data_status():
    """How much of each competitor's data is synthetic sample data.

    Live ingestion silently falls back to fixtures when a scraper is blocked,
    so the UI uses this to warn before anyone treats sample data as real.
    """
    status = get_data_status()
    empty = {"reviews": 0, "synthetic": 0, "latest_date": None}
    return {
        "demo_mode": os.getenv("DEMO_MODE", "false").lower() == "true",
        "competitors": [{"name": n, **status.get(n, empty)} for n in COMPETITOR_NAMES],
    }
