"""Orchestrate all scrapers and persist raw data to the reviews table."""

import argparse
import logging
import sys

from config import COMPETITORS, SUBREDDITS, CompetitorConfig
from database.db import init_schema

logger = logging.getLogger(__name__)


def run_for_competitor(competitor: CompetitorConfig) -> None:
    """Run all scrapers for a single competitor and store results.

    Args:
        competitor: Competitor config dict from config.COMPETITORS.
    """
    raise NotImplementedError("Implement in Sprint 1 — Day 1")


def main() -> None:
    """CLI entry point.

    Usage:
        python ingestion/run_ingestion.py                        # all competitors
        python ingestion/run_ingestion.py --competitor HubSpot   # single competitor
    """
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)

    parser = argparse.ArgumentParser(description="RivalSense ingestion pipeline")
    parser.add_argument(
        "--competitor",
        type=str,
        default=None,
        help="Competitor name to ingest (default: all)",
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

    for competitor in targets:
        logger.info("Ingesting data for %s ...", competitor["name"])
        run_for_competitor(competitor)


if __name__ == "__main__":
    main()
