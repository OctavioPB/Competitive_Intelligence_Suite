"""M05 — Trigger Alerts: detect competitor vulnerability signals and draft outreach."""

import logging
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger(__name__)

_NEGATIVE_KEYWORDS = ["outage", "lawsuit", "layoffs", "breach", "downtime", "fired"]
_SENTIMENT_DROP_THRESHOLD = -0.5
_REVIEW_SPIKE_MULTIPLIER = 2.0


@dataclass
class Alert:
    """A detected competitor vulnerability signal."""

    trigger_type: str          # "sentiment_drop" | "negative_news" | "review_spike"
    competitor: str
    evidence_summary: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    outreach_draft: str = ""


def check_triggers(competitor_list: list[str]) -> list[Alert]:
    """Scan for all three signal types across the given competitors.

    Signal 1: sentiment_delta < -0.5 in last 7 days.
    Signal 2: NewsAPI article with negative keywords in last 48 h.
    Signal 3: review_count spike > 2× 30-day average in last 7 days.

    Args:
        competitor_list: List of competitor names to scan.

    Returns:
        List of Alert objects; empty list if no signals detected.
    """
    raise NotImplementedError("Implement in Sprint 5 — Day 11")


def generate_outreach(alert: Alert, llm: bool = True) -> str:
    """Draft an outreach message for a detected alert.

    Args:
        alert: Alert object returned by check_triggers().
        llm: If True, call the Claude API for a personalised draft.
              If False, use a template string substitution.

    Returns:
        Outreach message string.
    """
    raise NotImplementedError("Implement in Sprint 5 — Day 11")


def send_slack_alert(alert: Alert) -> None:
    """Post an alert to the configured Slack webhook.

    Args:
        alert: Alert object with outreach_draft populated.
    """
    raise NotImplementedError("Implement in Sprint 5 — Day 11")
