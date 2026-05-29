"""Seed rivalsense_demo.db with fixture data and run the full NLP pipeline.

Usage (from project root):
    python scripts/seed_demo_db.py

Creates rivalsense_demo.db in the project root, seeded with:
- ~200 reviews per competitor (fixtures + bad-week scenario)
- Pre-computed processed_reviews (topics, sentiment, entities, wish phrases)
- Pre-generated battlecard JSON stubs for all 3 competitors

The "bad week" scenario injects:
- 15 very negative Salesforce reviews dated 2025-12-26 to 2026-01-01
  → triggers sentiment_drop alert (avg_delta < -0.5)
- 1 Salesforce newsapi article with "outage" keyword dated 2025-12-31
  → triggers negative_news alert
- 15 extra HubSpot reviews dated 2025-12-26 to 2026-01-01
  → triggers review_spike alert (recent > 2× expected)
"""

import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

# Point db.py at the demo database BEFORE any project imports
os.environ["DATABASE_URL"] = "rivalsense_demo.db"
os.environ["DEMO_MODE"] = "false"

sys.path.insert(0, str(Path(__file__).parent.parent))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger("seed_demo_db")

# ── Bad-week fixture content ──────────────────────────────────────────────────

_BAD_WEEK_DATES = [
    "2025-12-26", "2025-12-27", "2025-12-28",
    "2025-12-29", "2025-12-30", "2025-12-31", "2026-01-01",
]

# Positive reviews inserted 30-35 days before bad-week to create a high baseline.
# Without this, the fixture data's existing negative reviews make the 30-day avg
# already negative (~-0.39), which dampens the sentiment_delta to only ~-0.25.
_SALESFORCE_BASELINE_BOOST_DATES = [
    "2025-11-21", "2025-11-22", "2025-11-23", "2025-11-24", "2025-11-25",
    "2025-11-26", "2025-11-27", "2025-11-28", "2025-11-29", "2025-11-30",
    "2025-12-01", "2025-12-02", "2025-12-03", "2025-12-04", "2025-12-05",
]

_SALESFORCE_POSITIVE_REVIEWS = [
    "Salesforce has been outstanding this quarter. Excellent support, great uptime, highly recommend.",
    "Very impressed with Salesforce reliability and their team. Best CRM for enterprise. Love it.",
    "Salesforce is performing excellently. Superb features, wonderful support, very happy with it.",
    "Great experience with Salesforce this month. Excellent platform, outstanding customer success team.",
    "Salesforce is fantastic. Brilliant features, excellent uptime, amazing ROI. Highly satisfied.",
    "Salesforce support has been outstanding. Quick responses, helpful team, excellent resolution.",
    "Excellent performance from Salesforce. The platform is reliable, powerful, and their team is great.",
    "Love using Salesforce. Excellent dashboards, great automation, superb reporting. Very happy.",
    "Salesforce is the best CRM we have used. Excellent features, great support, outstanding reliability.",
    "Outstanding experience with Salesforce this quarter. Brilliant reliability, wonderful team, highly recommend.",
    "Salesforce has exceeded expectations. Excellent uptime, great features, superb customer success.",
    "Very happy with Salesforce. Outstanding reliability, excellent support, great performance.",
    "Salesforce delivers excellent value. Great features, outstanding support, superb uptime.",
    "Loving Salesforce this month. Excellent performance, great team, wonderful customer success.",
    "Salesforce is performing wonderfully. Excellent reliability, outstanding support, highly satisfied.",
]

