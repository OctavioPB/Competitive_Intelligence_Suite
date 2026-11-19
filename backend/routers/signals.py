"""Market signals router — competitor pricing-page changes and hiring patterns."""

import os

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.deps import known_competitor
from config import COMPETITORS
from ingestion.browser import playwright_available
from modules.market_signals import CATEGORY_LABELS, get_hiring_overview, get_pricing_overview

router = APIRouter(tags=["signals"])


def _config(competitor: str) -> dict:
    return next(c for c in COMPETITORS if c["name"] == competitor)


def _demo_mode() -> bool:
    return os.getenv("DEMO_MODE", "false").lower() == "true"


@router.get("/signals/pricing")
def pricing(competitor: str):
    """Monitored pricing pages: current price points and the latest change."""
    name = known_competitor(competitor)
    return {**get_pricing_overview(name), "monitored_urls": _config(name).get("pricing_urls", [])}


@router.get("/signals/hiring")
def hiring(competitor: str):
    """Open roles by function and what was posted in the last 30 days."""
    name = known_competitor(competitor)
    careers = _config(name).get("careers")
    board = None
    if careers:
        board = {
            "provider": careers["provider"],
            "board": careers["board"],
            # Workday is paged newest-first and only read back 30 days (see scraper_jobs).
            "recent_only": careers["provider"] == "workday",
        }
    return {**get_hiring_overview(name), "board": board, "category_labels": CATEGORY_LABELS}


class RefreshRequest(BaseModel):
    competitor: str


@router.post("/signals/refresh")
def refresh(body: RefreshRequest):
    """Check the competitor's pricing pages and job board now.

    Slow on purpose-built boards (Workday pages through ~60 requests), so the
    UI shows a spinner; the daily scheduler job does the same for everyone.
    """
    name = known_competitor(body.competitor)
    if _demo_mode():
        raise HTTPException(
            status_code=409,
            detail="Demo mode shows sample market signals — live checks are disabled so they "
                   "never mix with the demo data.",
        )
    from ingestion.run_signals import check_competitor

    return {**check_competitor(_config(name)), "headless_browser": playwright_available()}
