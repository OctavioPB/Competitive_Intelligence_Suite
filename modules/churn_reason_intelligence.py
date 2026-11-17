"""M07 — Churn Reason Intelligence: why users leave each competitor, by category."""

import json
import logging
from datetime import datetime, timezone

from config import PROJECT_ROOT
from database.db import query_df
from utils.llm import REPAIR_SYSTEM_PROMPT, call_claude, parse_json_object

logger = logging.getLogger(__name__)

_CACHE_DIR = PROJECT_ROOT / "outputs" / "churn"
_DAYS      = 180  # analyse last 6 months of reviews

BUCKET_LABELS: dict[str, str] = {
    "pricing":     "Pricing & Contract Complexity",
    "ux":          "UX & Usability Friction",
    "features":    "Missing Features & Integrations",
    "support":     "Support & Documentation Quality",
    "reliability": "Reliability & Performance",
}

# ── SQL ───────────────────────────────────────────────────────────────────────
# Windows anchor on the competitor's MAX(date), not on today's date, so the
# analysis keeps working on fixture/demo data and on DBs that are not refreshed
# daily (same convention as trigger_alerts and pain_point_radar).

_SINCE_EXPR = """date(
              (SELECT MAX(date) FROM processed_reviews WHERE competitor_name = ?),
              ?
          )"""

_TOPICS_SQL = f"""
    SELECT
        topic_label,
        COUNT(*)             AS mention_count,
        AVG(sentiment_score) AS avg_sentiment,
        GROUP_CONCAT(SUBSTR(review_text, 1, 250), '|||') AS sample_texts
    FROM processed_reviews
    WHERE competitor_name = ?
      AND date >= {_SINCE_EXPR}
      AND topic_cluster >= 0
      AND topic_label NOT IN ('misc', 'insufficient_data')
    GROUP BY topic_label
    ORDER BY mention_count DESC
    LIMIT 15
"""

_TOTAL_SQL = f"""
    SELECT COUNT(*) AS total
    FROM processed_reviews
    WHERE competitor_name = ?
      AND date >= {_SINCE_EXPR}
"""

# ── Prompts ───────────────────────────────────────────────────────────────────

_SYSTEM_PROMPT = """\
You are a B2B competitive intelligence analyst. You receive aggregated review topic data \
for a competitor product and must categorise each topic into one of five churn buckets, \
then synthesise a structured analysis.

Five churn buckets:
  pricing     — pricing, contracts, billing, cost surprise, ROI complaints, enterprise tiers
  ux          — interface friction, learning curve, slow UI, poor mobile, bad design
  features    — missing functionality, missing integrations, API limits, ignored feature requests
  support     — slow support response, poor docs, unhelpful tickets, bad onboarding
  reliability — downtime, outages, sync errors, crashes, performance degradation

Return ONLY valid JSON. No markdown fences. No preamble. Schema:

{
  "competitor": "<name>",
  "generated_at": "<ISO 8601 UTC>",
  "total_reviews_analysed": <int>,
  "buckets": [
    {
      "category": "<pricing|ux|features|support|reliability>",
      "label": "<human-readable label>",
      "mention_pct": <float 0-100, all five must sum to 100>,
      "trend_direction": "<worsening|stable|improving>",
      "proof_quotes": ["<authentic customer voice quote>", "<second quote>"]
    }
  ]
}

Rules:
- All five buckets must appear, even if mention_pct is 0
- mention_pct values must sum to exactly 100
- trend_direction: worsening if avg_sentiment < -0.35, improving if > 0.05, else stable
- proof_quotes: extract 2 real verbatim-style quotes from the sample texts; first person, specific detail
- Sort buckets by mention_pct descending
- Use the exact label strings from BUCKET_LABELS, not your own wording
"""

_USER_PROMPT_TEMPLATE = """\
Competitor: {competitor}
Analysis window: last {days} days
Total reviews in window: {total}

TOPIC CLUSTERS (from processed customer reviews):
{topic_lines}

Generate the churn reason analysis JSON now.
"""


