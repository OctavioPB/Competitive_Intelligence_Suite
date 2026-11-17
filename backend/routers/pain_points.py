"""Pain Points router — competitor pain point radar."""

from fastapi import APIRouter, Query

from backend.deps import json_safe, known_competitor
from modules.pain_point_radar import get_pain_points

router = APIRouter(tags=["pain-points"])


@router.get("/pain-points")
def pain_points(
    competitor: str = Query("Salesforce", description="Competitor name"),
    top_n: int = Query(10, ge=1, le=50, description="Number of pain points to return"),
):
    df = get_pain_points(known_competitor(competitor), top_n)

    points = [
        {
            "topic_label": str(row.topic_label),
            "mention_count": int(row.mention_count),
            "avg_severity": json_safe(float(row.avg_severity)),
            "trend_direction": str(row.trend_direction),
        }
        for row in df.itertuples(index=False)
    ]

    return {"competitor": competitor, "points": points}
