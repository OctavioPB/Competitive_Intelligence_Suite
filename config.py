from pathlib import Path
from typing import NotRequired, TypedDict


class CareersConfig(TypedDict):
    """Public job board of a competitor.

    provider: "greenhouse" | "lever" | "ashby" | "workday".
    board:    Board token (Greenhouse / Lever / Ashby) or, for Workday, the
              full career-site URL, e.g. https://acme.wd1.myworkdayjobs.com/External.
    """

    provider: str
    board: str


class CompetitorConfig(TypedDict):
    name: str
    g2_slug: str
    trustpilot_slug: str
    reddit_keywords: list[str]
    # Market signals (all optional — a missing key just skips that source).
    pricing_urls: NotRequired[list[str]]
    careers: NotRequired[CareersConfig]
    app_store_id: NotRequired[int]       # Apple App Store track id
    capterra_url: NotRequired[str]       # product review page, e.g. https://www.capterra.com/p/<id>/<Name>/reviews/


COMPETITORS: list[CompetitorConfig] = [
    {
        "name": "Salesforce",
        "g2_slug": "salesforce-crm",
        "trustpilot_slug": "salesforce.com",
        "reddit_keywords": ["salesforce", "sfdc", "sales cloud"],
        "pricing_urls": ["https://www.salesforce.com/sales/pricing/"],
        "careers": {
            "provider": "workday",
            "board": "https://salesforce.wd12.myworkdayjobs.com/External_Career_Site",
        },
        "app_store_id": 404249815,
    },
    {
        "name": "HubSpot",
        "g2_slug": "hubspot",
        "trustpilot_slug": "hubspot.com",
        "reddit_keywords": ["hubspot", "hubspot crm"],
        "pricing_urls": ["https://www.hubspot.com/pricing/sales"],
        "careers": {"provider": "greenhouse", "board": "hubspotjobs"},
        "app_store_id": 1107711722,
    },
    {
        "name": "Pipedrive",
        "g2_slug": "pipedrive",
        "trustpilot_slug": "pipedrive.com",
        "reddit_keywords": ["pipedrive"],
        "pricing_urls": ["https://www.pipedrive.com/en/pricing"],
        # No public ATS feed found for Pipedrive's careers site — add one here if it changes.
        "app_store_id": 921456160,
    },
]

OWN_FEATURES: list[str] = [
    "ai email suggestions",
    "flat rate pricing",
    "offline mobile",
    "workflow automation",
    "one-click integrations",
    "real-time collaboration",
    "advanced reporting",
]

SUBREDDITS: list[str] = [
    "CRM",
    "salesforce",
    "hubspot",
    "entrepreneur",
    "smallbusiness",
    "sales",
    "SaaS",
]

# Derived — use this instead of iterating COMPETITORS when only names are needed
COMPETITOR_NAMES: list[str] = [c["name"] for c in COMPETITORS]

# Absolute repo root — anchor for the DB file, caches and model artefacts so the
# app behaves the same regardless of the working directory it is launched from.
PROJECT_ROOT: Path = Path(__file__).resolve().parent
