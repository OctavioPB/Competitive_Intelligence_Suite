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

# Insert only reviews not already stored, so re-running ingestion (e.g. the daily
# scheduler job) never duplicates rows and inflates mention counts.
_INSERT_SQL = """
    INSERT INTO reviews
        (source, competitor_name, review_text, rating, date, author_id, helpful_count, is_synthetic)
    SELECT :source, :competitor_name, :review_text, :rating, :date, :author_id, :helpful_count,
           :is_synthetic
    WHERE NOT EXISTS (
        SELECT 1 FROM reviews
        WHERE competitor_name = :competitor_name
          AND source          = :source
          AND date            = :date
          AND review_text     = :review_text
    )
"""


def _demo_mode() -> bool:
    return os.getenv("DEMO_MODE", "false").lower() == "true"


def _store_reviews(rows: list[dict[str, Any]]) -> int:
    """Bulk-insert review rows into the reviews table, skipping ones already stored.

    Returns:
        Number of new rows inserted.
    """
    params = [
        {
            "source": r["source"],
            "competitor_name": r["competitor_name"],
            "review_text": r["review_text"],
            "rating": r.get("rating"),
            "date": r.get("date", ""),
            "author_id": r.get("author_id", ""),
            "helpful_count": r.get("helpful_count", 0),
            # Fixtures set this; it is how the UI tells sample data from scraped data.
            "is_synthetic": int(bool(r.get("is_synthetic", 0))),
        }
        for r in rows
    ]
    return executemany(_INSERT_SQL, params)


def _scrape_with_fallback(competitor: CompetitorConfig) -> list[dict[str, Any]]:
    """Try all live scrapers for a competitor; fall back to fixtures on failure."""
    # Imported lazily: praw / newsapi are only needed for live scraping.
    from ingestion import scraper_g2, scraper_newsapi, scraper_reddit, scraper_trustpilot

    all_reviews: list[dict[str, Any]] = []

    # G2
    try:
        all_reviews.extend(scraper_g2.scrape_reviews(competitor))
    except ScrapingError as exc:
        logger.warning("G2 scraper failed for %s: %s — using fixtures.", competitor["name"], exc)
        all_reviews.extend(fixture_module.generate(competitor))
        return all_reviews  # fixtures already contain all source types

    # Trustpilot
    try:
        all_reviews.extend(scraper_trustpilot.scrape_reviews(competitor))
    except ScrapingError as exc:
        logger.warning("Trustpilot scraper failed for %s: %s", competitor["name"], exc)

    # Reddit
    try:
        all_reviews.extend(scraper_reddit.scrape_posts(competitor, SUBREDDITS))
    except ScrapingError as exc:
        logger.warning("Reddit scraper failed for %s: %s", competitor["name"], exc)

    # NewsAPI
    try:
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
        Number of new reviews stored (already-stored reviews are skipped).
    """
    name = competitor["name"]

    if use_fixtures or _demo_mode():
        logger.info("[%s] Using fixture data (DEMO_MODE or --use-fixtures).", name)
        reviews = fixture_module.generate(competitor)
    else:
        reviews = _scrape_with_fallback(competitor)

    if not reviews:
        logger.warning("[%s] No reviews collected — skipping DB write.", name)
        return 0

    inserted = _store_reviews(reviews)
    logger.info(
        "[%s] Stored %d new reviews (%d already present).",
        name, inserted, len(reviews) - inserted,
    )
    return inserted


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
