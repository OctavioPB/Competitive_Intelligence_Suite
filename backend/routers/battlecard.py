"""Battlecard router — AI-generated sales battlecards."""

from fastapi import APIRouter
from pydantic import BaseModel

from backend.deps import known_competitor
from modules.battlecard_generator import generate_battlecard, load_cached_battlecard

router = APIRouter(tags=["battlecard"])


class BattlecardRequest(BaseModel):
    competitor: str


@router.get("/battlecard")
def get_cached_battlecard(competitor: str = "Salesforce"):
    """Return the cached battlecard, or null if none exists."""
    return load_cached_battlecard(known_competitor(competitor))


@router.post("/battlecard")
def create_battlecard(body: BattlecardRequest):
    """Generate a fresh battlecard via the Claude API."""
    return generate_battlecard(known_competitor(body.competitor))
