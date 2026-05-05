"""M05 — Trigger Alerts: detect competitor vulnerability signals and draft outreach."""

import logging
import os
from dataclasses import dataclass, field
from datetime import datetime

import pandas as pd

from database.db import query_df
from utils.llm import get_client, retry_with_backoff

logger = logging.getLogger(__name__)

_NEGATIVE_KEYWORDS = ["outage", "lawsuit", "layoffs", "breach", "downtime", "fired", "hack"]
_SENTIMENT_DROP_THRESHOLD = -0.5
_REVIEW_SPIKE_MULTIPLIER = 2.0
_MODEL = "claude-sonnet-4-6"

# SQL anchors on MAX(date) in the dataset so fixture data works correctly.
_SENTIMENT_SQL = """
    SELECT AVG(sentiment_delta) AS avg_delta
    FROM processed_reviews
    WHERE competitor_name = ?
      AND date >= date(
              (SELECT MAX(date) FROM processed_reviews WHERE competitor_name = ?),
              '-7 days'
          )
"""

_NEWS_SQL = """
    SELECT review_text, date
    FROM processed_reviews
    WHERE competitor_name = ?
      AND source = 'newsapi'
      AND date >= date(
              (SELECT MAX(date) FROM processed_reviews
               WHERE competitor_name = ? AND source = 'newsapi'),
              '-2 days'
          )
    ORDER BY date DESC
    LIMIT 50
"""

_SPIKE_RECENT_SQL = """
    SELECT COUNT(*) AS count
    FROM processed_reviews
    WHERE competitor_name = ?
      AND date >= date(
              (SELECT MAX(date) FROM processed_reviews WHERE competitor_name = ?),
              '-7 days'
          )
"""

_SPIKE_BASELINE_SQL = """
    SELECT COUNT(*) AS count
    FROM processed_reviews
    WHERE competitor_name = ?
      AND date >= date(
              (SELECT MAX(date) FROM processed_reviews WHERE competitor_name = ?),
              '-37 days'
          )
      AND date < date(
              (SELECT MAX(date) FROM processed_reviews WHERE competitor_name = ?),
              '-7 days'
          )
"""

_OUTREACH_TEMPLATES: dict[str, str] = {
    "sentiment_drop": (
        "Hi [Name],\n\n"
        "I noticed {competitor} has been receiving significantly more negative feedback "
        "from their customers over the past week. If your team is feeling that friction or "
        "starting to evaluate alternatives, I'd love to show you how we compare.\n\n"
        "Would a quick 15-minute call this week work?\n\nBest,"
    ),
    "negative_news": (
        "Hi [Name],\n\n"
        "I saw the recent news around {competitor} — moments like these often prompt teams "
        "to review their vendor stack. We've helped several {competitor} customers transition "
        "smoothly, and I'd be happy to share how we could do the same for you.\n\n"
        "Worth a brief conversation?\n\nBest,"
    ),
    "review_spike": (
        "Hi [Name],\n\n"
        "There's been an unusual spike in {competitor} customer complaints recently — "
        "usually a sign of broader friction in the platform. If your team is feeling the same "
        "pain, we'd love to show you a better alternative.\n\n"
        "Open to a quick call?\n\nBest,"
    ),
}


@dataclass
class Alert:
    """A detected competitor vulnerability signal."""

    trigger_type: str       # "sentiment_drop" | "negative_news" | "review_spike"
    competitor: str
    evidence_summary: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    outreach_draft: str = ""


# ── Internal signal detectors ─────────────────────────────────────────────────


def _check_sentiment_drop(competitor: str) -> Alert | None:
    df = query_df(_SENTIMENT_SQL, (competitor, competitor))
    if df.empty or pd.isna(df["avg_delta"].iloc[0]):
        return None
    avg_delta = float(df["avg_delta"].iloc[0])
    if avg_delta < _SENTIMENT_DROP_THRESHOLD:
        return Alert(
            trigger_type="sentiment_drop",
            competitor=competitor,
            evidence_summary=(
                f"Avg sentiment delta {avg_delta:+.3f} in last 7 days "
                f"(threshold: {_SENTIMENT_DROP_THRESHOLD})"
            ),
        )
    return None


def _check_negative_news(competitor: str) -> Alert | None:
    df = query_df(_NEWS_SQL, (competitor, competitor))
    if df.empty:
        return None
    for _, row in df.iterrows():
        text_lower = str(row["review_text"]).lower()
        matched = [kw for kw in _NEGATIVE_KEYWORDS if kw in text_lower]
        if matched:
            headline = str(row["review_text"])[:120]
            return Alert(
                trigger_type="negative_news",
                competitor=competitor,
                evidence_summary=(
                    f"News article with keywords {matched} on {row['date']}: "
                    f'"{headline}..."'
                ),
            )
    return None


