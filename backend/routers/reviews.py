"""Reviews router — the individual reviews behind pain points and sentiment months."""

from typing import Literal

from fastapi import APIRouter, HTTPException, Query

from backend.deps import known_competitor
from modules.review_evidence import get_reviews

router = APIRouter(tags=["reviews"])


@router.get("/reviews")
def list_reviews(
    competitor: str = Query("Salesforce", description="Competitor name"),
    topic: str | None = Query(None, max_length=200, description="Exact topic_label"),
    month: str | None = Query(None, pattern=r"^\d{4}-(0[1-9]|1[0-2])$", description="YYYY-MM"),
    sort: Literal["negative", "positive", "recent"] = "negative",
    limit: int = Query(10, ge=1, le=50),
):
    try:
        result = get_reviews(known_competitor(competitor), topic, month, sort, limit)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {"competitor": competitor, "topic": topic, "month": month, **result}
