"""Synthetic review fixtures for demo mode and test isolation.

Generates ~120 reviews per competitor covering 8 distinct topic areas so
BERTopic can find meaningful clusters. Seeds a fixed random state for
reproducibility.
"""

import random
from datetime import datetime, timedelta
from typing import Any

from config import CompetitorConfig

_SEED = 42

# Topic areas and seed sentences per competitor.
# 8 topics × 3 seeds × 5 elaborations = 120 reviews per competitor.
_FIXTURE_DATA: dict[str, dict[str, list[str]]] = {
    "Salesforce": {
        "pricing": [
            "Salesforce is incredibly expensive. The per-seat licensing alone costs us over $400 per user per month, and that's before add-ons.",
            "The pricing structure is opaque and unpredictable. Every renewal comes with surprise cost increases that management has to approve.",
            "We were quoted $250k per year just for the base CRM. Small companies simply cannot afford Salesforce at this scale.",
        ],
        "learning_curve": [
            "The learning curve is brutal. My sales reps spent three months in training before they could use it productively.",
            "Salesforce is so complex that we had to hire a dedicated admin just to manage the platform. That's an extra $90k salary.",
            "Non-technical users are completely lost. The interface has too many options and the UX feels like it was designed by engineers, not salespeople.",
        ],
        "customisation": [
            "Every customisation requires an expensive consultant. We can't change a single workflow without paying someone $200/hour.",
            "Out of the box it does very little. You have to customise everything, which requires Apex or Lightning development knowledge.",
            "The custom reports module is powerful but requires technical expertise. Marketing can't build their own dashboards without IT help.",
        ],
        "support": [
            "Support response times are appalling. A critical issue took 5 business days to get a response on, and that was with Premium support.",
            "The support team routes tickets endlessly between teams. I've had issues open for 3 weeks with no resolution.",
            "Unless you pay for Signature support, you're basically on your own. The documentation is dense and the community forums are hit-or-miss.",
        ],
        "mobile_app": [
            "The mobile app is a joke compared to the desktop version. You can't access most of the features your reps need in the field.",
            "Mobile is severely limited. No offline access means your field reps are stuck when they lose signal at customer sites.",
            "The iOS app crashes constantly and loses data. We've had reps lose entire meeting notes because the app crashed on submit.",
        ],
        "integration": [
            "Integrating Salesforce with our ERP was a 6-month project that cost more than the annual license. The native connectors are poor.",
            "API limits are a constant problem. We hit our daily API call limit by noon because every tool we use tries to sync with Salesforce.",
            "The integration ecosystem requires expensive third-party tools. Everything needs a connector, and those connectors all cost extra.",
        ],
        "reporting": [
            "Report Builder is clunky and unintuitive. Creating a simple pipeline report requires joining 4 objects and SQL-level logic.",
            "Getting data out of Salesforce is harder than getting data in. The export tools are limited and the BI connectors are brittle.",
            "Dashboard refresh rates are slow and the historical data analysis tools are primitive for the price we pay.",
        ],
        "positive": [
            "Salesforce is the gold standard for enterprise CRM for good reason. The feature depth is unmatched once you're past the learning curve.",
            "The AppExchange ecosystem is genuinely useful. We found pre-built solutions for 80% of our use cases.",
            "For a large sales organisation, Salesforce scales incredibly well. Managing 500 reps across 12 regions works seamlessly.",
        ],
    },
    "HubSpot": {
        "pricing_tiers": [
            "The free tier is basically a bait-and-switch. The moment you need anything useful you're pushed to a $800/month plan.",
            "HubSpot's pricing jumps are predatory. Going from Starter to Professional is a 10x price increase for features that should be basic.",
            "We got locked into a 2-year contract and then discovered we needed features that were locked behind a higher tier. No flexibility.",
        ],
        "email_limits": [
            "The email sending limits are infuriating. We hit our 5,000 email monthly cap in the first week and had to buy overages.",
            "Email deliverability issues are never acknowledged. Our open rates dropped 40% after moving to HubSpot and support blamed us.",
            "Removing the HubSpot branding from emails costs an extra $200/month. That's absurd for a paid plan.",
        ],
        "contact_limits": [
            "The contact tier limits are designed to extract money. We crossed 50k contacts and our bill nearly doubled overnight.",
            "Marketing contacts vs non-marketing contacts is a confusing distinction that exists purely to upsell you to a higher tier.",
            "We had to archive 20,000 contacts to avoid a bill increase. That's not a feature, that's a tax on growth.",
        ],
        "reporting": [
            "HubSpot's reporting is surface-level at best. Custom reports require the Enterprise plan and even then the attribution modelling is weak.",
            "The analytics dashboards look pretty but lack depth. You can't build multi-touch attribution without custom integrations.",
            "Revenue reporting is basic and doesn't connect to our actual billing system without expensive connectors.",
        ],
        "support": [
            "Support quality depends entirely on which tier you're on. Free plan users are basically left to the knowledge base.",
            "Chat support is helpful for simple questions but escalations to email support have 3-4 day response times.",
            "The knowledge base is outdated. Half the screenshots show UI elements that no longer exist after their rebrand.",
        ],
        "automation": [
            "Workflow automation has too many restrictions on lower tiers. Branching logic requires Professional or higher.",
            "Enrollment triggers are unreliable. Contacts sometimes miss workflows and we can't figure out why.",
            "There's no way to bulk-enroll contacts in a workflow without importing and re-importing. A basic workflow management gap.",
        ],
        "integration": [
            "The HubSpot-Salesforce sync is one-directional by default. Getting bidirectional sync requires custom mapping and constant maintenance.",
            "Native integrations work for 80% of use cases but break in edge cases that support can't fix without escalation.",
            "The API is well-documented but rate limits are hit frequently in large data operations.",
        ],
        "positive": [
            "HubSpot is genuinely the best option for SMBs getting started with CRM. The onboarding experience is excellent.",
            "The marketing automation at Professional tier is really powerful once you understand the workflow builder.",
            "HubSpot's content management and SEO tools integrated with the CRM is a genuine differentiator. No other tool does this as seamlessly.",
        ],
    },
    "Pipedrive": {
        "reporting": [
            "Pipedrive's reporting is embarrassingly basic. I can't get a simple forecast by region without exporting to Excel.",
            "The reporting module hasn't changed in 3 years. Basic pipeline analytics are missing and there's no revenue attribution.",
            "We had to build a separate BI dashboard to get the reports we needed. Pipedrive just can't do custom analytics.",
        ],
        "email_marketing": [
            "There's no built-in email marketing in Pipedrive. Every campaign requires a third-party tool and the sync is always out of date.",
            "Email sequences are limited to simple linear flows. Any branching logic requires Zapier, which adds cost and latency.",
            "Email tracking is unreliable. Open events fire inconsistently and the data can't be trusted for follow-up automation.",
        ],
        "customisation": [
            "Custom fields are limited and can't be used in most views or filters. You hit the ceiling fast.",
            "The pipeline view is clean but inflexible. You can't add custom stages with conditional logic.",
            "There's no way to customise the deal card view. Everyone sees the same fields regardless of their role.",
        ],
        "support": [
            "Customer support has gotten worse as the company grew. Response times on chat have gone from minutes to days.",
            "The support team often closes tickets without resolving the underlying issue. You have to reopen the same ticket multiple times.",
            "There's no dedicated account manager on standard plans. You're on your own for complex configuration questions.",
        ],
        "automation": [
            "The automation builder is very basic. If-then logic is limited and there's no multi-branch automation.",
            "Workflow triggers are limited to a handful of events. You can't trigger automation on custom field changes.",
            "We use Zapier for all our automation because Pipedrive's native tools are too limited. That's an extra $100/month.",
        ],
        "ai_features": [
            "Pipedrive has no AI-powered features. No lead scoring, no email suggestions, no deal health indicators.",
            "The AI Sales Assistant feature gives generic tips that aren't personalised to our pipeline stage or deal size.",
            "Competitors are shipping AI-powered forecasting and deal intelligence. Pipedrive is falling behind significantly.",
        ],
        "mobile_app": [
            "The mobile app is usable but lacks key features. You can't access LeadBooster or Web Visitors from mobile.",
            "Offline mode is missing. Our field reps lose all their work when they lose connectivity at client sites.",
            "The mobile app takes 10-15 seconds to load on a fresh open. For a sales rep between meetings that's too slow.",
        ],
        "positive": [
            "Pipedrive has the cleanest pipeline view of any CRM I've used. Drag and drop deal management is intuitive and fast.",
            "The onboarding was genuinely easy. We were fully operational in two weeks with no consultant needed.",
            "For a small sales team that just needs pipeline management, Pipedrive is excellent value. No bloat, no complexity.",
        ],
    },
}