def _check_review_spike(competitor: str) -> Alert | None:
    recent_df = query_df(_SPIKE_RECENT_SQL, (competitor, competitor))
    baseline_df = query_df(_SPIKE_BASELINE_SQL, (competitor, competitor, competitor))

    if recent_df.empty or baseline_df.empty:
        return None

    recent_count = float(recent_df["count"].iloc[0])
    baseline_count = float(baseline_df["count"].iloc[0])

    # Baseline covers 30 days; daily_avg × 7 = expected 7-day volume
    daily_avg = baseline_count / 30.0
    expected_7d = daily_avg * 7

    if expected_7d > 0 and recent_count > expected_7d * _REVIEW_SPIKE_MULTIPLIER:
        return Alert(
            trigger_type="review_spike",
            competitor=competitor,
            evidence_summary=(
                f"{int(recent_count)} reviews in last 7 days vs "
                f"expected {expected_7d:.1f} "
                f"({_REVIEW_SPIKE_MULTIPLIER:.0f}× spike threshold)"
            ),
        )
    return None


def _build_slack_payload(alert: Alert) -> dict:
    alert_label = {
        "sentiment_drop": "[Sentiment Drop]",
        "negative_news": "[Negative News]",
        "review_spike": "[Review Spike]",
    }.get(alert.trigger_type, "[Alert]")
    ts = alert.timestamp.strftime("%Y-%m-%d %H:%M UTC")
    return {
        "blocks": [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"{alert_label} RivalSense Alert: {alert.competitor}",
                },
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*Type:* `{alert.trigger_type}`"},
                    {"type": "mrkdwn", "text": f"*Detected:* {ts}"},
                ],
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Evidence:* {alert.evidence_summary}",
                },
            },
            {"type": "divider"},
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Suggested outreach:*\n{alert.outreach_draft or '_Not yet generated._'}",
                },
            },
        ]
    }


# ── Public API ────────────────────────────────────────────────────────────────


def check_triggers(competitor_list: list[str]) -> list[Alert]:
    """Scan for all three signal types across the given competitors.

    Signal 1: avg sentiment_delta < -0.5 in last 7 days.
    Signal 2: NewsAPI article containing a negative keyword in last 48 h.
    Signal 3: Review count spike > 2× the 30-day daily average.

    Uses MAX(date) per competitor as the anchor so fixture data works correctly.

    Args:
        competitor_list: Competitor names to scan.

    Returns:
        List of Alert objects (empty if no signals detected).
    """
    alerts: list[Alert] = []
    checkers = (_check_sentiment_drop, _check_negative_news, _check_review_spike)

    for competitor in competitor_list:
        for checker in checkers:
            try:
                alert = checker(competitor)
                if alert is not None:
                    alerts.append(alert)
                    logger.info(
                        "Alert detected: %s / %s", competitor, alert.trigger_type
                    )
            except Exception as exc:  # noqa: BLE001
                logger.warning(
                    "Signal check failed for %s (%s): %s",
                    competitor, checker.__name__, exc,
                )

    return alerts


@retry_with_backoff
def _call_claude_outreach(alert: Alert) -> str:
    client = get_client()
    prompt = (
        f"Write a brief, warm B2B sales outreach email body (3–4 sentences max) "
        f"for this situation:\n\n"
        f"Competitor: {alert.competitor}\n"
        f"Signal type: {alert.trigger_type}\n"
        f"Evidence: {alert.evidence_summary}\n\n"
        f"Be empathetic, reference the specific situation, and include a soft call to action. "
        f"Return only the email body — no subject line, no greeting salutation."
    )
    response = client.messages.create(
        model=_MODEL,
        max_tokens=300,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text


def generate_outreach(alert: Alert, llm: bool = True) -> str:
    """Draft an outreach message for a detected alert.

    Args:
        alert: Alert returned by check_triggers().
        llm: If True, call Claude API for a personalised draft.
             If False, use a template substitution (faster, no API cost).

    Returns:
        Outreach message string.
    """
    if llm:
        try:
            return _call_claude_outreach(alert)
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "LLM outreach generation failed for %s — falling back to template: %s",
                alert.competitor, exc,
            )

    template = _OUTREACH_TEMPLATES.get(
        alert.trigger_type,
        "Hi [Name],\n\nI noticed some changes around {competitor} recently — "
        "would love to chat if you're evaluating alternatives.\n\nBest,",
    )
    return template.format(competitor=alert.competitor)


def send_slack_alert(alert: Alert) -> None:
    """Post an alert to the configured Slack webhook.

    Reads SLACK_WEBHOOK_URL from environment. Silently skips if not set.

    Args:
        alert: Alert object (outreach_draft should already be populated).
    """
    from outputs.slack_webhook import post_message

    webhook_url = os.getenv("SLACK_WEBHOOK_URL", "")
    if not webhook_url:
        logger.warning(
            "SLACK_WEBHOOK_URL not set — Slack notification skipped for %s / %s.",
            alert.competitor, alert.trigger_type,
        )
        return

    payload = _build_slack_payload(alert)
    post_message(webhook_url, payload)
    logger.info(
        "Slack alert sent: %s / %s", alert.competitor, alert.trigger_type
    )
