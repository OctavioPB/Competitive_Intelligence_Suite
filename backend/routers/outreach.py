"""Outreach router — outreach composer (M09)."""

from fastapi import APIRouter
from pydantic import BaseModel, Field

from backend.deps import known_competitor
from modules.outreach_composer import compose_outreach

router = APIRouter(tags=["outreach"])


class OutreachRequest(BaseModel):
    competitor: str
    complaint:  str = Field(min_length=1, max_length=4000)
    username:   str = Field("Prospect", max_length=120)


@router.post("/outreach/compose")
def create_outreach(body: OutreachRequest):
    """Generate three personalised outreach variants for a switching-intent prospect."""
    return compose_outreach(
        competitor=known_competitor(body.competitor),
        complaint=body.complaint,
        username=body.username or "Prospect",
    )
