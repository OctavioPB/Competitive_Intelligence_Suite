"""Orchestrate all scrapers and persist raw data to the reviews table."""

import argparse
import logging
import os
import sys
from pathlib import Path
from typing import Any

# Ensure project root is on sys.path when script is run directly
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import COMPETITORS, SUBREDDITS, CompetitorConfig
from database.db import executemany, init_schema
from ingestion import fixtures as fixture_module
from ingestion.scraper_g2 import ScrapingError

logger = logging.getLogger(__name__)

_INSERT_SQL = """
    INSERT INTO reviews (source, competitor_name, review_text, rating, date, author_id, helpful_count)
    VALUES (?, ?, ?, ?, ?, ?, ?)
"""

_DEMO_MODE: bool = os.getenv("DEMO_MODE", "false").lower() == "true"


def _store_reviews(rows: list[dict[str, Any]]) -> None:
    """Bulk-insert review rows into the reviews table."""
    params = [
        (
            r["source"],
            r["competitor_name"],
            r["review_text"],
            r.get("rating"),
            r.get("date", ""),
            r.get("author_id", ""),
            r.get("helpful_count", 0),
        )
        for r in rows
    ]
    executemany(_INSERT_SQL, params)


def _scrape_with_fallback(competitor: CompetitorConfig) -> list[dict[str, Any]]:
    """Try all live scrapers for a competitor; fall back to fixtures on failure."""
    from ingestion import scraper_g2, scraper_reddit, scraper_newsapi

    all_reviews: list[dict[str, Any]] = []

    # G2
    try:
        all_reviews.extend(scraper_g2.scrape_reviews(competitor))
    except ScrapingError as exc:
        logger.warning("G2 scraper failed for %s: %s — using fixtures.", competitor["name"], exc)
        all_reviews.extend(fixture_module.generate(competitor))
        return all_reviews  # fixtures already contain all source types

    # Reddit
    try:
        from ingestion import scraper_reddit

        all_reviews.extend(scraper_reddit.scrape_posts(competitor, SUBREDDITS))
    except ScrapingError as exc:
        logger.warning("Reddit scraper failed for %s: %s", competitor["name"], exc)

    # NewsAPI
    try:
        from ingestion import scraper_newsapi

        all_reviews.extend(scraper_newsapi.fetch_articles(competitor))
    except ScrapingError as exc:
        logger.warning("NewsAPI scraper failed for %s: %s", competitor["name"], exc)

    return all_reviews


def run_for_competitor(competitor: CompetitorConfig, use_fixtures: bool = False) -> int:
    """Run ingestion for a single competitor and store results.

    Args:
        competitor: Competitor config dict from config.COMPETITORS.
        use_fixtures: If True, skip live scraping and use synthetic fixture data.

    Returns:
        Number of reviews stored.
    """
    name = competitor["name"]

    if use_fixtures or _DEMO_MODE:
        logger.info("[%s] Using fixture data (DEMO_MODE or --use-fixtures).", name)
        reviews = fixture_module.generate(competitor)
    else:
        reviews = _scrape_with_fallback(competitor)

    if not reviews:
        logger.warning("[%s] No reviews collected — skipping DB write.", name)
        return 0

    _store_reviews(reviews)
    logger.info("[%s] Stored %d reviews.", name, len(reviews))
    return len(reviews)


def main() -> None:
    """CLI entry point.

    Usage:
        python ingestion/run_ingestion.py                          # all competitors
        python ingestion/run_ingestion.py --competitor HubSpot     # single competitor
        python ingestion/run_ingestion.py --use-fixtures           # skip live scraping
    """
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)

    parser = argparse.ArgumentParser(description="RivalSense ingestion pipeline")
    parser.add_argument(
        "--competitor",
        type=str,
        default=None,
        help="Competitor name to ingest (default: all)",
    )
    parser.add_argument(
        "--use-fixtures",
        action="store_true",
        default=False,
        help="Use synthetic fixture data instead of live scraping",
    )
    args = parser.parse_args()

    init_schema()

    targets = (
        [c for c in COMPETITORS if c["name"] == args.competitor]
        if args.competitor
        else COMPETITORS
    )

    if not targets:
        logger.error("No competitor matched '%s'. Check config.COMPETITORS.", args.competitor)
        sys.exit(1)

    total = 0
    for competitor in targets:
        total += run_for_competitor(competitor, use_fixtures=args.use_fixtures)

    logger.info("Ingestion complete. Total rows stored: %d", total)


if __name__ == "__main__":
    main()
