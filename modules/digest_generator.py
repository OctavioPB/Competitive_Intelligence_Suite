"""M08 — Intelligence Digest: Claude-synthesised weekly executive brief."""

import json
import logging
from datetime import datetime, timedelta, timezone

from database.db import execute, query_df
from utils.llm import get_client, retry_with_backoff

logger = logging.getLogger(__name__)

_MODEL = "claude-sonnet-4-6"

# ── SQL ───────────────────────────────────────────────────────────────────────

_SENTIMENT_DELTA_SQL = """
    SELECT
        AVG(CASE WHEN date >= ? THEN sentiment_score END) AS recent_avg,
        AVG(CASE WHEN date >= ? AND date < ? THEN sentiment_score END) AS prior_avg
    FROM processed_reviews
    WHERE competitor_name = ?
      AND source NOT IN ('newsapi')
"""

_TOP_PAIN_SQL = """
    SELECT topic_label, COUNT(*) AS cnt
    FROM processed_reviews
    WHERE competitor_name = ?
      AND topic_cluster >= 0
      AND topic_label NOT IN ('misc', 'insufficient_data')
      AND date >= ?
    GROUP BY topic_label
    ORDER BY cnt DESC
    LIMIT 1
"""

_LATEST_DIGEST_SQL = "SELECT report_json FROM digests ORDER BY id DESC LIMIT 1"
_DIGEST_HISTORY_SQL = "SELECT id, generated_at FROM digests ORDER BY id DESC LIMIT 20"
_INSERT_DIGEST_SQL  = "INSERT INTO digests (generated_at, report_json) VALUES (?, ?)"

# ── Prompts ───────────────────────────────────────────────────────────────────

_SYSTEM_PROMPT = """\
You are a B2B revenue intelligence analyst writing a Monday morning brief for a \
VP of Sales. You receive a structured snapshot of competitive data across multiple \
competitors and must synthesise it into an executive digest.

Return ONLY valid JSON. No markdown fences. No preamble. Schema:

{
  "generated_at": "<ISO 8601 UTC>",
  "overall_theme": "<1 sentence — the single most important competitive story this week>",
  "per_competitor": [
    {
      "name": "<competitor name>",
      "sentiment_delta": <float — change in avg sentiment vs prior period>,
      "sentiment_signal": "<improving|declining|stable>",
      "top_pain": "<top pain point topic in plain English>",
      "summary": "<2 sentence narrative of this competitor's competitive status>",
      "action_bullets": [
        "<concrete action the sales team should take — start with a verb>",
        "<second action>",
        "<third action>"
      ]
    }
  ],
  "top_alert": "<1-sentence description of the most urgent alert this week, or null>",
  "top_lead": "<1-sentence description of the highest-urgency prospect lead, or null>"
}

Rules:
- overall_theme must be opinionated and specific — not generic
- action_bullets must be concrete and actionable (e.g. "Lead with TCO comparison against Salesforce's latest pricing change")
- sentiment_signal: improving if delta > 0.05, declining if < -0.05, else stable
- If no alert or lead data, use null
"""

_USER_PROMPT_TEMPLATE = """\
Generate a competitive intelligence digest for this week.

COMPETITOR DATA:
{competitor_lines}

ALERTS THIS WEEK: {alert_summary}

TOP PROSPECT LEAD: {lead_summary}

Generate the digest JSON now.
"""


# ── Internal helpers ──────────────────────────────────────────────────────────


def _sentiment_delta(competitor: str, window_days: int = 30) -> tuple[float, float]:
    """Return (recent_avg, prior_avg) sentiment for a competitor."""
    now         = datetime.now(timezone.utc)
    recent_from = (now - timedelta(days=window_days)).strftime("%Y-%m-%d")
    prior_from  = (now - timedelta(days=2 * window_days)).strftime("%Y-%m-%d")

    row = query_df(
        _SENTIMENT_DELTA_SQL,
        (recent_from, prior_from, recent_from, competitor),
    )
    if row.empty:
        return 0.0, 0.0
    recent = float(row.iloc[0]["recent_avg"] or 0.0)
    prior  = float(row.iloc[0]["prior_avg"]  or 0.0)
    return round(recent, 4), round(prior, 4)


def _top_pain(competitor: str, window_days: int = 30) -> str:
    since = (datetime.now(timezone.utc) - timedelta(days=window_days)).strftime("%Y-%m-%d")
    row   = query_df(_TOP_PAIN_SQL, (competitor, since))
    if row.empty:
        return "insufficient data"
    return str(row.iloc[0]["topic_label"]).replace("_", " ")


