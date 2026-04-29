from typing import TypedDict


class CompetitorConfig(TypedDict):
    name: str
    g2_slug: str
    trustpilot_slug: str
    reddit_keywords: list[str]


COMPETITORS: list[CompetitorConfig] = [
    {
        "name": "Salesforce",
        "g2_slug": "salesforce-crm",
        "trustpilot_slug": "salesforce.com",
        "reddit_keywords": ["salesforce", "sfdc", "sales cloud"],
    },
    {
        "name": "HubSpot",
        "g2_slug": "hubspot",
        "trustpilot_slug": "hubspot.com",
        "reddit_keywords": ["hubspot", "hubspot crm"],
    },
    {
        "name": "Pipedrive",
        "g2_slug": "pipedrive",
        "trustpilot_slug": "pipedrive.com",
        "reddit_keywords": ["pipedrive"],
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
