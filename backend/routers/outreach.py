"""Outreach router — outreach composer (M09)."""

from fastapi import APIRouter
from pydantic import BaseModel

from modules.outreach_composer import compose_outreach

router = APIRouter(tags=["outreach"])


class OutreachRequest(BaseModel):
    competitor: str
    complaint:  str
    username:   str = "Prospect"


@router.post("/outreach/compose")
def create_outreach(body: OutreachRequest):
    """Generate three personalised outreach variants for a switching-intent prospect."""
    return compose_outreach(
        competitor=body.competitor,
        complaint=body.complaint,
        username=body.username,
    )
