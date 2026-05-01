"""M04 — Battlecard Generator: Claude-powered sales battlecards from M01 + M03."""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from config import COMPETITORS, OWN_FEATURES
from modules.feature_wish_miner import extract_wishes, flag_own_features
from modules.pain_point_radar import get_pain_points
from utils.llm import get_client, retry_with_backoff

logger = logging.getLogger(__name__)

_MODEL = "claude-sonnet-4-6"
_BATTLECARD_DIR = Path("outputs/battlecards")

# ── Prompts ───────────────────────────────────────────────────────────────────

_SYSTEM_PROMPT = """\
You are an expert B2B sales strategist. Generate a structured sales battlecard \
for competing against a software product using customer review intelligence data.

Return ONLY a valid JSON object — no markdown fences, no preamble, no explanation. \
The response must start with { and end with }. Use this exact schema:

{
  "competitor": "<competitor name>",
  "generated_at": "<ISO 8601 UTC timestamp>",
  "objections": [
    {
      "objection": "<the sales objection a prospect raises when choosing this competitor>",
      "evidence": "<data point: topic category, mention count, severity score>",
      "counter": "<specific, assertive 1-2 sentence counter from your product's perspective>",
      "proof_quote": "<authentic customer voice quote in first person, 1-2 sentences>"
    }
  ],
  "feature_gaps": [
    {
      "gap": "<feature or capability the competitor lacks based on customer requests>",
      "frequency": <integer mention count>,
      "your_advantage": "<how your product already addresses this gap>"
    }
  ],
  "recommended_pitch": "<2-3 sentence executive-level pitch for a sales rep opening a switching conversation>"
}

Rules:
- Include exactly 5 objections, one per pain point provided
- Include one feature_gap entry per gap provided (up to 5)
- Counters must be specific and actionable — avoid phrases like "we do it better"
- proof_quote must feel authentic, as if written by an actual frustrated customer
- recommended_pitch leads with the competitor's biggest verifiable pain point
"""

_REPAIR_SYSTEM_PROMPT = """\
The following text should be valid JSON but has a syntax error. \
Return ONLY the corrected JSON — no explanation, no markdown fences. \
The response must start with { and end with }.
"""

_USER_PROMPT_TEMPLATE = """\
Generate a sales battlecard for competing against {competitor}.

TOP 5 PAIN POINTS (from {total_reviews} customer reviews):
{pain_lines}

FEATURE GAPS ALREADY COVERED BY OUR PRODUCT:
{gap_lines}

Generate the JSON battlecard now.
"""

# ── JSON schema reference (documentation only — not sent to the API) ──────────

BATTLECARD_SCHEMA = {
    "competitor": "string",
    "generated_at": "ISO timestamp",
    "objections": [
        {
            "objection": "string",
            "evidence": "string (pain point + mention count)",
            "counter": "string",
            "proof_quote": "string (verbatim from reviews)",
        }
    ],
    "feature_gaps": [
        {
            "gap": "string",
            "frequency": "int",
            "your_advantage": "string",
        }
    ],
    "recommended_pitch": "string (2-3 sentences)",
}


# ── Internal helpers ──────────────────────────────────────────────────────────


def _build_user_prompt(
    competitor: str,
    pain_df: pd.DataFrame,
    wish_df: pd.DataFrame,
) -> str:
    total_reviews = int(pain_df["mention_count"].sum()) if not pain_df.empty else 0

    if not pain_df.empty:
        pain_lines = "\n".join(
            f"  {i + 1}. {row['topic_label']} — {row['mention_count']} mentions, "
            f"severity {row['avg_severity']:.2f} ({row['trend_direction']} {row['trend_icon']})"
            for i, (_, row) in enumerate(pain_df.head(5).iterrows())
        )
    else:
        pain_lines = "  (no pain point data available — use general CRM competitor pain points)"

    if not wish_df.empty and "your_product_has_it" in wish_df.columns:
        covered = wish_df[wish_df["your_product_has_it"]].head(5)
        if not covered.empty:
            gap_lines = "\n".join(
                f"  {i + 1}. {row['wish_phrase_cluster']} — {row['count']} mentions"
                for i, (_, row) in enumerate(covered.iterrows())
            )
        else:
            gap_lines = "  (no covered feature gaps identified)"
    elif not wish_df.empty:
        gap_lines = "\n".join(
            f"  {i + 1}. {row['wish_phrase_cluster']} — {row['count']} mentions"
            for i, (_, row) in enumerate(wish_df.head(5).iterrows())
        )
    else:
        gap_lines = "  (no feature wish data available)"

    return _USER_PROMPT_TEMPLATE.format(
        competitor=competitor,
        total_reviews=total_reviews,
        pain_lines=pain_lines,
        gap_lines=gap_lines,
    )


