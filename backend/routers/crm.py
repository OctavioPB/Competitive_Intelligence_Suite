"""CRM router — push Hot Prospect leads into HubSpot or Salesforce."""

import os
from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.routers.prospects import FIXTURE_POST_URLS
from outputs.crm_sync import CRMConfigError, CRMError, client_for, crm_status, push_leads

router = APIRouter(tags=["crm"])


class LeadIn(BaseModel):
    username: str = Field(max_length=200)
    post_url: str = Field(max_length=500)
    created_at: str = ""
    competitor_name: str = ""
    urgency_score: float = 0.0
    complaint_summary: str = Field("", max_length=4000)
    company_signals: list[str] = []
    suggested_angle: str = Field("", max_length=2000)
    is_synthetic: bool = False


class PushRequest(BaseModel):
    target: Literal["hubspot", "salesforce"]
    leads: list[LeadIn] = Field(min_length=1, max_length=50)


@router.get("/crm/status")
def get_crm_status():
    """Which CRMs are configured, so the UI can enable the right buttons."""
    return {
        "demo_mode": os.getenv("DEMO_MODE", "false").lower() == "true",
        **crm_status(),
    }


@router.post("/crm/push")
def push_to_crm(body: PushRequest):
    """Create the given leads in the CRM, skipping ones that already exist."""
    if os.getenv("DEMO_MODE", "false").lower() == "true":
        raise HTTPException(
            status_code=409,
            detail="Demo mode uses sample leads — CRM sync is disabled so no fake leads reach a real CRM.",
        )

    try:
        client = client_for(body.target)
    except CRMConfigError as exc:
        raise HTTPException(status_code=503, detail=f"{body.target} is not configured: {exc}") from exc
    except CRMError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    # Trust the server's own fixture list, not only the flag sent by the browser.
    result = push_leads(
        client,
        [lead.model_dump() for lead in body.leads],
        is_synthetic=lambda lead: lead["is_synthetic"] or lead["post_url"] in FIXTURE_POST_URLS,
    )
    return result.summary()
