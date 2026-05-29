"""Battlecard router — AI-generated sales battlecards."""

from fastapi import APIRouter
from pydantic import BaseModel

from modules.battlecard_generator import generate_battlecard, load_cached_battlecard

router = APIRouter(tags=["battlecard"])


class BattlecardRequest(BaseModel):
    competitor: str


@router.get("/battlecard")
def get_cached_battlecard(competitor: str = "Salesforce"):
    """Try to load a cached battlecard; returns null if none exists."""
    card = load_cached_battlecard(competitor)
    return card  # FastAPI serialises None → null in JSON


@router.post("/battlecard")
def create_battlecard(body: BattlecardRequest):
    """Generate a fresh battlecard via the module (may call Claude API)."""
    card = generate_battlecard(body.competitor)
    return card
