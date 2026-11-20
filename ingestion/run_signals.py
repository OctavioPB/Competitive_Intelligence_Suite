"""Check competitor pricing pages and job boards, and store what changed.

Usage (from the project root):
    python ingestion/run_signals.py                         # all competitors
    python ingestion/run_signals.py --competitor HubSpot
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
from datetime import date
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import CompetitorConfig
from database.db import init_schema
from ingestion.browser import FetchError
from ingestion.scraper_g2 import ScrapingError
from ingestion.scraper_jobs import fetch_postings
from ingestion.scraper_pricing import fetch_price_points
from modules.market_signals import describe_changes, record_job_postings, record_pricing_check
from modules.settings_store import competitors as all_competitors

logger = logging.getLogger(__name__)


def check_competitor(competitor: CompetitorConfig, today: date | None = None) -> dict[str, Any]:
    """Run every configured market-signal source for one competitor.

    A failing source is reported in ``errors`` and never stops the others.
    """
    name = competitor["name"]
    today = today or date.today()
    report: dict[str, Any] = {"competitor": name, "pricing": [], "jobs": None, "errors": []}

    for url in competitor.get("pricing_urls", []):
        try:
            points, rendered = fetch_price_points(url)
        except FetchError as exc:
            logger.warning("[%s] pricing page %s: %s", name, url, exc)
            report["errors"].append(f"Pricing page {url}: {exc}")
            continue
        result = record_pricing_check(name, url, points, today)
        report["pricing"].append({
            "url": url,
            "status": result["status"],
            "price_points": len(points),
            "rendered": rendered,
            "changes": describe_changes(result["added"], result["removed"]),
        })
        logger.info("[%s] pricing %s: %s (%d price points)", name, url, result["status"], len(points))

    careers = competitor.get("careers")
    if careers:
        try:
            postings = fetch_postings(careers, today=today)
        except ScrapingError as exc:
            logger.warning("[%s] job board: %s", name, exc)
            report["errors"].append(f"Job board ({careers['provider']}): {exc}")
        else:
            result = record_job_postings(name, careers["provider"], postings, today)
            report["jobs"] = {"source": careers["provider"], **result}
            logger.info("[%s] jobs: %d open, %d new", name, result["seen"], result["new"])

    return report


def main() -> None:
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    parser = argparse.ArgumentParser(description="RivalSense market signals (pricing pages + job boards)")
    parser.add_argument("--competitor", default=None, help="Competitor name (default: all)")
    args = parser.parse_args()

    if os.getenv("DEMO_MODE", "false").lower() == "true":
        logger.error("DEMO_MODE=true — live checks would write into the demo database. Unset it first.")
        sys.exit(1)

    init_schema()
    targets = [c for c in all_competitors() if args.competitor in (None, c["name"])]
    if not targets:
        logger.error("No competitor matched '%s'. Check the Settings page.", args.competitor)
        sys.exit(1)

    for competitor in targets:
        report = check_competitor(competitor)
        for page in report["pricing"]:
            for line in page["changes"]:
                logger.info("[%s] price change: %s", competitor["name"], line)


if __name__ == "__main__":
    main()
