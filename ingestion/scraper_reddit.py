"""Scrape Reddit posts mentioning a competitor using PRAW."""

import logging
from typing import Any

import praw

from config import CompetitorConfig

logger = logging.getLogger(__name__)


def scrape_posts(
    competitor: CompetitorConfig,
    subreddits: list[str],
    limit: int = 500,
) -> list[dict[str, Any]]:
    """Fetch Reddit posts mentioning competitor keywords from the given subreddits.

    Uses PRAW with credentials from environment variables:
    REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_USER_AGENT.

    Args:
        competitor: Competitor config dict from config.COMPETITORS.
        subreddits: List of subreddit names to search (without r/ prefix).
        limit: Maximum posts to retrieve per subreddit per keyword.

    Returns:
        List of post dicts with keys:
        source, competitor_name, review_text, rating, date, author_id, helpful_count.
        (rating=None, helpful_count=upvote_ratio*100 for Reddit posts)
    """
    raise NotImplementedError("Implement in Sprint 1 — Day 1")