@retry_with_backoff
def _call_claude(system: str, user: str) -> str:
    client   = get_client()
    response = client.messages.create(
        model=_MODEL,
        max_tokens=2048,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    logger.info(
        "Digest token usage: %d in + %d out",
        response.usage.input_tokens,
        response.usage.output_tokens,
    )
    return response.content[0].text


def _parse_digest(raw: str) -> dict:
    text = raw.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        text  = "\n".join(lines[1:-1]) if len(lines) > 2 else text
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        logger.error("Digest JSON parse failed. Raw: %.500s", raw)
        raise ValueError("Failed to parse digest JSON") from exc


def _store_digest(data: dict) -> None:
    """Persist digest to SQLite digests table."""
    try:
        execute(
            _INSERT_DIGEST_SQL,
            (data.get("generated_at", ""), json.dumps(data, ensure_ascii=False)),
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("Could not store digest: %s", exc)


# ── Public API ────────────────────────────────────────────────────────────────


def load_latest_digest() -> dict | None:
    """Return the most recently stored digest, or None."""
    try:
        row = query_df(_LATEST_DIGEST_SQL)
        if row.empty:
            return None
        return json.loads(str(row.iloc[0]["report_json"]))
    except Exception as exc:  # noqa: BLE001
        logger.warning("Could not load latest digest: %s", exc)
        return None


def list_digest_history() -> list[dict]:
    """Return a list of {id, generated_at} for past digests."""
    try:
        df = query_df(_DIGEST_HISTORY_SQL)
        return df.to_dict(orient="records") if not df.empty else []
    except Exception as exc:  # noqa: BLE001
        logger.warning("Could not list digest history: %s", exc)
        return []


def generate_digest(competitor_names: list[str]) -> dict:
    """Generate a Claude-synthesised executive digest across all competitors.

    Args:
        competitor_names: List of competitor names to include.

    Returns:
        Digest dict with keys: generated_at, overall_theme, per_competitor,
        top_alert, top_lead.
    """
    from config import COMPETITOR_NAMES, SUBREDDITS
    from modules.trigger_alerts import check_triggers

    # ── Collect competitor intelligence ───────────────────────────────────────
    competitor_lines = []
    for name in competitor_names:
        recent_avg, prior_avg = _sentiment_delta(name)
        delta     = round(recent_avg - prior_avg, 4)
        top_pain  = _top_pain(name)
        competitor_lines.append(
            f"  {name}:\n"
            f"    sentiment_delta={delta:+.3f} (recent={recent_avg:.3f}, prior={prior_avg:.3f})\n"
            f"    top_pain_point: {top_pain}"
        )

    # ── Collect alerts ────────────────────────────────────────────────────────
    try:
        alerts = check_triggers(competitor_names)
        alert_summary = (
            f"{len(alerts)} alert(s): "
            + "; ".join(f"{a.competitor}/{a.trigger_type}" for a in alerts[:3])
            if alerts else "none"
        )
        top_alert_raw = (
            f"{alerts[0].competitor} — {alerts[0].trigger_type}: {alerts[0].evidence_summary}"
            if alerts else None
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("Alert check failed in digest: %s", exc)
        alert_summary  = "unavailable"
        top_alert_raw  = None

    # ── Collect top prospect ──────────────────────────────────────────────────
    try:
        from modules.hot_prospect_finder import enrich_lead, score_urgency

        _FIXTURE_POST = {
            "source": "reddit", "post_id": "dgst01",
            "username": "top_prospect",
            "post_text": "Switching from Salesforce — pricing is insane and support is terrible.",
            "post_url": "https://reddit.com/r/CRM/comments/example",
            "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "competitor_name": "Salesforce",
            "upvotes": 50, "num_comments": 20, "sentiment_score": -0.75,
        }
        _FIXTURE_POST["urgency_score"] = score_urgency(_FIXTURE_POST)
        lead = enrich_lead(_FIXTURE_POST)
        top_lead_raw = (
            f"{lead['username']} (urgency={lead['urgency_score']:.2f}): "
            f"{lead['complaint_summary'][:100]}"
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("Lead enrichment failed in digest: %s", exc)
        top_lead_raw = None

    # ── Build prompt ──────────────────────────────────────────────────────────
    user_prompt = _USER_PROMPT_TEMPLATE.format(
        competitor_lines="\n".join(competitor_lines),
        alert_summary=alert_summary,
        lead_summary=top_lead_raw or "none",
    )

    logger.info("Generating digest for %d competitors ...", len(competitor_names))
    raw    = _call_claude(_SYSTEM_PROMPT, user_prompt)
    digest = _parse_digest(raw)

    digest.setdefault("generated_at", datetime.now(timezone.utc).isoformat())
    digest.setdefault("overall_theme", "")
    digest.setdefault("per_competitor", [])
    digest.setdefault("top_alert", top_alert_raw)
    digest.setdefault("top_lead",  top_lead_raw)

    _store_digest(digest)
    return digest