_SALESFORCE_BAD_WEEK_REVIEWS = [
    "Absolutely terrible. Salesforce crashed completely for 6 hours. Catastrophic data loss. Switching immediately. Worst platform ever.",
    "Horrible outage ruining our entire sales week. Salesforce is awful and their support is useless and incompetent. Never again.",
    "Disgusting how bad Salesforce has become. Third terrible outage in 6 months, horrific support, absurd overpriced renewal. Switching now.",
    "Salesforce is a disaster. Terrible reliability, awful support, outrageous pricing. We hate this platform and are leaving immediately.",
    "Worst SaaS experience ever. Salesforce downtime destroyed our sales targets. Appalling response from support. This is unacceptable garbage.",
    "Awful awful awful. Salesforce failed us completely this week. Data corruption, terrible support, horrible downtime. We are done forever.",
    "Terrible outage costing us thousands. Salesforce support is shockingly bad and incompetent. This is the worst software we have ever used.",
    "Salesforce is absolutely dreadful. Horrible reliability, terrible service, overpriced garbage. Leadership furious. Switching immediately.",
    "Worst software experience in my career. Salesforce outage is catastrophic and their response is appalling and incompetent. Switching now.",
    "Horrific. Salesforce is a terrible platform that has failed us repeatedly. Awful support, terrible uptime. Switching to a competitor today.",
    "Absolutely appalling Salesforce outage. Dreadful platform, horrible customer service. We hate this overpriced garbage. Never again.",
    "Terrible terrible terrible. Salesforce crashed, support is awful, pricing is outrageous. Worst CRM decision we ever made. Done.",
    "Salesforce is shockingly bad this week. Catastrophic downtime ruining our business. Unacceptable terrible service. Switching immediately.",
    "Disgusted with Salesforce after this awful outage. Terrible platform, incompetent support, horrible reliability. Actively switching now.",
    "The worst. Salesforce has been a terrible nightmare this week. Catastrophic failures, awful support, dreadful experience. Leaving today.",
]

_SALESFORCE_OUTAGE_ARTICLE = (
    "Major Salesforce outage leaves thousands of enterprise customers without CRM access for 6 hours. "
    "The downtime, which began early morning on 2025-12-31, caused widespread disruption across "
    "multiple industries. Salesforce's status page acknowledged the incident but provided no ETA. "
    "Customers report data sync failures and API errors across all regions. Analysts warn this "
    "could accelerate customer churn for already price-sensitive segments."
)

_HUBSPOT_SPIKE_REVIEWS = [
    "HubSpot's latest pricing change has upset our entire marketing team. Looking for alternatives.",
    "HubSpot contact limits hit again. Third time this quarter we had to archive active contacts.",
    "Fed up with HubSpot support. Three tickets open, none resolved in two weeks.",
    "HubSpot API limits are making our integration project impossible. Need to find an alternative.",
    "HubSpot raised prices again with 30 days notice. That is not how you treat loyal customers.",
    "The HubSpot workflow builder is broken after the latest update. Automations stopped firing.",
    "HubSpot email deliverability has tanked this month. 40% drop in open rates with no explanation.",
    "Switching from HubSpot to a competitor. The tier pricing model is extractive and unsustainable.",
    "HubSpot contact tier limits hit right before our campaign launch. Terrible timing, no support.",
    "Another HubSpot price increase email in my inbox. Time to seriously evaluate alternatives.",
    "HubSpot API documentation is outdated and support cannot help with custom integrations.",
    "The HubSpot mobile app crashes every time I try to log a call. Basic CRM feature broken.",
    "HubSpot customer support used to be excellent. Now it is automated responses and long waits.",
    "Disappointed by HubSpot's removal of features from our tier without any prior notice.",
    "HubSpot has become what it used to criticise Salesforce for — overpriced and bloated.",
]

# ── Pre-built battlecard stubs (avoids Claude API calls during seeding) ───────

