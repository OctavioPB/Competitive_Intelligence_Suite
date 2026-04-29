"""Orchestrate the NLP pipeline: read reviews, write processed_reviews."""

import argparse
import logging
import sys

from config import COMPETITORS, CompetitorConfig

logger = logging.getLogger(__name__)


def run_for_competitor(competitor: CompetitorConfig) -> None:
    """Run the full NLP pipeline for a single competitor.

    Reads from reviews, writes to processed_reviews. Idempotent:
    existing processed rows are updated rather than duplicated.

    Args:
        competitor: Competitor config dict from config.COMPETITORS.
    """
    raise NotImplementedError("Implement in Sprint 1 — Day 2")


def main() -> None:
    """CLI entry point.

    Usage:
        python pipeline/run_pipeline.py                        # all competitors
        python pipeline/run_pipeline.py --competitor HubSpot   # single competitor
    """
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)

    parser = argparse.ArgumentParser(description="RivalSense NLP pipeline")
    parser.add_argument(
        "--competitor",
        type=str,
        default=None,
        help="Competitor name to process (default: all)",
    )
    args = parser.parse_args()

    targets = (
        [c for c in COMPETITORS if c["name"] == args.competitor]
        if args.competitor
        else COMPETITORS
    )

    if not targets:
        logger.error("No competitor matched '%s'. Check config.COMPETITORS.", args.competitor)
        sys.exit(1)

    for competitor in targets:
        logger.info("Running NLP pipeline for %s ...", competitor["name"])
        run_for_competitor(competitor)


if __name__ == "__main__":
    main()