# ── Internal helpers ──────────────────────────────────────────────────────────


def _build_user_prompt(competitor: str, df, total: int) -> str:
    lines = []
    for _, row in df.iterrows():
        label     = str(row["topic_label"]).replace("_", " ")
        count     = int(row["mention_count"])
        avg_sent  = float(row["avg_sentiment"])
        samples   = str(row["sample_texts"] or "")
        # Take first two sample quotes (split on '|||')
        quotes    = [q.strip() for q in samples.split("|||") if q.strip()][:2]
        quote_str = " | ".join(f'"{q[:120]}"' for q in quotes)
        lines.append(
            f"  - {label}: {count} mentions, avg_sentiment={avg_sent:.3f}\n"
            f"    samples: {quote_str}"
        )
    return _USER_PROMPT_TEMPLATE.format(
        competitor=competitor,
        days=_DAYS,
        total=total,
        topic_lines="\n".join(lines) if lines else "  (no topic data found)",
    )


def _call_claude(system: str, user: str) -> str:
    return call_claude(system, user, max_tokens=2048, label="Churn")


def _parse_analysis(raw: str, competitor: str, total: int) -> dict:
    data = parse_json_object(
        raw,
        context="churn",
        repair=lambda text: _call_claude(REPAIR_SYSTEM_PROMPT, text),
    )
    data.setdefault("competitor", competitor)
    data.setdefault("generated_at", datetime.now(timezone.utc).isoformat())
    data.setdefault("total_reviews_analysed", total)
    data.setdefault("buckets", [])
    return data


def _save(data: dict, competitor: str) -> None:
    _CACHE_DIR.mkdir(parents=True, exist_ok=True)
    slug    = competitor.lower().replace(" ", "_")
    payload = json.dumps(data, indent=2, ensure_ascii=False)
    (_CACHE_DIR / f"{slug}_latest.json").write_text(payload, encoding="utf-8")
    logger.info("Churn analysis cached: %s", slug)


# ── Public API ────────────────────────────────────────────────────────────────


def load_cached_analysis(competitor: str) -> dict | None:
    """Load the most recent cached churn analysis from disk, or None."""
    slug = competitor.lower().replace(" ", "_")
    path = _CACHE_DIR / f"{slug}_latest.json"
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        logger.warning("Could not load churn cache for %s: %s", competitor, exc)
        return None


def analyse_competitor(competitor: str) -> dict:
    """Analyse why users leave a competitor using Claude and recent reviews.

    Args:
        competitor: Competitor name matching processed_reviews.competitor_name.

    Returns:
        Dict with keys: competitor, generated_at, total_reviews_analysed, buckets.
        Each bucket: category, label, mention_pct, trend_direction, proof_quotes.
    """
    params = (competitor, competitor, f"-{_DAYS} days")

    total_row = query_df(_TOTAL_SQL, params)
    total     = int(total_row.iloc[0]["total"]) if not total_row.empty else 0

    df = query_df(_TOPICS_SQL, params)

    if df.empty or total == 0:
        logger.warning("[%s] No review data for churn analysis — returning stub.", competitor)
        return {
            "competitor":             competitor,
            "generated_at":           datetime.now(timezone.utc).isoformat(),
            "total_reviews_analysed": 0,
            "buckets": [
                {
                    "category":        cat,
                    "label":           BUCKET_LABELS[cat],
                    "mention_pct":     20.0,
                    "trend_direction": "stable",
                    "proof_quotes":    [],
                }
                for cat in BUCKET_LABELS
            ],
        }

    user_prompt = _build_user_prompt(competitor, df, total)
    logger.info("[%s] Calling Claude for churn analysis ...", competitor)
    raw  = _call_claude(_SYSTEM_PROMPT, user_prompt)
    data = _parse_analysis(raw, competitor, total)
    _save(data, competitor)
    return data
