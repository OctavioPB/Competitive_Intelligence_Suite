"""M04 — Battlecard Generator: Claude-powered sales battlecards from M01 + M03."""

import logging
from pathlib import Path

logger = logging.getLogger(__name__)

_BATTLECARD_DIR = Path("outputs/battlecards")
_MODEL = "claude-sonnet-4-6"

# JSON schema returned by the LLM — do not change without updating the markdown renderer.
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
    "recommended_pitch": "string (2–3 sentences)",
}


def generate_battlecard(competitor: str) -> dict:
    """Generate a sales battlecard for a competitor using the Claude API.

    Injects top 5 pain points (from M01) and top 5 feature gaps (from M03)
    into the user prompt. Returns parsed JSON matching BATTLECARD_SCHEMA.
    All calls wrapped with @retry_with_backoff from utils.llm.

    Args:
        competitor: Competitor name matching config.COMPETITORS.

    Returns:
        Dict matching BATTLECARD_SCHEMA.
    """
    raise NotImplementedError("Implement in Sprint 4 — Day 9")


def refresh_all_battlecards() -> None:
    """Regenerate battlecards for all competitors and save to outputs/battlecards/.

    Calls generate_battlecard() for each entry in config.COMPETITORS and
    writes the result as JSON + rendered markdown.
    """
    raise NotImplementedError("Implement in Sprint 4 — Day 9")
