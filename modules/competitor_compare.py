"""Every competitor side by side: sentiment, pain points, churn and signals.

Reuses each module's own query so the numbers match what the single-competitor
pages show; nothing new is computed here except the 30-day sentiment window.
"""

from __future__ import annotations

from typing import Any

import pandas as pd

from database.db import query_df
from modules.pain_point_radar import get_pain_points
from modules.sentiment_timeline import build_timeline

_WINDOW_DAYS = 30
_TIMELINE_MONTHS = 12

_SUMMARY_SQL = """
    WITH anchor AS (SELECT MAX(date) AS d FROM processed_reviews WHERE competitor_name = :c)
    SELECT
        COUNT(*) AS total,
        SUM(is_synthetic) AS synthetic,
        (SELECT d FROM anchor) AS latest_date,
        SUM(CASE WHEN date > date((SELECT d FROM anchor), :w) THEN 1 ELSE 0 END) AS recent_n,
        AVG(CASE WHEN date > date((SELECT d FROM anchor), :w) THEN sentiment_score END) AS recent_s,
        AVG(CASE WHEN date <= date((SELECT d FROM anchor), :w)
                  AND date > date((SELECT d FROM anchor), :w2) THEN sentiment_score END) AS prior_s,
        AVG(CASE WHEN date > date((SELECT d FROM anchor), :w) THEN rating END) AS recent_r
    FROM processed_reviews
    WHERE competitor_name = :c
"""


def _num(value: Any, digits: int = 3) -> float | None:
    return None if value is None or pd.isna(value) else round(float(value), digits)


def _summary(name: str) -> dict[str, Any]:
    row = query_df(_SUMMARY_SQL, {
        "c": name, "w": f"-{_WINDOW_DAYS} days", "w2": f"-{2 * _WINDOW_DAYS} days",
    }).to_dict("records")[0]
    total = int(row["total"] or 0)
    recent, prior = _num(row["recent_s"]), _num(row["prior_s"])
    return {
        "reviews_total": total,
        "synthetic_share": round(int(row["synthetic"] or 0) / total, 3) if total else 0.0,
        "latest_date": row["latest_date"],
        "reviews_30d": int(row["recent_n"] or 0),
        "sentiment_30d": recent,
        "sentiment_prev_30d": prior,
        "sentiment_change": None if recent is None or prior is None else round(recent - prior, 3),
        "rating_30d": _num(row["recent_r"], 2),
    }


def _pain(name: str) -> list[dict[str, Any]]:
    df = get_pain_points(name, top_n=3)
    return [
        {
            "topic": r["topic_label"],
            "severity": float(r["avg_severity"]),
            "mentions": int(r["mention_count"]),
            "trend": r["trend_direction"],
        }
        for r in df.to_dict("records")
    ]


def _timeline(name: str) -> list[dict[str, Any]]:
    df = build_timeline(name, _TIMELINE_MONTHS)
    return [
        {"month": str(r["month"]), "avg_sentiment": _num(r["avg_sentiment"])}
        for r in df.to_dict("records")
        if _num(r["avg_sentiment"]) is not None
    ]


def _churn(name: str) -> list[dict[str, Any]] | None:
    from modules.churn_reason_intelligence import load_cached_analysis

    analysis = load_cached_analysis(name)
    if not analysis:
        return None
    return [
        {"label": b.get("label"), "mention_pct": b.get("mention_pct"), "trend": b.get("trend_direction")}
        for b in analysis.get("buckets", [])[:3]
    ]


def _signals(name: str) -> dict[str, Any]:
    """Active alerts and market signals; missing tables simply mean "none yet"."""
    out: dict[str, Any] = {"active_alerts": 0, "last_price_change": None, "support_share": None, "new_roles": 0}
    try:
        from modules.alert_history import list_alerts

        out["active_alerts"] = sum(
            a["status"] != "dismissed" for a in list_alerts(competitor=name, active_only=True)
        )
    except Exception:  # noqa: BLE001
        pass
    try:
        from modules.market_signals import get_hiring_overview, get_pricing_overview

        dates = [p["last_change"]["date"] for p in get_pricing_overview(name)["pages"] if p["last_change"]]
        out["last_price_change"] = max(dates) if dates else None
        hiring = get_hiring_overview(name)
        if hiring["new_roles"]:
            support = next((c["new"] for c in hiring["by_category"] if c["category"] == "support"), 0)
            out["support_share"] = round(support / hiring["new_roles"], 3)
            out["new_roles"] = hiring["new_roles"]
    except Exception:  # noqa: BLE001
        pass
    return out


def compare_competitors(names: list[str]) -> dict[str, Any]:
    return {
        "window_days": _WINDOW_DAYS,
        "competitors": [
            {
                "name": name,
                **_summary(name),
                "pain_points": _pain(name),
                "churn": _churn(name),
                "timeline": _timeline(name),
                **_signals(name),
            }
            for name in names
        ],
    }
