"""Scrape Reddit posts mentioning a competitor using PRAW."""

import logging
import os
from typing import Any

import praw
from praw.exceptions import PRAWException

from config import CompetitorConfig
from ingestion.scraper_g2 import ScrapingError

logger = logging.getLogger(__name__)


def _build_client() -> praw.Reddit:
    """Return a read-only PRAW client from environment variables.

    Raises:
        ScrapingError: If any required credential env var is missing.
    """
    client_id = os.getenv("REDDIT_CLIENT_ID", "")
    client_secret = os.getenv("REDDIT_CLIENT_SECRET", "")
    user_agent = os.getenv("REDDIT_USER_AGENT", "RivalSense/1.0")

    if not client_id or not client_secret:
        raise ScrapingError(
            "REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET must be set to use the Reddit scraper."
        )

    return praw.Reddit(
        client_id=client_id,
        client_secret=client_secret,
        user_agent=user_agent,
        read_only=True,
    )


def scrape_posts(
    competitor: CompetitorConfig,
    subreddits: list[str],
    limit: int = 100,
) -> list[dict[str, Any]]:
    """Fetch Reddit posts mentioning competitor keywords from the given subreddits.

    Args:
        competitor: Competitor config dict from config.COMPETITORS.
        subreddits: List of subreddit names to search (without r/ prefix).
        limit: Maximum posts to retrieve per subreddit per keyword.

    Returns:
        List of post dicts with keys:
        source, competitor_name, review_text, rating, date, author_id, helpful_count.

    Raises:
        ScrapingError: If credentials are missing or the API call fails.
    """
    name = competitor["name"]
    keywords = competitor["reddit_keywords"]
    posts: list[dict[str, Any]] = []
    seen_ids: set[str] = set()

    try:
        reddit = _build_client()
    except ScrapingError:
        raise

    for subreddit_name in subreddits:
        for keyword in keywords:
            try:
                subreddit = reddit.subreddit(subreddit_name)
                results = subreddit.search(keyword, limit=limit, sort="new")
                for post in results:
                    if post.id in seen_ids:
                        continue
                    seen_ids.add(post.id)

                    text = (post.selftext or post.title).strip()
                    if not text or len(text) < 30:
                        continue

                    import datetime as _dt

                    post_date = _dt.datetime.utcfromtimestamp(post.created_utc).strftime(
                        "%Y-%m-%d"
                    )
                    posts.append(
                        {
                            "source": "reddit",
                            "competitor_name": name,
                            "review_text": text,
                            "rating": None,
                            "date": post_date,
                            "author_id": str(post.author) if post.author else "deleted",
                            "helpful_count": int(post.score),
                        }
                    )
            except PRAWException as exc:
                logger.warning(
                    "Reddit API error for r/%s / '%s': %s", subreddit_name, keyword, exc
                )

    if not posts:
        raise ScrapingError(f"Reddit scraper returned 0 posts for {name}.")

    logger.info("Reddit: scraped %d posts for %s", len(posts), name)
    return posts