_STUB_BATTLECARDS: dict[str, dict] = {
    "Salesforce": {
        "competitor": "Salesforce",
        "generated_at": "2025-12-27T09:00:00+00:00",
        "recommended_pitch": (
            "Salesforce customers consistently report three breaking points: unpredictable pricing "
            "that jumps at every renewal, support that disappears when it matters most, and a "
            "learning curve that demands an expensive admin just to maintain basic workflows. "
            "We solve all three — flat rate pricing, dedicated onboarding, and a UI your reps "
            "can use on day one without a consultant."
        ),
        "objections": [
            {
                "objection": "We've invested years customising Salesforce — migration risk is too high.",
                "evidence": "Pricing pain point — 42 mentions, severity 0.82 (rising ↑)",
                "counter": (
                    "Our migration team handles the full data transfer and workflow rebuild with "
                    "a guaranteed 30-day parallel run. If anything breaks, we fix it before you "
                    "cut over — zero downside risk to your existing pipeline."
                ),
                "proof_quote": (
                    "Every customisation in Salesforce requires an expensive consultant. "
                    "I've spent $200/hour just to change a single workflow. That alone "
                    "would make me recommend a competitor to anyone asking."
                ),
            },
            {
                "objection": "Our enterprise requires the depth of features Salesforce provides.",
                "evidence": "Learning curve pain point — 38 mentions, severity 0.76 (stable →)",
                "counter": (
                    "Our enterprise tier matches Salesforce's core CRM feature set with native "
                    "AI lead scoring, territory management, and advanced reporting — all included "
                    "in the base price, not sold as separate add-ons."
                ),
                "proof_quote": (
                    "Salesforce is so complex we had to hire a dedicated admin at $90k salary "
                    "just to manage the platform. New hires consistently flag this in their "
                    "onboarding feedback."
                ),
            },
            {
                "objection": "Salesforce has a large partner ecosystem we rely on.",
                "evidence": "Integration pain point — 31 mentions, severity 0.71 (rising ↑)",
                "counter": (
                    "We offer 200+ one-click native integrations covering your core stack — "
                    "no connector middleware required. For custom integrations, our REST API "
                    "has no daily call limits at the enterprise tier."
                ),
                "proof_quote": (
                    "Integrating Salesforce with our ERP was a 6-month project that cost more "
                    "than the annual license. The native connectors are poor and everything "
                    "needs an expensive third-party connector."
                ),
            },
            {
                "objection": "Support quality concern — what happens when we have a critical issue?",
                "evidence": "Support pain point — 29 mentions, severity 0.68 (stable →)",
                "counter": (
                    "Every plan includes a named customer success manager and a 4-hour SLA "
                    "for critical issues — no additional tier required. Our average first "
                    "response time is 47 minutes across all severity levels."
                ),
                "proof_quote": (
                    "A critical issue took 5 business days to get a response on, and that was "
                    "with Salesforce Premium support. The support team routes tickets endlessly "
                    "between teams with no resolution."
                ),
            },
            {
                "objection": "Field reps use the mobile app — is your mobile experience solid?",
                "evidence": "Mobile app pain point — 24 mentions, severity 0.61 (stable →)",
                "counter": (
                    "Our mobile app is a full-feature mirror of the desktop, with offline mode "
                    "for field reps who lose connectivity at customer sites — a capability "
                    "Salesforce charges separately for and still delivers inconsistently."
                ),
                "proof_quote": (
                    "The Salesforce mobile app is a joke compared to desktop. No offline access "
                    "means our field reps are stuck when they lose signal. We've had reps "
                    "lose entire meeting notes because the app crashed on submit."
                ),
            },
        ],
        "feature_gaps": [
            {
                "gap": "Offline mobile access for field reps",
                "frequency": 18,
                "your_advantage": "Full offline mode included in all tiers — data syncs automatically when connectivity returns.",
            },
            {
                "gap": "AI-powered email suggestions",
                "frequency": 14,
                "your_advantage": "Native AI email suggestions trained on your company's top-performing sequences, included in Pro tier.",
            },
            {
                "gap": "Transparent flat rate pricing",
                "frequency": 11,
                "your_advantage": "Single flat monthly rate per seat — no add-ons, no surprise renewals, no per-module licensing.",
            },
            {
                "gap": "Advanced reporting without enterprise plan",
                "frequency": 9,
                "your_advantage": "Full reporting suite including revenue attribution and custom dashboards available from Professional tier.",
            },
            {
                "gap": "Workflow automation without consultants",
                "frequency": 8,
                "your_advantage": "Visual drag-and-drop automation builder — no Apex or Lightning knowledge required.",
            },
        ],
    },
    "HubSpot": {
        "competitor": "HubSpot",
        "generated_at": "2025-12-27T09:00:00+00:00",
        "recommended_pitch": (
            "HubSpot customers hit three walls as they grow: contact tier pricing that bills "
            "them for their own customer list, email sending limits that cap campaigns mid-month, "
            "and a reporting layer that requires Enterprise to do anything meaningful. "
            "We offer unlimited contacts, uncapped email volume, and full reporting — "
            "all on a single flat-rate plan."
        ),
        "objections": [
            {
                "objection": "HubSpot's all-in-one marketing + CRM integration is hard to replace.",
                "evidence": "Contact limits pain point — 44 mentions, severity 0.79 (rising ↑)",
                "counter": (
                    "Our platform integrates CRM, marketing automation, and content management "
                    "natively — with unlimited contacts at every tier. You never pay more "
                    "because your pipeline grew."
                ),
                "proof_quote": (
                    "We crossed 50k contacts and our bill nearly doubled overnight. "
                    "The contact tier limits are designed to extract money — it's not a feature, "
                    "it's a tax on growth."
                ),
            },
            {
                "objection": "We've built workflows in HubSpot that would be painful to rebuild.",
                "evidence": "Automation pain point — 36 mentions, severity 0.72 (rising ↑)",
                "counter": (
                    "Our migration service exports your HubSpot workflows and rebuilds them "
                    "in our builder in under 2 weeks, including branching logic and custom "
                    "triggers that HubSpot locks behind its Professional tier."
                ),
                "proof_quote": (
                    "Workflow automation has too many restrictions on lower tiers. "
                    "Branching logic requires Professional or higher — a feature that should "
                    "be standard on any paid plan."
                ),
            },
            {
                "objection": "HubSpot's reporting dashboards are familiar to our marketing team.",
                "evidence": "Reporting pain point — 28 mentions, severity 0.65 (stable →)",
                "counter": (
                    "Our reporting layer includes multi-touch attribution, revenue reporting, "
                    "and custom dashboard builder from the Professional tier — no Enterprise "
                    "upgrade required. Your team gets more insight at a lower price point."
                ),
                "proof_quote": (
                    "HubSpot's reporting is surface-level at best. Custom reports require "
                    "the Enterprise plan and even then the attribution modelling is weak. "
                    "We had to build a separate BI dashboard to get the reports we needed."
                ),
            },
            {
                "objection": "HubSpot support has been reliable for us.",
                "evidence": "Support pain point — 22 mentions, severity 0.58 (stable →)",
                "counter": (
                    "Every customer gets a named CSM and 24/7 live chat — not just the "
                    "top tier. Our NPS score is 72 vs the industry average of 43, "
                    "measured by G2 verified reviews."
                ),
                "proof_quote": (
                    "Support quality depends entirely on which tier you're on. "
                    "Free plan users are basically left to the knowledge base, and "
                    "escalations to email support have 3-4 day response times."
                ),
            },
            {
                "objection": "HubSpot's email marketing tools are tightly integrated with CRM.",
                "evidence": "Email limits pain point — 19 mentions, severity 0.55 (declining ↓)",
                "counter": (
                    "Our email marketing is fully native with unlimited sends at Professional "
                    "tier — no monthly caps, no overage billing, no branding tax. "
                    "Deliverability is managed by our team with proactive domain monitoring."
                ),
                "proof_quote": (
                    "The email sending limits are infuriating. We hit our monthly cap in the "
                    "first week and had to buy overages. Removing HubSpot branding costs "
                    "an extra $200/month — absurd for a paid plan."
                ),
            },
        ],
        "feature_gaps": [
            {
                "gap": "Unlimited contacts without tier jumps",
                "frequency": 22,
                "your_advantage": "Flat-rate pricing with unlimited contacts — no billing shock when your pipeline grows.",
            },
            {
                "gap": "Bulk workflow enrollment",
                "frequency": 16,
                "your_advantage": "One-click bulk enrollment with full filter logic — enroll any segment instantly without re-importing.",
            },
            {
                "gap": "Advanced reporting on Professional tier",
                "frequency": 12,
                "your_advantage": "Full multi-touch attribution and revenue reporting available from Professional, not Enterprise.",
            },
            {
                "gap": "AI-powered lead scoring",
                "frequency": 9,
                "your_advantage": "Native AI lead scoring trained on your historical conversion data, included from Professional tier.",
            },
            {
                "gap": "Transparent API rate limits",
                "frequency": 7,
                "your_advantage": "Generous API limits with burst allowances — no daily cap surprises in large data operations.",
            },
        ],
    },
    "Pipedrive": {
        "competitor": "Pipedrive",
        "generated_at": "2025-12-27T09:00:00+00:00",
        "recommended_pitch": (
            "Pipedrive teams outgrow the platform at three predictable moments: when they need "
            "reporting beyond a basic pipeline view, when they want email marketing without "
            "paying for a separate tool, and when AI features become table stakes for their "
            "industry. We're the natural next step — same clean pipeline UX, full reporting, "
            "native email, and AI lead scoring built in."
        ),
        "objections": [
            {
                "objection": "Pipedrive's pipeline view is clean — we've built our process around it.",
                "evidence": "Reporting pain point — 38 mentions, severity 0.74 (rising ↑)",
                "counter": (
                    "Our pipeline view uses the same drag-and-drop card model Pipedrive popularised, "
                    "with the addition of native revenue forecasting, territory views, and custom "
                    "field filters — all in the same clean interface your reps already understand."
                ),
                "proof_quote": (
                    "Pipedrive's reporting is embarrassingly basic. I can't get a simple forecast "
                    "by region without exporting to Excel. The module hasn't changed in 3 years "
                    "and basic pipeline analytics are completely missing."
                ),
            },
            {
                "objection": "We use Zapier to fill Pipedrive's gaps — that works for us.",
                "evidence": "Automation pain point — 31 mentions, severity 0.68 (stable →)",
                "counter": (
                    "We replace your Zapier spend with native automations — branching logic, "
                    "multi-step workflows, and custom field triggers all built in. "
                    "The average Pipedrive customer saves $150/month in Zapier costs at migration."
                ),
                "proof_quote": (
                    "We use Zapier for all our automation because Pipedrive's native tools are "
                    "too limited. That's an extra $100/month just to cover basic workflow gaps "
                    "that should be included in the core product."
                ),
            },
            {
                "objection": "Pipedrive onboarding was easy — we don't want implementation complexity.",
                "evidence": "Email marketing pain point — 26 mentions, severity 0.63 (rising ↑)",
                "counter": (
                    "Our guided onboarding takes 2 weeks with a dedicated implementation "
                    "specialist. We import your Pipedrive data, rebuild your pipeline stages, "
                    "and train your team — before you're charged a single dollar."
                ),
                "proof_quote": (
                    "There's no built-in email marketing in Pipedrive. Every campaign requires "
                    "a third-party tool and the sync is always out of date. Email sequences "
                    "are limited to simple linear flows."
                ),
            },
            {
                "objection": "Pipedrive support has been responsive on our plan.",
                "evidence": "Support pain point — 21 mentions, severity 0.57 (declining ↓)",
                "counter": (
                    "We include a named customer success manager on all plans — no dedicated "
                    "account manager is gated behind a premium tier. Complex configuration "
                    "questions get answered within 4 hours, not days."
                ),
                "proof_quote": (
                    "Customer support has gotten worse as the company grew. Response times on "
                    "chat have gone from minutes to days. There's no dedicated account manager "
                    "on standard plans — you're on your own for complex questions."
                ),
            },
            {
                "objection": "AI features are not critical for our sales process today.",
                "evidence": "AI features pain point — 18 mentions, severity 0.52 (rising ↑)",
                "counter": (
                    "Our AI lead scoring and deal health indicators are optional overlays — "
                    "they don't change your workflow, they just surface which deals need "
                    "attention. Teams that enable them report 23% higher close rates in "
                    "the first quarter."
                ),
                "proof_quote": (
                    "Pipedrive has no AI-powered features. No lead scoring, no email suggestions, "
                    "no deal health indicators. Competitors are shipping AI-powered forecasting "
                    "and deal intelligence — Pipedrive is falling behind significantly."
                ),
            },
        ],
        "feature_gaps": [
            {
                "gap": "Advanced reporting and revenue forecasting",
                "frequency": 20,
                "your_advantage": "Native revenue forecasting by region, rep, and product line — no Excel export required.",
            },
            {
                "gap": "Built-in email marketing with branching sequences",
                "frequency": 15,
                "your_advantage": "Full email sequence builder with branching logic, A/B testing, and deliverability monitoring included.",
            },
            {
                "gap": "AI-powered lead scoring",
                "frequency": 11,
                "your_advantage": "AI lead scoring trained on your historical win/loss data — surfaces your most likely converters.",
            },
            {
                "gap": "Workflow automation with custom field triggers",
                "frequency": 9,
                "your_advantage": "Trigger automations on any custom field change — no Zapier required for complex multi-step flows.",
            },
            {
                "gap": "Offline mobile access",
                "frequency": 7,
                "your_advantage": "Full offline mobile mode — reps can log calls, update deals, and capture notes without connectivity.",
            },
        ],
    },
}


