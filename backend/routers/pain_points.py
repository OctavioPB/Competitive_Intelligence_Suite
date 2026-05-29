"""Pain Points router — competitor pain point radar."""

import math

from fastapi import APIRouter, Query

from modules.pain_point_radar import get_pain_points

router = APIRouter(tags=["pain-points"])


def _safe(value):
    """Convert NaN/inf to None for JSON serialisation."""
    if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
        return None
    return value


@router.get("/pain-points")
def pain_points(
    competitor: str = Query("Salesforce", description="Competitor name"),
    top_n: int = Query(10, ge=1, le=50, description="Number of pain points to return"),
):
    df = get_pain_points(competitor, top_n)
    if df.empty:
        return {"competitor": competitor, "points": []}

    points = []
    for _, row in df.iterrows():
        points.append(
            {
                "topic_label": str(row["topic_label"]),
                "mention_count": int(row["mention_count"]),
                "avg_severity": _safe(float(row["avg_severity"])),
                "trend_direction": str(row["trend_direction"]),
                "trend_icon": str(row.get("trend_icon", "")),
            }
        )

    return {"competitor": competitor, "points": points}
