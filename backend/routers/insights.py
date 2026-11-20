"""Insights router — what changed per competitor, and all competitors side by side."""

from fastapi import APIRouter, Query

from backend.deps import known_competitor
from modules.settings_store import competitor_names
from modules.change_tracker import get_changes
from modules.competitor_compare import compare_competitors

router = APIRouter(tags=["insights"])


@router.get("/changes")
def changes(competitor: str, days: int = Query(7, ge=1, le=90)):
    """Reviews, battlecard, digest, alerts, pricing and hiring changes in the window."""
    return get_changes(known_competitor(competitor), days)


@router.get("/compare")
def compare():
    """Every configured competitor side by side."""
    return compare_competitors(competitor_names())