# ── Database helpers ──────────────────────────────────────────────────────────

_INSERT_REVIEW_SQL = """
    INSERT INTO reviews (source, competitor_name, review_text, rating, date, author_id, helpful_count)
    VALUES (?, ?, ?, ?, ?, ?, ?)
"""


def _insert_reviews(rows: list[dict]) -> None:
    from database.db import executemany

    params = [
        (
            r["source"],
            r["competitor_name"],
            r["review_text"],
            r.get("rating"),
            r.get("date", ""),
            r.get("author_id", ""),
            r.get("helpful_count", 0),
        )
        for r in rows
    ]
    executemany(_INSERT_REVIEW_SQL, params)


def _reset_db() -> None:
    """Delete rivalsense_demo.db and recreate the schema."""
    from database.db import init_schema

    demo_path = Path("rivalsense_demo.db")
    if demo_path.exists():
        demo_path.unlink()
        logger.info("Deleted existing rivalsense_demo.db")

    init_schema()
    logger.info("Schema initialised at rivalsense_demo.db")


def _seed_fixtures() -> None:
    """Insert base fixture data (~126 reviews per competitor)."""
    from config import COMPETITORS
    from ingestion import fixtures as fixture_module

    for competitor in COMPETITORS:
        rows = fixture_module.generate(competitor)
        _insert_reviews(rows)
        logger.info("[%s] Inserted %d fixture rows", competitor["name"], len(rows))


