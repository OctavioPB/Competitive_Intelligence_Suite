"""Win/loss router — log closed deals and compare their reasons with review pain points."""

from typing import Literal

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from backend.auth_deps import current_user
from backend.deps import known_competitor
from modules.winloss import CATEGORIES, DealError, delete_deal, list_deals, record_deal, winloss_insights

router = APIRouter(tags=["winloss"])


class DealIn(BaseModel):
    competitor: str
    outcome: Literal["won", "lost"]
    reason_category: str
    reason_text: str = Field("", max_length=2000)
    deal_name: str = Field("", max_length=200)
    amount: float | None = Field(None, ge=0)
    closed_on: str | None = Field(None, max_length=10)


@router.get("/winloss")
def get_winloss(competitor: str):
    name = known_competitor(competitor)
    return {**winloss_insights(name), "recent": list_deals(name, limit=50), "category_labels": CATEGORIES}


@router.post("/winloss/deals")
def add_deal(body: DealIn, request: Request):
    user = current_user(request) or {}
    try:
        return record_deal(
            known_competitor(body.competitor), body.outcome, body.reason_category,
            reason_text=body.reason_text, deal_name=body.deal_name, amount=body.amount,
            closed_on=body.closed_on, created_by=user.get("email"),
        )
    except DealError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.delete("/winloss/deals/{deal_id}")
def remove_deal(deal_id: int):
    try:
        delete_deal(deal_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="No such deal") from exc
    return {"ok": True}
