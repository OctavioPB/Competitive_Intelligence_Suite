"""Sample market signals for the demo database (flagged is_synthetic = 1).

Fits the seeded "bad week" (2025-12-26 → 2026-01-01):

* HubSpot raises Sales Hub Professional and Starter on 2025-12-29 → pricing_change alert.
* Salesforce opens a wave of support roles → hiring_signal alert.
* HubSpot hires engineers for integrations / APIs → hiring_signal alert.

Usage (seeds whichever database is active — DEMO_MODE / DATABASE_URL):
    python ingestion/signal_fixtures.py
"""

from __future__ import annotations

import sys
from contextlib import closing
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from database.db import get_conn, init_schema
from modules.market_signals import record_job_postings, record_pricing_check

CRAWL_DAY = date(2026, 1, 1)

_PRICING: dict[str, tuple[str, list[tuple[date, list[str]]]]] = {
    "HubSpot": ("https://www.hubspot.com/pricing/sales", [
        (date(2025, 11, 20), [
            "Free: $0 /mo",
            "Starter: $15 /mo/seat",
            "Professional: $90 /mo/seat",
            "Enterprise: $150 /mo/seat",
            "Sequences: $1,500",
        ]),
        (date(2025, 12, 29), [
            "Free: $0 /mo",
            "Starter: $20 /mo/seat",
            "Professional: $100 /mo/seat",
            "Enterprise: $150 /mo/seat",
            "Onboarding fee (Professional): $1,500",
        ]),
    ]),
    "Salesforce": ("https://www.salesforce.com/sales/pricing/", [
        (date(2025, 11, 20), [
            "Starter Suite: $25 USD/User/Month",
            "Pro Suite: $100 USD/User/Month",
            "Enterprise: $165 USD/User/Month",
            "Unlimited: $330 USD/User/Month",
        ]),
    ]),
    "Pipedrive": ("https://www.pipedrive.com/en/pricing", [
        (date(2025, 11, 20), [
            "Lite: US$14", "Growth: US$24", "Premium: US$49", "Ultimate: US$69",
        ]),
    ]),
}

# (title, department, days before the crawl it was posted)
_JOBS: dict[str, tuple[str, list[tuple[str, str, int]]]] = {
    "Salesforce": ("workday", [
        ("Customer Support Engineer, Sales Cloud", "Customer Success", 2),
        ("Technical Support Engineer - Tier 2", "Customer Success", 3),
        ("Support Specialist, Premier Success", "Customer Success", 3),
        ("Customer Success Manager - Mid-Market", "Customer Success", 4),
        ("Customer Success Manager - Enterprise", "Customer Success", 6),
        ("Technical Support Engineer - Integrations", "Customer Success", 7),
        ("Support Escalations Manager", "Customer Success", 8),
        ("Customer Support Representative (Contract)", "Customer Success", 9),
        ("Technical Account Manager, Signature Success", "Customer Success", 11),
        ("Support Engineer, Data Cloud", "Customer Success", 12),
        ("Customer Success Architect", "Customer Success", 14),
        ("Account Executive, Commercial", "Sales", 3),
        ("Account Executive, Enterprise", "Sales", 9),
        ("Solution Engineer, Sales Cloud", "Sales", 13),
        ("Senior Software Engineer, Agentforce", "Engineering", 5),
        ("Software Engineer, Platform Reliability", "Engineering", 10),
        ("Lead Product Manager, Sales Cloud", "Product", 15),
        ("Product Marketing Manager, SMB", "Marketing", 18),
        ("Senior Financial Analyst", "Finance", 20),
        ("Program Manager, Customer Programs", "Operations", 22),
        # No older roles: the Workday reader stops at 30 days, so the sample does too.
    ]),
    "HubSpot": ("greenhouse", [
        ("Senior Software Engineer, Integrations Platform", "Engineering", 4),
        ("Software Engineer II, Public APIs", "Engineering", 6),
        ("Staff Engineer, App Marketplace & Ecosystem", "Engineering", 9),
        ("Senior Software Engineer, Data Sync", "Engineering", 12),
        ("Product Manager, Integrations", "Product", 15),
        ("Software Engineer, CRM Core", "Engineering", 20),
        ("Account Executive, Mid-Market", "Sales", 3),
        ("Account Executive, Corporate", "Sales", 8),
        ("Account Manager, Install Base", "Sales", 11),
        ("Customer Support Specialist", "Customer Support", 16),
        ("Customer Success Manager", "Scaled CS", 24),
        ("Content Marketing Manager", "Marketing", 27),
        ("Senior Data Analyst", "Operations", 40),
        ("Account Executive, Enterprise", "Sales", 75),
    ]),
}


def _clear() -> None:
    with closing(get_conn()) as conn, conn:
        conn.execute("DELETE FROM pricing_snapshots WHERE is_synthetic = 1")
        conn.execute("DELETE FROM job_postings WHERE is_synthetic = 1")


def seed_market_signals() -> dict[str, int]:
    """Replace the sample pricing snapshots and job postings. Idempotent."""
    init_schema()
    _clear()

    snapshots = 0
    for competitor, (url, versions) in _PRICING.items():
        for day, points in versions:
            record_pricing_check(competitor, url, points, day, is_synthetic=True)
            snapshots += 1
        # The latest check, so "last checked" reads as the end of the bad week.
        record_pricing_check(competitor, url, versions[-1][1], CRAWL_DAY, is_synthetic=True)

    postings = 0
    for competitor, (source, roles) in _JOBS.items():
        rows = [
            {
                "external_id": f"demo-{competitor.lower()}-{i}",
                "title": title,
                "department": department,
                "location": "Remote",
                "url": None,
                "posted_date": (CRAWL_DAY - timedelta(days=age)).isoformat(),
            }
            for i, (title, department, age) in enumerate(roles)
        ]
        record_job_postings(competitor, source, rows, CRAWL_DAY, is_synthetic=True)
        postings += len(rows)

    return {"pricing_versions": snapshots, "job_postings": postings}


if __name__ == "__main__":
    print(seed_market_signals())
