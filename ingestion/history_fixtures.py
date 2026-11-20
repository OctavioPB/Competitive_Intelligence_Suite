"""Sample history for the demo: an earlier battlecard version, two weekly digests and win/loss deals.

"What changed" compares stored versions; a freshly seeded demo has only one
of each, so this adds the week before (flagged is_synthetic where the table
allows it). Battlecard files are written next to the current ones; the current
``*_latest.json`` stubs must already exist (scripts/seed_demo_db.py writes them).

Usage (seeds whichever database is active — DEMO_MODE / DATABASE_URL):
    python ingestion/history_fixtures.py
"""

from __future__ import annotations

import copy
import json
import sys
from contextlib import closing
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from database.db import get_conn, init_schema

PREVIOUS_DAY = "2025-12-20"

# What the battlecard said a week earlier, before the bad week.
_PREVIOUS_CARD_EDITS: dict[str, dict] = {
    "Salesforce": {
        "recommended_pitch": "Lead with ease of use: Salesforce needs months of admin work before reps are productive.",
        "objection": ("Salesforce is the safe enterprise choice.", "Analyst reports and brand recognition",
                      "Safe is expensive — show the 3-year TCO including admins and consultants.", ""),
        "gap": ("Native Slack notifications", 6, "Built in, no add-on licence."),
    },
    "HubSpot": {
        "recommended_pitch": "Lead with reporting depth: HubSpot dashboards stop at surface metrics.",
        "objection": ("HubSpot's free CRM is good enough for us.", "Free tier adoption",
                      "Free until the first tier jump — map their next 12 months of contact growth.", ""),
        "gap": ("Custom report builder without Enterprise", 9, "Every plan includes custom reports."),
    },
    "Pipedrive": {
        "recommended_pitch": "Lead with automation: Pipedrive workflows run out of steps quickly.",
        "objection": ("Pipedrive is simpler for small sales teams.", "Onboarding speed reviews",
                      "Match the simplicity, then show what they get when they grow.", ""),
        "gap": ("Multi-pipeline forecasting", 7, "Forecast across pipelines in one view."),
    },
}

_DIGESTS: list[dict] = [
    {
        "generated_at": "2025-12-22T07:00:00+00:00",
        "overall_theme": "A quiet week: HubSpot's tier pricing remains the most-cited reason to look elsewhere.",
        "per_competitor": [
            {"name": "Salesforce", "sentiment_delta": -0.04, "sentiment_signal": "stable",
             "top_pain": "Implementation and admin cost",
             "summary": "Steady complaints about admin overhead; no major incidents.",
             "action_bullets": ["Lead with time-to-value in enterprise deals."]},
            {"name": "HubSpot", "sentiment_delta": -0.06, "sentiment_signal": "declining",
             "top_pain": "Contact-tier pricing",
             "summary": "Contact-tier jumps keep frustrating growing teams.",
             "action_bullets": ["Offer a contact-growth cost projection."]},
            {"name": "Pipedrive", "sentiment_delta": 0.02, "sentiment_signal": "stable",
             "top_pain": "Reporting limits",
             "summary": "Mostly positive; reporting remains the weak spot.",
             "action_bullets": ["Demo dashboards early in Pipedrive evaluations."]},
        ],
        "top_alert": None,
        "top_lead": None,
    },
    {
        "generated_at": "2025-12-29T07:00:00+00:00",
        "overall_theme": "Salesforce's outage and HubSpot's price rise make this the best week of the quarter to prospect.",
        "per_competitor": [
            {"name": "Salesforce", "sentiment_delta": -0.66, "sentiment_signal": "declining",
             "top_pain": "Outages and support response time",
             "summary": "A six-hour outage and slow support drove the sharpest sentiment drop this year.",
             "action_bullets": ["Reach out to accounts affected by the outage with an uptime comparison."]},
            {"name": "HubSpot", "sentiment_delta": -0.21, "sentiment_signal": "declining",
             "top_pain": "Price increase on Sales Hub",
             "summary": "Professional went from $90 to $100 per seat; complaints spiked the same week.",
             "action_bullets": ["Send renewal-season TCO comparisons to HubSpot Professional users."]},
            {"name": "Pipedrive", "sentiment_delta": 0.01, "sentiment_signal": "stable",
             "top_pain": "Reporting limits",
             "summary": "No change; reporting is still the gap to lead with.",
             "action_bullets": ["Keep dashboards first in Pipedrive demos."]},
        ],
        "top_alert": "Salesforce — negative_news: major outage on 2025-12-31.",
        "top_lead": None,
    },
]