_ELABORATIONS = [
    "We've raised this with their support team multiple times with no resolution.",
    "Our team has been asking for a fix for over a year.",
    "This has cost us deals because our reps can't get the information they need.",
    "I've seen multiple competitors solve this problem years ago.",
    "Management is seriously considering switching because of this.",
    "This alone would make me recommend a competitor to anyone asking.",
    "The workaround we built costs more in dev time than we save.",
    "I wish they would prioritise this in their roadmap.",
    "Three other companies I know have left because of this exact issue.",
    "We've had to hire additional headcount just to manage this gap.",
    "It's the #1 complaint from every person on our sales team.",
    "After two years of hoping for improvement, we're starting to evaluate alternatives.",
    "Honestly a deal-breaker for companies scaling past 50 seats.",
    "The community forums confirm this is a widespread issue, not just us.",
    "We love the product overall but this specific issue is painful.",
    "Would switch immediately if a competitor offered the same core features without this problem.",
    "We've adapted our workflow around this limitation but it slows everyone down.",
    "New hires consistently flag this as a frustration in their onboarding feedback.",
    "Our operations team spends 6 hours a week on workarounds for this.",
    "Despite this flaw the product is still better than what we used before.",
]

_WISH_PHRASES = [
    "I wish they would add better reporting without requiring an enterprise plan.",
    "Would be nice if the mobile app had offline mode.",
    "Please add bulk workflow enrollment — this is a basic feature.",
    "I need a proper territory management system built in.",
    "Would love to see AI-powered lead scoring added to the base tier.",
    "Missing a proper email sequence builder with branching logic.",
    "Need better API rate limits for growing data pipelines.",
    "I wish the pricing was transparent without having to talk to sales.",
]

