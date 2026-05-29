"""Digest router — intelligence digest (M08)."""

from fastapi import APIRouter

from config import COMPETITOR_NAMES
from modules.digest_generator import generate_digest, list_digest_history, load_latest_digest

router = APIRouter(tags=["digest"])


@router.get("/digest/latest")
def get_latest_digest():
    """Return the most recently stored digest, or null if none exists."""
    return load_latest_digest()


@router.get("/digest/history")
def get_digest_history():
    """Return a list of past digest metadata: [{id, generated_at}]."""
    return list_digest_history()


@router.post("/digest/generate")
def create_digest():
    """Generate a fresh Claude-synthesised digest across all competitors."""
    return generate_digest(COMPETITOR_NAMES)
