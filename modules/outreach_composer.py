"""M09 — Outreach Composer: generate personalised outreach from competitive intelligence."""

import json
import logging
from datetime import datetime, timezone

from utils.llm import get_client, retry_with_backoff

logger = logging.getLogger(__name__)

_MODEL = "claude-sonnet-4-6"

# ── Prompts ───────────────────────────────────────────────────────────────────

_SYSTEM_PROMPT = """\
You are an expert B2B sales development rep. You receive a prospect's complaint about \
a competitor and relevant competitive intelligence about that competitor's weaknesses. \
Write three outreach variants that feel personal, specific, and evidence-backed — not \
generic or salesy.

Return ONLY valid JSON. No markdown fences. No preamble. Schema:

{
  "competitor": "<name>",
  "username": "<prospect username or label>",
  "generated_at": "<ISO 8601 UTC>",
  "email": {
    "subject": "<email subject line — specific and curiosity-driven, max 60 chars>",
    "body": "<full email body — 3-4 short paragraphs, ends with a soft CTA>"
  },
  "linkedin_dm": "<LinkedIn DM — max 280 characters, personal, references their specific complaint>",
  "call_bullets": [
    "<opening hook — reference their exact complaint>",
    "<bridge to your product's strength against this competitor weakness>",
    "<soft close — propose a 15-minute call, no pressure>"
  ]
}

Rules:
- Reference the prospect's actual complaint language — do not use generic phrases
- Ground every claim in the competitive intelligence provided
- Email body must be < 200 words — busy people don't read long emails
- linkedin_dm must be <= 280 characters — verify the count before returning
- call_bullets: 3 bullets only, each <= 30 words, starts with a verb or power word
- Do NOT use competitor's name as a negative — say "I noticed you've been evaluating alternatives"
- Close with a question, not a statement
"""

_USER_PROMPT_TEMPLATE = """\
PROSPECT INFORMATION:
  Username / name: {username}
  Competitor they are leaving: {competitor}
  Their complaint: "{complaint}"

COMPETITIVE INTELLIGENCE ABOUT {competitor}:
  Top pain points:
{pain_lines}
  Recommended pitch from battlecard: {pitch}

Write the three outreach variants now.
"""

_REPAIR_SYSTEM_PROMPT = """\
The following text should be valid JSON but has a syntax error. \
Return ONLY the corrected JSON — no explanation, no markdown fences.
"""


# ── Internal helpers ──────────────────────────────────────────────────────────


def _get_pain_context(competitor: str) -> str:
    """Fetch top 3 pain points for the competitor as formatted lines."""
    try:
        from modules.pain_point_radar import get_pain_points
        df = get_pain_points(competitor, top_n=3)
        if df.empty:
            return "  (no pain point data available)"
        lines = []
        for _, row in df.iterrows():
            label    = str(row["topic_label"]).replace("_", " ")
            severity = float(row["avg_severity"])
            trend    = str(row["trend_direction"])
            lines.append(f"    - {label}: severity={severity:.2f}, trend={trend}")
        return "\n".join(lines)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Could not fetch pain points for outreach: %s", exc)
        return "  (pain point data unavailable)"


def _get_pitch(competitor: str) -> str:
    """Return the cached battlecard recommended pitch, or a generic fallback."""
    try:
        from modules.battlecard_generator import load_cached_battlecard
        card = load_cached_battlecard(competitor)
        if card and card.get("recommended_pitch"):
            return card["recommended_pitch"][:300]
    except Exception as exc:  # noqa: BLE001
        logger.warning("Could not load battlecard pitch for outreach: %s", exc)
    return "(no cached battlecard — use the competitor's top pain points to frame your pitch)"


@retry_with_backoff
def _call_claude(system: str, user: str) -> str:
    client   = get_client()
    response = client.messages.create(
        model=_MODEL,
        max_tokens=1024,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    logger.info(
        "Outreach token usage: %d in + %d out",
        response.usage.input_tokens,
        response.usage.output_tokens,
    )
    return response.content[0].text


def _parse_bundle(raw: str, competitor: str, username: str) -> dict:
    text = raw.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        text  = "\n".join(lines[1:-1]) if len(lines) > 2 else text

    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        logger.warning("[%s] Outreach JSON parse failed — attempting repair.", competitor)
        repaired = _call_claude(_REPAIR_SYSTEM_PROMPT, text)
        try:
            data = json.loads(repaired.strip())
        except json.JSONDecodeError as exc:
            raise ValueError(f"Failed to parse outreach JSON for {competitor}") from exc

    data.setdefault("competitor", competitor)
    data.setdefault("username",   username)
    data.setdefault("generated_at", datetime.now(timezone.utc).isoformat())
    data.setdefault("email", {"subject": "", "body": ""})
    data.setdefault("linkedin_dm", "")
    data.setdefault("call_bullets", [])
    return data


# ── Public API ────────────────────────────────────────────────────────────────


def compose_outreach(competitor: str, complaint: str, username: str = "Prospect") -> dict:
    """Generate three personalised outreach variants for a switching-intent prospect.

    Args:
        competitor: Competitor name the prospect is leaving.
        complaint:  The prospect's complaint text (from Reddit post or manual input).
        username:   Prospect's Reddit username or name (used to personalise the opening).

    Returns:
        Dict with keys: competitor, username, generated_at,
        email {subject, body}, linkedin_dm (str), call_bullets (list[str]).
    """
    pain_lines = _get_pain_context(competitor)
    pitch      = _get_pitch(competitor)

    user_prompt = _USER_PROMPT_TEMPLATE.format(
        username=username,
        competitor=competitor,
        complaint=complaint[:400],
        pain_lines=pain_lines,
        pitch=pitch,
    )

    logger.info("[%s] Composing outreach for %s ...", competitor, username)
    raw    = _call_claude(_SYSTEM_PROMPT, user_prompt)
    bundle = _parse_bundle(raw, competitor, username)
    return bundle
