"""Sentiment router — competitor sentiment timeline."""

from fastapi import APIRouter, Query

from backend.deps import json_safe, known_competitor
from modules.sentiment_timeline import build_timeline

router = APIRouter(tags=["sentiment"])


@router.get("/sentiment")
def sentiment_timeline(
    competitor: str = Query("Salesforce", description="Competitor name"),
    months: int = Query(18, ge=1, le=60, description="Number of months to include"),
):
    df = build_timeline(known_competitor(competitor), months)

    timeline = [
        {
            "month": str(row.month),
            "avg_sentiment": json_safe(float(row.avg_sentiment)),
            "stddev": json_safe(float(row.stddev)),
            "review_count": int(row.review_count),
            "top_event": row.top_event if isinstance(row.top_event, str) else None,
        }
        for row in df.itertuples(index=False)
    ]

    return {"competitor": competitor, "months": months, "timeline": timeline}
