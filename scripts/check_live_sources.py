"""Check that every live data source still works against the real websites.

Scrapers break silently when a site changes its markup or API. This runs each
configured source once, prints a table (also written to the GitHub Actions job
summary) and exits 1 if a source that is expected to work returned nothing.

G2 and Capterra are reported but never fail the check: both block automated
browsers (DataDome / Cloudflare), so "blocked" is their expected state.

Usage (from the project root):
    python scripts/check_live_sources.py
Needs only requests, beautifulsoup4 and (for HubSpot pricing) playwright.
"""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path
from typing import Callable

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import COMPETITORS  # noqa: E402

Check = tuple[str, str, bool, Callable[[], str]]   # competitor, source, required, run → detail


def _pricing(url: str) -> Callable[[], str]:
    def run() -> str:
        from ingestion.scraper_pricing import fetch_price_points

        points, rendered = fetch_price_points(url)
        return f"{len(points)} price points ({'headless' if rendered else 'static'})"
    return run


def _jobs(careers) -> Callable[[], str]:
    def run() -> str:
        from ingestion.scraper_jobs import fetch_postings

        # A short window keeps the Workday crawl to one or two pages.
        postings = fetch_postings(careers, max_age_days=3)
        return f"{len(postings)} postings ({careers['provider']})"
    return run


def _app_store(competitor) -> Callable[[], str]:
    def run() -> str:
        from ingestion.scraper_appstore import scrape_reviews

        return f"{len(scrape_reviews(competitor, max_pages=1))} reviews"
    return run


def _g2(competitor) -> Callable[[], str]:
    def run() -> str:
        from ingestion.scraper_g2 import scrape_reviews

        return f"{len(scrape_reviews(competitor, max_pages=1))} reviews"
    return run


def _capterra(competitor) -> Callable[[], str]:
    def run() -> str:
        from ingestion.scraper_capterra import scrape_reviews

        return f"{len(scrape_reviews(competitor))} reviews"
    return run


def checks() -> list[Check]:
    found: list[Check] = []
    for c in COMPETITORS:
        name = c["name"]
        for url in c.get("pricing_urls", []):
            found.append((name, "Pricing page", True, _pricing(url)))
        if c.get("careers"):
            found.append((name, "Job board", True, _jobs(c["careers"])))
        if c.get("app_store_id"):
            found.append((name, "App Store", True, _app_store(c)))
        found.append((name, "G2", False, _g2(c)))
        if c.get("capterra_url"):
            found.append((name, "Capterra", False, _capterra(c)))
    return found


def main() -> int:
    rows: list[tuple[str, str, str, str]] = []
    failures = 0
    for competitor, source, required, run in checks():
        started = time.monotonic()
        try:
            status, detail = "✅ ok", run()
        except Exception as exc:  # noqa: BLE001 — every failure is reported, none aborts the run
            detail = str(exc).replace("|", "/")[:180]
            status = "❌ failed" if required else "⚠️ blocked (expected)"
            failures += required
        rows.append((competitor, source, status, f"{detail} · {time.monotonic() - started:.1f}s"))

    table = ["| Competitor | Source | Status | Detail |", "|---|---|---|---|"]
    table += [f"| {a} | {b} | {c} | {d} |" for a, b, c, d in rows]
    verdict = (
        f"**{failures} required source(s) failed.**" if failures
        else "All required sources returned data."
    )
    report = "\n".join(["## Live source check", "", *table, "", verdict, ""])

    print(report)
    summary = os.getenv("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as fh:
            fh.write(report)
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