def _seed_bad_week() -> None:
    """Insert the 'bad week' scenario to trigger all 3 alert types."""
    import random

    rng = random.Random(99)

    # Salesforce: 15 positive reviews dated 30-40 days BEFORE the bad week.
    # This lifts the 30-day rolling baseline to ~+0.7 so the bad-week drop
    # produces sentiment_delta < -0.5 (threshold for the alert to fire).
    boost_rows = []
    for i, text in enumerate(_SALESFORCE_POSITIVE_REVIEWS):
        date = _SALESFORCE_BASELINE_BOOST_DATES[i % len(_SALESFORCE_BASELINE_BOOST_DATES)]
        boost_rows.append(
            {
                "source": rng.choice(["g2", "trustpilot"]),
                "competitor_name": "Salesforce",
                "review_text": text,
                "rating": round(rng.uniform(4.2, 5.0), 1),
                "date": date,
                "author_id": f"baseline_boost_{i:03d}",
                "helpful_count": rng.randint(1, 15),
            }
        )
    _insert_reviews(boost_rows)
    logger.info("[Salesforce] Inserted %d baseline-boost positive reviews", len(boost_rows))

    # Salesforce: 15 very negative reviews dated in the last 7 days
    sf_rows = []
    for i, text in enumerate(_SALESFORCE_BAD_WEEK_REVIEWS):
        date = rng.choice(_BAD_WEEK_DATES)
        sf_rows.append(
            {
                "source": rng.choice(["g2", "trustpilot"]),
                "competitor_name": "Salesforce",
                "review_text": text,
                "rating": round(rng.uniform(1.0, 1.8), 1),
                "date": date,
                "author_id": f"badweek_sf_{i:03d}",
                "helpful_count": rng.randint(5, 40),
            }
        )
    _insert_reviews(sf_rows)
    logger.info("[Salesforce] Inserted %d bad-week reviews", len(sf_rows))

    # Salesforce: outage news article dated 2025-12-31
    news_row = [
        {
            "source": "newsapi",
            "competitor_name": "Salesforce",
            "review_text": _SALESFORCE_OUTAGE_ARTICLE,
            "rating": None,
            "date": "2025-12-31",
            "author_id": "newsapi_outage_001",
            "helpful_count": 0,
        }
    ]
    _insert_reviews(news_row)
    logger.info("[Salesforce] Inserted outage news article")

    # HubSpot: 15 extra reviews to create a review spike
    hs_rows = []
    for i, text in enumerate(_HUBSPOT_SPIKE_REVIEWS):
        date = rng.choice(_BAD_WEEK_DATES)
        hs_rows.append(
            {
                "source": rng.choice(["g2", "trustpilot", "reddit"]),
                "competitor_name": "HubSpot",
                "review_text": text,
                "rating": round(rng.uniform(1.5, 2.5), 1),
                "date": date,
                "author_id": f"badweek_hs_{i:03d}",
                "helpful_count": rng.randint(2, 25),
            }
        )
    _insert_reviews(hs_rows)
    logger.info("[HubSpot] Inserted %d spike reviews", len(hs_rows))


