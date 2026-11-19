"""Alerts router — competitor vulnerability trigger alerts."""

import logging
import sqlite3
from datetime import datetime, timezone
from typing import Literal

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from backend.deps import known_competitor
from config import COMPETITOR_NAMES
from modules.alert_history import (
    UnknownAlertError,
    list_alerts,
    mark_all_seen,
    record_alerts,
    save_draft,
    set_status,
    status_counts,
)
from modules.trigger_alerts import Alert, check_triggers, generate_outreach

logger = logging.getLogger(__name__)
router = APIRouter(tags=["alerts"])


def _alert_to_dict(alert: Alert) -> dict:
    """Serialise an Alert dataclass to a JSON-safe dict."""
    ts = alert.timestamp
    ts_str = ts.isoformat() if isinstance(ts, datetime) else str(ts)

    return {
        "trigger_type": alert.trigger_type,
        "competitor": alert.competitor,
        "evidence_summary": alert.evidence_summary,
        "timestamp": ts_str,
        "outreach_draft": alert.outreach_draft or None,
    }


def _demo_alerts() -> list[Alert]:
    """Return the hardcoded bad-week demo fixture."""
    ts = datetime(2025, 12, 27, 9, 0, 0)
    return [
        Alert(
            trigger_type="sentiment_drop",
            competitor="Salesforce",
            evidence_summary="Avg sentiment delta -0.71 in last 7 days (threshold: -0.5)",
            timestamp=ts,
            outreach_draft=(
                "Hi [Name],\n\n"
                "Salesforce has been receiving significantly more negative feedback this week — "
                "many customers cite cost and support response times. If your team is feeling "
                "that friction, we'd love to show you how we compare.\n\n"
                "Open to a quick 15-minute call?\n\nBest,"
            ),
        ),
        Alert(
            trigger_type="negative_news",
            competitor="Salesforce",
            evidence_summary=(
                "News article with keywords ['outage'] on 2025-12-26: "
                '"Major Salesforce outage affecting thousands of enterprise customers..."'
            ),
            timestamp=ts,
            outreach_draft=(
                "Hi [Name],\n\n"
                "I saw the news around Salesforce's outage this week — moments like these "
                "often prompt teams to review their CRM vendor. We've helped several "
                "Salesforce customers transition smoothly and I'd be happy to share how.\n\n"
                "Worth a brief conversation?\n\nBest,"
            ),
        ),
        Alert(
            trigger_type="pricing_change",
            competitor="HubSpot",
            evidence_summary=(
                "Pricing page changed on 2025-12-29 (hubspot.com/pricing/sales): "
                "Starter: $15 /mo/seat → $20 /mo/seat; Professional: $90 /mo/seat → $100 /mo/seat; "
                "New Onboarding fee (Professional): $1,500"
            ),
            timestamp=ts,
            outreach_draft=(
                "Hi [Name],\n\n"
                "HubSpot just raised Sales Hub Professional to $100 per seat and added an "
                "onboarding fee. If your renewal is coming up, it's a good moment to compare — "
                "we'd be happy to put together a side-by-side on total cost.\n\n"
                "Worth 15 minutes?\n\nBest,"
            ),
        ),
        Alert(
            trigger_type="hiring_signal",
            competitor="Salesforce",
            evidence_summary=(
                "11 of 20 roles opened in the last 30 days are customer support / success (55%) "
                "— a sign their support is under strain."
            ),
            timestamp=ts,
            outreach_draft=(
                "Hi [Name],\n\n"
                "Salesforce is hiring support staff at an unusual pace right now — usually a sign "
                "ticket queues are long. If your team is waiting on answers, we'd be glad to show "
                "how fast our support responds.\n\n"
                "Open to a quick call?\n\nBest,"
            ),
        ),
        Alert(
            trigger_type="review_spike",
            competitor="HubSpot",
            evidence_summary="42 reviews in last 7 days vs expected 18.0 (2× spike threshold)",
            timestamp=ts,
            outreach_draft=(
                "Hi [Name],\n\n"
                "There's been an unusual spike in HubSpot customer complaints this week — "
                "typically a sign of broader platform friction. If your team is considering "
                "alternatives, we'd love to show you what we offer.\n\n"
                "Open to a quick call?\n\nBest,"
            ),
        ),
    ]