@retry_with_backoff
def _call_claude(system: str, user: str) -> str:
    """Make a single Claude API call and return the raw text response.

    Logs token usage and warns when the total exceeds 2,000 tokens.
    Wrapped with @retry_with_backoff for transient API errors.
    """
    client = get_client()
    response = client.messages.create(
        model=_MODEL,
        max_tokens=2048,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    in_tok = response.usage.input_tokens
    out_tok = response.usage.output_tokens
    total = in_tok + out_tok
    logger.info("Token usage: %d in + %d out = %d total", in_tok, out_tok, total)
    if total > 2000:
        logger.warning(
            "Token count %d exceeds 2,000 — consider trimming the input prompt.", total
        )
    return response.content[0].text


def _parse_battlecard(raw: str, competitor: str) -> dict:
    text = raw.strip()
    # Strip markdown code fences that some models emit despite instructions
    if text.startswith("```"):
        lines = text.splitlines()
        text = "\n".join(lines[1:-1]) if len(lines) > 2 else text

    try:
        card = json.loads(text)
    except json.JSONDecodeError:
        logger.warning("[%s] Initial JSON parse failed — attempting repair.", competitor)
        repaired_raw = _call_claude(_REPAIR_SYSTEM_PROMPT, text)
        try:
            card = json.loads(repaired_raw.strip())
        except json.JSONDecodeError as exc:
            logger.error("[%s] JSON repair failed.\nRaw: %.500s", competitor, raw)
            raise ValueError(f"Failed to parse battlecard JSON for {competitor}") from exc

    card.setdefault("competitor", competitor)
    card.setdefault("generated_at", datetime.now(timezone.utc).isoformat())
    card.setdefault("objections", [])
    card.setdefault("feature_gaps", [])
    card.setdefault("recommended_pitch", "")
    return card


def _save_battlecard(card: dict, competitor: str) -> None:
    _BATTLECARD_DIR.mkdir(parents=True, exist_ok=True)
    slug = competitor.lower().replace(" ", "_")

    payload = json.dumps(card, indent=2, ensure_ascii=False)

    # Latest file — serves as the UI cache key
    (_BATTLECARD_DIR / f"{slug}_latest.json").write_text(payload, encoding="utf-8")

    # Timestamped archive (date part of generated_at)
    date_tag = card.get("generated_at", "")[:10].replace("-", "") or "unknown"
    (_BATTLECARD_DIR / f"{slug}_{date_tag}.json").write_text(payload, encoding="utf-8")

    # Markdown version for reference
    (_BATTLECARD_DIR / f"{slug}_latest.md").write_text(
        battlecard_to_markdown(card), encoding="utf-8"
    )
    logger.info("Battlecard saved: %s", _BATTLECARD_DIR / f"{slug}_latest.json")


# ── Public API ────────────────────────────────────────────────────────────────


def battlecard_to_markdown(card: dict) -> str:
    """Convert a battlecard dict to a formatted markdown string.

    Args:
        card: Dict matching BATTLECARD_SCHEMA.

    Returns:
        Markdown string ready to render or export.
    """
    lines: list[str] = [
        f"# Sales Battlecard: vs. {card.get('competitor', 'Unknown')}",
        f"*Generated: {card.get('generated_at', '')[:19].replace('T', ' ')} UTC*",
        "",
        "---",
        "",
        "## Recommended Pitch",
        "",
        card.get("recommended_pitch", ""),
        "",
        "---",
        "",
        "## Objection Handlers",
        "",
    ]

    for i, obj in enumerate(card.get("objections", []), 1):
        lines += [
            f"### {i}. {obj.get('objection', '')}",
            "",
            f"**Evidence:** {obj.get('evidence', '')}",
            "",
            f"**Counter:** {obj.get('counter', '')}",
            "",
            f"> \"{obj.get('proof_quote', '')}\"",
            "",
        ]

    lines += [
        "---",
        "",
        "## Feature Gaps (We Win Here)",
        "",
    ]

    for gap in card.get("feature_gaps", []):
        lines += [
            f"- **{gap.get('gap', '')}** ({gap.get('frequency', 0)} mentions)",
            f"  → {gap.get('your_advantage', '')}",
            "",
        ]

    return "\n".join(lines)


def load_cached_battlecard(competitor: str) -> dict | None:
    """Load the most recently generated battlecard from disk, or None if absent.

    Args:
        competitor: Competitor name from config.COMPETITORS.

    Returns:
        Battlecard dict or None.
    """
    slug = competitor.lower().replace(" ", "_")
    path = _BATTLECARD_DIR / f"{slug}_latest.json"
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        logger.warning("Could not load cached battlecard for %s: %s", competitor, exc)
        return None


def generate_battlecard(competitor: str) -> dict:
    """Generate a sales battlecard for a competitor using the Claude API.

    Pulls top-5 pain points from M01 and top-5 covered feature gaps from M03,
    constructs a structured prompt, calls claude-sonnet-4-6, and persists the
    result to outputs/battlecards/.

    Args:
        competitor: Competitor name matching config.COMPETITORS.

    Returns:
        Dict matching BATTLECARD_SCHEMA.
    """
    logger.info("[%s] Pulling pain points and feature gaps ...", competitor)
    pain_df = get_pain_points(competitor, top_n=5)
    wish_df = extract_wishes(competitor)
    if not wish_df.empty:
        wish_df = flag_own_features(wish_df, OWN_FEATURES)

    user_prompt = _build_user_prompt(competitor, pain_df, wish_df)
    logger.info("[%s] Calling Claude API ...", competitor)
    raw = _call_claude(_SYSTEM_PROMPT, user_prompt)
    card = _parse_battlecard(raw, competitor)
    _save_battlecard(card, competitor)
    return card


def refresh_all_battlecards() -> None:
    """Regenerate battlecards for every competitor in config.COMPETITORS.

    Calls generate_battlecard() sequentially and saves each result to
    outputs/battlecards/. Logs a summary on completion.
    """
    results: dict[str, str] = {}
    for competitor in COMPETITORS:
        name = competitor["name"]
        try:
            generate_battlecard(name)
            results[name] = "ok"
            logger.info("[%s] Battlecard refreshed.", name)
        except Exception as exc:  # noqa: BLE001
            results[name] = f"error: {exc}"
            logger.error("[%s] Failed to refresh battlecard: %s", name, exc)

    ok = sum(1 for v in results.values() if v == "ok")
    logger.info(
        "refresh_all_battlecards complete: %d/%d succeeded. %s",
        ok, len(results), results,
    )
