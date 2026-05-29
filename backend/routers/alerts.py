"""Alerts router — competitor vulnerability trigger alerts."""

from datetime import datetime

from fastapi import APIRouter
from pydantic import BaseModel

from config import COMPETITOR_NAMES
from modules.trigger_alerts import Alert, check_triggers, generate_outreach

router = APIRouter(tags=["alerts"])


def _alert_to_dict(alert: Alert) -> dict:
    """Serialise an Alert dataclass to a JSON-safe dict."""
    ts = alert.timestamp
    if isinstance(ts, datetime):
        ts_str = ts.isoformat()
    else:
        ts_str = str(ts)

    return {
        "trigger_type": alert.trigger_type,
        "competitor": alert.competitor,
        "evidence_summary": alert.evidence_summary,
        "timestamp": ts_str,
        "outreach_draft": alert.outreach_draft if alert.outreach_draft else None,
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


@router.get("/alerts/demo")
def get_demo_alerts():
    """Return the hardcoded bad-week demo scenario (3 alerts)."""
    return [_alert_to_dict(a) for a in _demo_alerts()]


@router.post("/alerts/scan")
def scan_alerts():
    """Run live trigger checks across all configured competitors."""
    alerts = check_triggers(COMPETITOR_NAMES)
    return [_alert_to_dict(a) for a in alerts]


@router.post("/alerts/outreach")
def draft_outreach(body: OutreachRequest):
    """Reconstruct an Alert and generate (or template) an outreach draft."""
    try:
        ts = datetime.fromisoformat(body.timestamp)
    except ValueError:
        ts = datetime.utcnow()

    alert = Alert(
        trigger_type=body.trigger_type,
        competitor=body.competitor,
        evidence_summary=body.evidence_summary,
        timestamp=ts,
        outreach_draft=body.outreach_draft or "",
    )
    draft = generate_outreach(alert, llm=body.use_llm)
    return {"draft": draft}