class OutreachRequest(BaseModel):
    competitor: str
    trigger_type: str
    evidence_summary: str
    timestamp: str
    outreach_draft: str | None = None
    use_llm: bool = False
    alert_id: int | None = None        # when set, the draft is saved on that history row


class StatusRequest(BaseModel):
    status: Literal["new", "seen", "dismissed"]


class MarkSeenRequest(BaseModel):
    competitor: str | None = None


def _history_to_dict(row: dict, timestamp: str) -> dict:
    """A history row in the shape the Alerts page already renders, plus workflow fields."""
    return {
        "trigger_type": row["trigger_type"],
        "competitor": row["competitor"],
        "evidence_summary": row["evidence_summary"],
        "timestamp": timestamp,
        "outreach_draft": row["outreach_draft"],
        "id": row["id"],
        "status": row["status"],
        "is_new": row.get("is_new", False),
        "first_seen": row["first_seen"],
        "last_seen": row["last_seen"],
        "times_seen": row["times_seen"],
        "is_synthetic": row["is_synthetic"],
    }


@router.get("/alerts/demo")
def get_demo_alerts():
    """Return the hardcoded bad-week demo scenario (not stored in the history)."""
    return [_alert_to_dict(a) for a in _demo_alerts()]


@router.post("/alerts/scan")
def scan_alerts():
    """Run trigger checks across all competitors and record them in the history.

    An alert already detected during the last 7 days keeps its id and status, so
    re-scanning never turns a seen or dismissed alert back into a new one.
    """
    alerts = check_triggers(COMPETITOR_NAMES)
    now = datetime.now(timezone.utc).isoformat()
    try:
        rows = record_alerts(alerts)
    except sqlite3.Error as exc:
        # The detections matter more than their bookkeeping — return them unstored.
        logger.warning("Could not store alerts in the history: %s", exc)
        return [{**_alert_to_dict(a), "id": None, "status": None} for a in alerts]
    return [_history_to_dict(row, now) for row in rows]


@router.get("/alerts/history")
def alert_history(
    status: Literal["new", "seen", "dismissed"] | None = None,
    competitor: str | None = None,
    active: bool = False,
    limit: int = Query(200, ge=1, le=1000),
):
    """Stored alerts, most recently seen first, with counts per status."""
    name = known_competitor(competitor) if competitor else None
    rows = list_alerts(status=status, competitor=name, active_only=active, limit=limit)
    return {
        "alerts": [_history_to_dict(r, f"{r['last_seen']}T00:00:00") for r in rows],
        "counts": status_counts(),
    }


@router.post("/alerts/{alert_id}/status")
def update_alert_status(alert_id: int, body: StatusRequest):
    try:
        row = set_status(alert_id, body.status)
    except UnknownAlertError as exc:
        raise HTTPException(status_code=404, detail=f"No alert with id {alert_id}") from exc
    return _history_to_dict(row, f"{row['last_seen']}T00:00:00")


@router.post("/alerts/mark-seen")
def mark_seen(body: MarkSeenRequest):
    """Mark every new alert (optionally of one competitor) as seen."""
    name = known_competitor(body.competitor) if body.competitor else None
    return {"updated": mark_all_seen(name)}


@router.post("/alerts/outreach")
def draft_outreach(body: OutreachRequest):
    """Reconstruct an Alert and generate (or template) an outreach draft."""
    try:
        ts = datetime.fromisoformat(body.timestamp)
    except ValueError:
        ts = datetime.now(timezone.utc)

    alert = Alert(
        trigger_type=body.trigger_type,
        competitor=known_competitor(body.competitor),
        evidence_summary=body.evidence_summary,
        timestamp=ts,
        outreach_draft=body.outreach_draft or "",
    )
    draft = generate_outreach(alert, llm=body.use_llm)
    if body.alert_id is not None:
        save_draft(body.alert_id, draft)
    return {"draft": draft}