def _run_pipeline() -> None:
    """Run the full NLP pipeline for all competitors."""
    from config import COMPETITORS
    from pipeline.run_pipeline import run_for_competitor

    for competitor in COMPETITORS:
        try:
            n = run_for_competitor(competitor)
            logger.info("[%s] Pipeline complete: %d processed_reviews", competitor["name"], n)
        except Exception as exc:
            logger.error("[%s] Pipeline failed: %s", competitor["name"], exc)


def _write_battlecard_stubs() -> None:
    """Write pre-built battlecard JSON stubs to outputs/battlecards/."""
    battlecard_dir = Path("outputs/battlecards")
    battlecard_dir.mkdir(parents=True, exist_ok=True)

    from modules.battlecard_generator import battlecard_to_markdown

    for competitor, card in _STUB_BATTLECARDS.items():
        slug = competitor.lower().replace(" ", "_")
        payload = json.dumps(card, indent=2, ensure_ascii=False)

        (battlecard_dir / f"{slug}_latest.json").write_text(payload, encoding="utf-8")

        date_tag = card["generated_at"][:10].replace("-", "")
        (battlecard_dir / f"{slug}_{date_tag}.json").write_text(payload, encoding="utf-8")
        (battlecard_dir / f"{slug}_latest.md").write_text(
            battlecard_to_markdown(card), encoding="utf-8"
        )
        logger.info("Battlecard stub written: %s", slug)


def _print_summary() -> None:
    """Log a row-count summary for the demo DB."""
    from database.db import query_df

    reviews = query_df("SELECT competitor_name, COUNT(*) AS n FROM reviews GROUP BY competitor_name")
    processed = query_df(
        "SELECT competitor_name, COUNT(*) AS n FROM processed_reviews GROUP BY competitor_name"
    )

    logger.info("=== Demo DB summary ===")
    logger.info("reviews table:")
    for _, row in reviews.iterrows():
        logger.info("  %-12s %d rows", row["competitor_name"], row["n"])
    logger.info("processed_reviews table:")
    for _, row in processed.iterrows():
        logger.info("  %-12s %d rows", row["competitor_name"], row["n"])
    logger.info("========================")


def main() -> None:
    logger.info("=== RivalSense Demo DB Seeder ===")
    logger.info("Target: rivalsense_demo.db")

    _reset_db()
    _seed_fixtures()
    _seed_bad_week()
    _run_pipeline()
    _write_battlecard_stubs()
    _print_summary()

    logger.info("Done. Run: .\\demo.ps1 to launch the React + FastAPI stack.")


if __name__ == "__main__":
    main()
