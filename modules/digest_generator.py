"""M08 — Intelligence Digest: Claude-synthesised weekly executive brief."""

import json
import logging
import os
from datetime import datetime, timezone

import pandas as pd

from database.db import execute, query_df
from utils.llm import REPAIR_SYSTEM_PROMPT, call_claude, parse_json_object

logger = logging.getLogger(__name__)

_WINDOW_DAYS = 30

# ── SQL ───────────────────────────────────────────────────────────────────────

# Both windows anchor on the competitor's MAX(date) rather than today's date, so
# the digest stays meaningful on fixture/demo data (see README, decision #2).
_SENTIMENT_DELTA_SQL = """
    WITH anchor AS (
        SELECT MAX(date) AS d FROM processed_reviews WHERE competitor_name = :competitor
    )
    SELECT
        AVG(CASE WHEN date >= date((SELECT d FROM anchor), :recent)
                 THEN sentiment_score END) AS recent_avg,
        AVG(CASE WHEN date >= date((SELECT d FROM anchor), :prior)
                  AND date <  date((SELECT d FROM anchor), :recent)
                 THEN sentiment_score END) AS prior_avg
    FROM processed_reviews
    WHERE competitor_name = :competitor
      AND source NOT IN ('newsapi')
"""

_TOP_PAIN_SQL = """
    SELECT topic_label, COUNT(*) AS cnt
    FROM processed_reviews
    WHERE competitor_name = :competitor
      AND topic_cluster >= 0
      AND topic_label NOT IN ('misc', 'insufficient_data')
      AND date >= date(
              (SELECT MAX(date) FROM processed_reviews WHERE competitor_name = :competitor),
              :recent
          )
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


def _sentiment_delta(competitor: str, window_days: int = _WINDOW_DAYS) -> tuple[float, float]:
    """Return (recent_avg, prior_avg) sentiment for a competitor."""
    row = query_df(
        _SENTIMENT_DELTA_SQL,
        {
            "competitor": competitor,
            "recent": f"-{window_days} days",
            "prior": f"-{2 * window_days} days",
        },
    )
    if row.empty:
        return 0.0, 0.0
    # AVG() over an empty window is NULL, which pandas surfaces as None or NaN.
    recent, prior = (
        0.0 if pd.isna(v) else float(v)
        for v in (row.iloc[0]["recent_avg"], row.iloc[0]["prior_avg"])
    )
    return round(recent, 4), round(prior, 4)


def _top_pain(competitor: str, window_days: int = _WINDOW_DAYS) -> str:
    row = query_df(
        _TOP_PAIN_SQL,
        {"competitor": competitor, "recent": f"-{window_days} days"},
    )
    if row.empty:
        return "insufficient data"
    return str(row.iloc[0]["topic_label"]).replace("_", " ")


def _call_claude(system: str, user: str) -> str:
    return call_claude(system, user, max_tokens=2048, label="Digest")


def _parse_digest(raw: str) -> dict:
    return parse_json_object(
        raw,
        context="digest",
        repair=lambda text: _call_claude(REPAIR_SYSTEM_PROMPT, text),
    )


def _demo_top_lead() -> str | None:
    """Return a sample prospect line for the digest — demo mode only.

    Live Reddit scanning is too slow to run inline here, and a made-up lead must
    never reach a real executive brief, so outside DEMO_MODE this returns None.
    """
    if os.getenv("DEMO_MODE", "false").lower() != "true":
        return None

    from modules.hot_prospect_finder import enrich_lead, score_urgency

    post = {
        "source": "reddit", "post_id": "dgst01",
        "username": "top_prospect",
        "post_text": "Switching from Salesforce — pricing is insane and support is terrible.",
        "post_url": "https://reddit.com/r/CRM/comments/example",
        "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "competitor_name": "Salesforce",
        "upvotes": 50, "num_comments": 20, "sentiment_score": -0.75,
    }
    post["urgency_score"] = score_urgency(post)
    lead = enrich_lead(post)
    return (
        f"{lead['username']} (urgency={lead['urgency_score']:.2f}): "
        f"{lead['complaint_summary'][:100]}"
    )


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
        top_lead_raw = _demo_top_lead()
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
