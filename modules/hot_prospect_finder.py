"""M06 — Hot Prospect Finder: surface Reddit users actively switching competitors."""

import logging

import pandas as pd

logger = logging.getLogger(__name__)

_SWITCHING_PHRASES = [
    "looking for alternative",
    "switching from",
    "leaving",
    "is terrible",
    "alternative to",
    "fed up with",
    "moving away from",
]


def scan_reddit(competitor_list: list[str], subreddits: list[str]) -> pd.DataFrame:
    """Search subreddits for posts expressing intent to switch from a competitor.

    Args:
        competitor_list: List of competitor names to search for.
        subreddits: List of subreddit names to search (without r/ prefix).

    Returns:
        DataFrame with columns:
        source (str), post_id (str), username (str), post_text (str),
        post_url (str), created_at (str), competitor_name (str).
    """
    raise NotImplementedError("Implement in Sprint 5 — Day 12")


def score_urgency(post: dict) -> float:
    """Score a Reddit post for switching intent urgency.

    Scoring rubric:
      +0.4  explicit switching-intent keyword present
      +0.3  negative sentiment score
      +0.2  post created within last 7 days
      +0.1  upvotes + comments above median

    Args:
        post: Dict with keys: post_text, created_at, upvotes, num_comments,
              sentiment_score (pre-computed).

    Returns:
        Urgency score in [0.0, 1.0].
    """
    raise NotImplementedError("Implement in Sprint 5 — Day 12")


def enrich_lead(lead: dict) -> dict:
    """Add complaint_summary, company_signals, and suggested_angle to a lead.

    Args:
        lead: Dict from scan_reddit() result row.

    Returns:
        lead dict extended with:
        complaint_summary (str), company_signals (list[str]),
        suggested_angle (str).
    """
    raise NotImplementedError("Implement in Sprint 5 — Day 12")
