"""Sentiment router — competitor sentiment timeline."""

import math

from fastapi import APIRouter, Query

from modules.sentiment_timeline import build_timeline

router = APIRouter(tags=["sentiment"])


def _safe(value):
    """Convert NaN/inf/None to None for JSON serialisation."""
    if value is None:
        return None
    if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
        return None
    return value


@router.get("/sentiment")
def sentiment_timeline(
    competitor: str = Query("Salesforce", description="Competitor name"),
    months: int = Query(18, ge=1, le=60, description="Number of months to include"),
):
    df = build_timeline(competitor, months)
    if df.empty:
        return {"competitor": competitor, "months": months, "timeline": []}

    timeline = []
    for _, row in df.iterrows():
        timeline.append(
            {
                "month": str(row["month"]),
                "avg_sentiment": _safe(float(row["avg_sentiment"])),
                "stddev": _safe(float(row["stddev"])) if "stddev" in row else None,
                "review_count": int(row["review_count"]) if "review_count" in row else 0,
                "top_event": _safe(row.get("top_event")),
            }
        )

    return {"competitor": competitor, "months": months, "timeline": timeline}