_SOURCES = ["g2", "trustpilot", "g2", "g2", "trustpilot"]  # weighted toward g2


def _generate_reviews_for_competitor(
    competitor: CompetitorConfig,
    rng: random.Random,
) -> list[dict[str, Any]]:
    """Generate ~120 synthetic reviews for one competitor."""
    name = competitor["name"]
    topics = _FIXTURE_DATA.get(name, {})
    reviews: list[dict[str, Any]] = []

    # Base date for spread (18 months back from a fixed anchor)
    anchor = datetime(2026, 1, 1)

    review_num = 0
    for topic_name, seeds in topics.items():
        is_positive = topic_name == "positive"
        for seed in seeds:
            for elab in rng.sample(_ELABORATIONS, k=min(5, len(_ELABORATIONS))):
                days_back = rng.randint(1, 540)
                review_date = anchor - timedelta(days=days_back)

                if is_positive:
                    text = seed
                    rating = round(rng.uniform(4.0, 5.0), 1)
                else:
                    # Randomly append wish phrase to ~30% of pain point reviews
                    wish = rng.choice(_WISH_PHRASES) if rng.random() < 0.30 else ""
                    text = f"{seed} {elab}" + (f" {wish}" if wish else "")
                    rating = round(rng.uniform(1.5, 3.0), 1)

                review_num += 1
                reviews.append(
                    {
                        "source": rng.choice(_SOURCES),
                        "competitor_name": name,
                        "review_text": text,
                        "rating": rating,
                        "date": review_date.strftime("%Y-%m-%d"),
                        "author_id": f"fixture_user_{review_num:04d}",
                        "helpful_count": rng.randint(0, 50),
                    }
                )

    rng.shuffle(reviews)
    return reviews


def _generate_news_articles_for_competitor(
    competitor: CompetitorConfig,
    rng: random.Random,
) -> list[dict[str, Any]]:
    """Generate synthetic news article fixtures for a competitor."""
    name = competitor["name"]
    anchor = datetime(2026, 1, 1)

    headlines = [
        f"{name} Faces Customer Backlash Over Pricing Increase",
        f"{name} Reports Record Revenue Despite Churn Concerns",
        f"Analysts Question {name}'s Product Roadmap",
        f"{name} Acquires Integration Partner to Close Feature Gap",
        f"{name} Layoffs Hit Customer Success Team, Users Worried",
        f"{name} Outage Leaves Thousands of Sales Teams Without CRM for 6 Hours",
    ]

    articles = []
    for i, headline in enumerate(headlines):
        days_back = rng.randint(10, 500)
        article_date = anchor - timedelta(days=days_back)
        articles.append(
            {
                "source": "newsapi",
                "competitor_name": name,
                "review_text": f"{headline}. Industry observers note growing dissatisfaction among enterprise customers.",
                "rating": None,
                "date": article_date.strftime("%Y-%m-%d"),
                "author_id": f"NewsSource_{i}",
                "helpful_count": 0,
            }
        )
    return articles


def generate(competitor: CompetitorConfig) -> list[dict[str, Any]]:
    """Return ~120 synthetic reviews + news articles for a single competitor.

    Seeded random ensures identical output across runs.

    Args:
        competitor: Competitor config dict from config.COMPETITORS.

    Returns:
        List of review dicts matching the reviews table schema.
    """
    rng = random.Random(_SEED + hash(competitor["name"]) % 1000)
    reviews = _generate_reviews_for_competitor(competitor, rng)
    news = _generate_news_articles_for_competitor(competitor, rng)
    return reviews + news
