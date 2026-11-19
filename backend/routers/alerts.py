"""Alerts router — competitor vulnerability trigger alerts."""

from datetime import datetime, timezone

from fastapi import APIRouter
from pydantic import BaseModel

from backend.deps import known_competitor
from config import COMPETITOR_NAMES
from modules.trigger_alerts import Alert, check_triggers, generate_outreach

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


@router.get("/alerts/demo")
def get_demo_alerts():
    """Return the hardcoded bad-week demo scenario."""
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
        ts = datetime.now(timezone.utc)

    alert = Alert(
        trigger_type=body.trigger_type,
        competitor=known_competitor(body.competitor),
        evidence_summary=body.evidence_summary,
        timestamp=ts,
        outreach_draft=body.outreach_draft or "",
    )
    draft = generate_outreach(alert, llm=body.use_llm)
    return {"draft": draft}