def _previous_card(current: dict, competitor: str) -> dict:
    edits = _PREVIOUS_CARD_EDITS[competitor]
    card = copy.deepcopy(current)
    card["generated_at"] = f"{PREVIOUS_DAY}T09:00:00+00:00"
    card["recommended_pitch"] = edits["recommended_pitch"]
    # The latest objection and gap did not exist yet; an older one did.
    objection, evidence, counter, quote = edits["objection"]
    card["objections"] = card.get("objections", [])[:-1] + [
        {"objection": objection, "evidence": evidence, "counter": counter, "proof_quote": quote},
    ]
    gap, freq, advantage = edits["gap"]
    card["feature_gaps"] = card.get("feature_gaps", [])[1:] + [
        {"gap": gap, "frequency": freq, "your_advantage": advantage},
    ]
    return card


def seed_previous_battlecards() -> int:
    from modules.battlecard_generator import _BATTLECARD_DIR, _slug

    written = 0
    from modules.settings_store import competitor_names

    for name in competitor_names():
        latest = _BATTLECARD_DIR / f"{_slug(name)}_latest.json"
        if name not in _PREVIOUS_CARD_EDITS or not latest.exists():
            continue
        current = json.loads(latest.read_text(encoding="utf-8"))
        target = _BATTLECARD_DIR / f"{_slug(name)}_{PREVIOUS_DAY.replace('-', '')}.json"
        target.write_text(json.dumps(_previous_card(current, name), indent=2, ensure_ascii=False), encoding="utf-8")
        written += 1
    return written


def seed_digests() -> int:
    init_schema()
    with closing(get_conn()) as conn, conn:
        conn.execute("DELETE FROM digests WHERE is_synthetic = 1")
        conn.executemany(
            "INSERT INTO digests (generated_at, report_json, is_synthetic) VALUES (?, ?, 1)",
            [(d["generated_at"], json.dumps(d, ensure_ascii=False)) for d in _DIGESTS],
        )
    return len(_DIGESTS)


# (competitor, outcome, category, reason, deal, amount, closed_on)
_DEALS = [
    ("Salesforce", "lost", "features", "Needed CPQ and territory management out of the box", "Northwind Logistics", 84000, "2025-11-18"),
    ("Salesforce", "won", "pricing", "Three-year TCO was 40% lower once admin cost was included", "Contoso Retail", 52000, "2025-11-25"),
    ("Salesforce", "won", "support", "Their support had left them waiting two weeks on a sync bug", "Fabrikam Health", 61000, "2025-12-03"),
    ("Salesforce", "won", "reliability", "Moved after the December outage", "Tailspin Toys", 38000, "2025-12-30"),
    ("Salesforce", "lost", "integrations", "Deep existing MuleSoft integration with their ERP", "Adventure Works", 120000, "2025-12-12"),
    ("HubSpot", "lost", "pricing", "HubSpot Starter was cheaper for 5 seats", "Blue Yonder Bikes", 9000, "2025-11-20"),
    ("HubSpot", "lost", "pricing", "Bundled marketing hub discount", "Lucerne Publishing", 14000, "2025-12-08"),
    ("HubSpot", "won", "pricing", "Contact-tier jump would have doubled their bill", "Wide World Importers", 22000, "2025-12-15"),
    ("HubSpot", "lost", "ux", "Sales team already knew the HubSpot UI", "Proseware", 11000, "2025-12-19"),
    ("HubSpot", "won", "features", "Needed custom reports without the Enterprise tier", "Litware", 18000, "2025-12-29"),
    ("Pipedrive", "won", "features", "Outgrew Pipedrive reporting and automation", "Margie's Travel", 16000, "2025-12-02"),
    ("Pipedrive", "lost", "pricing", "Pipedrive Growth plan was half the price", "Alpine Ski House", 6000, "2025-12-22"),
]


def seed_deals() -> int:
    from modules.winloss import record_deal

    init_schema()
    with closing(get_conn()) as conn, conn:
        conn.execute("DELETE FROM deals WHERE is_synthetic = 1")
    for comp, outcome, cat, reason, deal, amount, day in _DEALS:
        record_deal(comp, outcome, cat, reason_text=reason, deal_name=deal, amount=amount,
                    closed_on=day, created_by="demo", is_synthetic=True)
    return len(_DEALS)


def seed_history() -> dict[str, int]:
    return {
        "battlecard_versions": seed_previous_battlecards(),
        "digests": seed_digests(),
        "deals": seed_deals(),
    }


if __name__ == "__main__":
    print(seed_history())
