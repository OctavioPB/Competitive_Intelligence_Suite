"""Tests for market signals (pricing pages, job boards) and the new review sources."""

from datetime import date

import pytest


@pytest.fixture()
def db():
    """Schema on the per-test isolated database (see conftest)."""
    from database.db import init_schema

    init_schema()


# ── Pricing-page extraction ───────────────────────────────────────────────────

_PRICING_HTML = """
<html><head><title>Pricing</title><script>var price = "$999";</script></head><body>
  <nav>Currency converter</nav><span>AU$</span>
  <div class="plan"><h3>Starter</h3><p>Essential tools for small teams getting going fast</p>
    <span>Starts at</span><span>$</span><span>15</span><span>/mo/seat</span>
    <span>(Billed annually)</span></div>
  <div class="plan"><h3>Professional</h3><p>Comprehensive software to automate your whole team</p>
    <span>US$</span><span>90</span><span>/mo/seat</span><span>kr</span></div>
  <div class="plan"><h3>Pro Suite</h3><span>$ 100</span><span>USD/User/Month</span></div>
  <p>How much does it cost? Starter Suite costs $25 USD per user, per month and includes email.</p>
  <span>Professional</span><span>US$ 90</span><span>/mo/seat</span>
</body></html>
"""


class TestPricingExtraction:
    def test_price_points_carry_plan_and_unit(self):
        from ingestion.scraper_pricing import extract_price_points

        points = extract_price_points(_PRICING_HTML)

        assert "Starter: $15 /mo/seat" in points            # split "$" / "15" rejoined
        assert "Professional: US$90 /mo/seat" in points     # "kr" / "US$" never become labels
        assert "Pro Suite: $100 USD/User/Month" in points   # 3-letter plan words are not units
        assert any(p.startswith("How much does it cost?") for p in points)  # sentences kept whole
        assert not any("999" in p for p in points)           # script contents ignored
        assert len(points) == len(set(points))               # repeated sections deduplicated

    def test_change_description_pairs_moves_by_plan(self):
        from modules.market_signals import describe_changes

        lines = describe_changes(
            added=["Professional: $100 /mo/seat", "Onboarding: $1,500"],
            removed=["Professional: $90 /mo/seat", "Sequences: $500"],
        )
        assert lines == [
            "Professional: $90 /mo/seat → $100 /mo/seat",
            "Removed Sequences: $500",
            "New Onboarding: $1,500",
        ]


# ── Anti-bot walls and the static → headless fallback ─────────────────────────


class TestBrowser:
    def test_bot_wall_names_the_protection(self):
        from ingestion.browser import bot_wall

        assert bot_wall(403, '<script src="https://ct.captcha-delivery.com/c.js"></script>') == "DataDome"
        assert bot_wall(403, "<title>Just a moment...</title><div id='cf-chl-widget'>") == "Cloudflare"
        assert bot_wall(200, "<title>Pricing</title><p>$10</p>") is None

    def test_static_html_is_used_when_it_has_the_content(self, monkeypatch):
        from ingestion import browser

        monkeypatch.setattr(browser, "fetch_static", lambda url: browser.Page(url, 200, "<p>ok</p>", "", False))
        monkeypatch.setattr(browser, "render", lambda *a, **k: pytest.fail("must not render"))
        monkeypatch.setattr(browser, "playwright_available", lambda: True)

        page = browser.fetch_html("https://x.test", lambda html: "ok" in html)
        assert page.rendered is False

    def test_blocked_everywhere_raises_with_the_wall_name(self, monkeypatch):
        from ingestion import browser

        wall = "<title>Just a moment...</title>"
        monkeypatch.setattr(browser, "fetch_static", lambda url: browser.Page(url, 403, wall, "Just a moment...", False))
        monkeypatch.setattr(browser, "render", lambda url, **k: browser.Page(url, 403, wall, "Just a moment...", True))
        monkeypatch.setattr(browser, "playwright_available", lambda: True)

        with pytest.raises(browser.FetchError, match="static: blocked by Cloudflare.*rendered: blocked by Cloudflare"):
            browser.fetch_html("https://x.test", lambda html: True)

    def test_g2_reports_the_block_instead_of_failing_silently(self, monkeypatch):
        from ingestion import browser, scraper_g2
        from config import COMPETITORS

        def blocked(*a, **k):
            raise browser.FetchError("static: blocked by DataDome (HTTP 403)")

        monkeypatch.setattr(browser, "fetch_html", blocked)
        with pytest.raises(scraper_g2.ScrapingError, match="DataDome"):
            scraper_g2.scrape_reviews(COMPETITORS[1], max_pages=1)


# ── Pricing storage and the pricing_change signal ─────────────────────────────


class TestPricingSignal:
    URL = "https://www.hubspot.com/pricing/sales"

    def test_first_unchanged_changed(self, db):
        from database.db import query_df
        from modules.market_signals import record_pricing_check

        v1 = ["Starter: $15 /mo/seat", "Professional: $90 /mo/seat"]
        v2 = ["Starter: $15 /mo/seat", "Professional: $100 /mo/seat"]

        assert record_pricing_check("HubSpot", self.URL, v1, date(2026, 1, 1))["status"] == "first"
        assert record_pricing_check("HubSpot", self.URL, list(reversed(v1)), date(2026, 1, 2))["status"] == "unchanged"
        changed = record_pricing_check("HubSpot", self.URL, v2, date(2026, 1, 3))
        assert changed == {
            "status": "changed",
            "added": ["Professional: $100 /mo/seat"],
            "removed": ["Professional: $90 /mo/seat"],
        }

        rows = query_df("SELECT first_seen, last_seen FROM pricing_snapshots ORDER BY id")
        assert rows.to_dict("records") == [
            {"first_seen": "2026-01-01", "last_seen": "2026-01-02"},   # unchanged check only moved last_seen
            {"first_seen": "2026-01-03", "last_seen": "2026-01-03"},
        ]

    def test_signal_fires_for_recent_change_only(self, db):
        from modules.market_signals import pricing_change_signal, record_pricing_check

        record_pricing_check("HubSpot", self.URL, ["Pro: $90"], date(2026, 1, 1))
        record_pricing_check("HubSpot", self.URL, ["Pro: $100"], date(2026, 1, 5))
        evidence = pricing_change_signal("HubSpot")
        assert evidence and "2026-01-05" in evidence and "Pro: $90 → $100" in evidence

        # Three weeks of unchanged checks later the change is no longer news.
        record_pricing_check("HubSpot", self.URL, ["Pro: $100"], date(2026, 1, 26))
        assert pricing_change_signal("HubSpot") is None


# ── Job boards ────────────────────────────────────────────────────────────────


class TestRoleClassification:
    @pytest.mark.parametrize(("title", "department", "category", "integration"), [
        ("Technical Support Engineer - Tier 2", None, "support", False),
        ("Customer Success Architect", None, "support", False),
        ("Lead Solution Engineer – Tableau", None, "sales", False),
        ("Renewals Manager", None, "sales", False),
        ("Senior Software Engineer, Integrations Platform", None, "engineering", True),
        ("Software Engineer II, Public APIs", "Engineering", "engineering", True),
        ("M&A Security Integration Engineer", None, "engineering", False),
        ("Product Marketing Manager", None, "marketing", False),
        ("Product Manager, Integrations", None, "product", True),
        ("Senior Accounts Payable Coordinator", "Finance", "other", False),
        ("Lead Product Manager, Sales Cloud", None, "product", False),
        ("Senior Software Engineer, Marketing Hub", None, "engineering", False),
        ("Customer Support Engineer, Sales Cloud", None, "support", False),
    ])
    def test_classify(self, title, department, category, integration):
        from modules.market_signals import classify_role

        assert classify_role(title, department) == (category, integration)


def _roles(spec):
    """[(title, days_old)] → postings crawled on 2026-01-31."""
    return [
        {"external_id": str(i), "title": t, "department": None, "location": "Remote", "url": None,
         "posted_date": date.fromordinal(date(2026, 1, 31).toordinal() - age).isoformat()}
        for i, (t, age) in enumerate(spec)
    ]


class TestHiringSignals:
    CRAWL = date(2026, 1, 31)

    def test_support_wave(self, db):
        from modules.market_signals import get_hiring_overview, hiring_signals, record_job_postings

        spec = [("Customer Support Specialist", 3)] * 6 + [("Account Executive", 5)] * 6 + [("Account Executive", 90)]
        record_job_postings("Salesforce", "workday", _roles(spec), self.CRAWL)

        overview = get_hiring_overview("Salesforce")
        assert (overview["open_roles"], overview["new_roles"]) == (13, 12)
        signals = hiring_signals("Salesforce")
        assert len(signals) == 1 and "6 of 12" in signals[0] and "50%" in signals[0]

    def test_no_signal_when_support_share_is_normal(self, db):
        from modules.market_signals import hiring_signals, record_job_postings

        spec = [("Customer Support Specialist", 3)] * 5 + [("Account Executive", 5)] * 30
        record_job_postings("Salesforce", "workday", _roles(spec), self.CRAWL)
        assert hiring_signals("Salesforce") == []

    def test_integration_push_and_closed_roles(self, db):
        from modules.market_signals import get_hiring_overview, hiring_signals, record_job_postings

        first = _roles([("Software Engineer, Public APIs", 2), ("Staff Engineer, Ecosystem", 4),
                        ("Senior Engineer, Data Sync", 6), ("Account Executive", 8)])
        record_job_postings("HubSpot", "greenhouse", first, date(2026, 1, 30))
        # Next crawl: the Account Executive role is gone (closed), the rest still open.
        result = record_job_postings("HubSpot", "greenhouse", first[:3], self.CRAWL)
        assert result == {"seen": 3, "new": 0}

        overview = get_hiring_overview("HubSpot")
        assert overview["open_roles"] == 3 and overview["integration_new"] == 3
        assert any("3 engineering roles on integrations" in s for s in hiring_signals("HubSpot"))


class TestJobBoardProviders:
    def test_workday_dates_and_stop_at_old_postings(self, monkeypatch):
        from ingestion import scraper_jobs

        today = date(2026, 11, 19)
        assert scraper_jobs.workday_posted_date("Posted Today", today) == ("2026-11-19", True)
        assert scraper_jobs.workday_posted_date("Posted 3 Days Ago", today) == ("2026-11-16", True)
        assert scraper_jobs.workday_posted_date("Posted 30+ Days Ago", today)[1] is False

        pages = [
            [{"title": "Support Engineer", "postedOn": "Posted Today", "externalPath": "/job/a", "bulletFields": ["JR1"]}] * 20,
            [{"title": "Account Executive", "postedOn": "Posted 5 Days Ago", "externalPath": "/job/b", "bulletFields": ["JR2"]},
             {"title": "Old role", "postedOn": "Posted 30+ Days Ago", "externalPath": "/job/c", "bulletFields": ["JR3"]}],
        ]
        calls = []

        class Resp:
            status_code = 200

            def __init__(self, body):
                self._body = body

            def json(self):
                return self._body

        def fake_post(url, json, **kwargs):
            calls.append((url, json["offset"]))
            return Resp({"jobPostings": pages[len(calls) - 1]})

        monkeypatch.setattr(scraper_jobs.requests, "post", fake_post)
        monkeypatch.setattr(scraper_jobs.time, "sleep", lambda s: None)

        postings = scraper_jobs.fetch_postings(
            {"provider": "workday", "board": "https://acme.wd5.myworkdayjobs.com/External"}, today=today,
        )
        assert calls[0][0] == "https://acme.wd5.myworkdayjobs.com/wday/cxs/acme/External/jobs"
        assert [c[1] for c in calls] == [0, 20]                      # stopped at the 30+ day posting
        assert len(postings) == 21 and postings[-1]["posted_date"] == "2026-11-14"
        assert postings[0]["url"] == "https://acme.wd5.myworkdayjobs.com/External/job/a"

    def test_greenhouse_lever_ashby_parsers(self, monkeypatch):
        from ingestion import scraper_jobs

        bodies = {
            "greenhouse": {"jobs": [{"id": 1, "title": "Support Rep", "departments": [{"name": "Customer Support"}],
                                     "location": {"name": "Dublin"}, "absolute_url": "https://gh/1",
                                     "first_published": "2026-11-01T10:00:00-04:00"}]},
            "lever": [{"id": "x", "text": "API Engineer", "categories": {"department": "R&D", "team": "Platform",
                                                                         "location": "Berlin"},
                       "hostedUrl": "https://lever/x", "createdAt": 1793491200000}],
            "ashby": {"jobs": [{"id": "y", "title": "AE", "department": "Sales", "location": "NYC",
                                "jobUrl": "https://ashby/y", "publishedAt": "2026-11-02T00:00:00Z"}]},
        }
        monkeypatch.setattr(scraper_jobs, "_get_json",
                            lambda url, **p: next(v for k, v in bodies.items() if k in url))

        gh = scraper_jobs.fetch_postings({"provider": "greenhouse", "board": "acme"})
        assert gh[0] | {} == {"external_id": "1", "title": "Support Rep", "department": "Customer Support",
                              "location": "Dublin", "url": "https://gh/1", "posted_date": "2026-11-01"}
        lv = scraper_jobs.fetch_postings({"provider": "lever", "board": "acme"})
        assert lv[0]["department"] == "R&D / Platform" and lv[0]["posted_date"] == "2026-11-01"
        ab = scraper_jobs.fetch_postings({"provider": "ashby", "board": "acme"})
        assert ab[0]["title"] == "AE" and ab[0]["posted_date"] == "2026-11-02"

        from ingestion.scraper_g2 import ScrapingError
        with pytest.raises(ScrapingError, match="Unsupported"):
            scraper_jobs.fetch_postings({"provider": "taleo", "board": "acme"})


# ── Review sources ────────────────────────────────────────────────────────────


class TestReviewSources:
    def test_app_store_feed(self):
        from ingestion.scraper_appstore import parse_feed

        payload = {"feed": {"entry": [
            {"im:name": {"label": "HubSpot"}},          # app metadata — no rating
            {"author": {"name": {"label": "sam"}}, "updated": {"label": "2026-11-04T10:00:00-07:00"},
             "im:rating": {"label": "2"}, "title": {"label": "Sync broke"},
             "content": {"label": "Contacts stopped syncing after the update."}, "im:voteSum": {"label": "3"}},
        ]}}
        rows = parse_feed(payload, "HubSpot")
        assert rows == [{
            "source": "app_store", "competitor_name": "HubSpot",
            "review_text": "Sync broke. Contacts stopped syncing after the update.",
            "rating": 2.0, "date": "2026-11-04", "author_id": "sam", "helpful_count": 3,
        }]
        # A page with a single entry comes back as an object, not a list.
        single = {"feed": {"entry": payload["feed"]["entry"][1]}}
        assert len(parse_feed(single, "HubSpot")) == 1

    def test_jsonld_reviews(self):
        from ingestion.structured_reviews import jsonld_reviews

        html = """<script type="application/ld+json">{"@graph": [{"@type": "Product", "review": [
            {"@type": "Review", "name": "Too pricey", "reviewBody": "Renewal went up 30%.",
             "reviewRating": {"ratingValue": 4, "bestRating": 10}, "datePublished": "2026-10-01T00:00:00Z",
             "author": {"@type": "Person", "name": "Ana"}}]}]}</script>
            <script type="application/ld+json">not json</script>"""
        assert jsonld_reviews(html) == [
            {"text": "Too pricey. Renewal went up 30%.", "rating": 2.0, "date": "2026-10-01", "author": "Ana"},
        ]

    def test_one_blocked_source_does_not_discard_the_others(self, monkeypatch):
        from config import COMPETITORS
        from ingestion import run_ingestion
        from ingestion.scraper_g2 import ScrapingError

        def blocked():
            raise ScrapingError("blocked by DataDome")

        row = {"source": "app_store", "competitor_name": "HubSpot", "review_text": "ok"}
        monkeypatch.setattr(run_ingestion, "_live_sources", lambda c: [("G2", blocked), ("App Store", lambda: [row])])
        assert run_ingestion._scrape_with_fallback(COMPETITORS[1]) == [row]

        # Only when every live source fails do fixtures stand in.
        monkeypatch.setattr(run_ingestion, "_live_sources", lambda c: [("G2", blocked)])
        rows = run_ingestion._scrape_with_fallback(COMPETITORS[1])
        assert rows and all(r.get("is_synthetic") for r in rows)


# ── Trigger Alerts + API ──────────────────────────────────────────────────────


class TestAlertsAndApi:
    def test_demo_signals_raise_the_new_alerts(self, db):
        from ingestion.signal_fixtures import seed_market_signals
        from modules.trigger_alerts import check_triggers, generate_outreach

        seed_market_signals()
        seed_market_signals()       # idempotent
        alerts = {(a.competitor, a.trigger_type): a for a in check_triggers(["Salesforce", "HubSpot", "Pipedrive"])}

        assert "Professional: $90 /mo/seat → $100 /mo/seat" in alerts[("HubSpot", "pricing_change")].evidence_summary
        assert "support" in alerts[("Salesforce", "hiring_signal")].evidence_summary
        assert "integrations" in alerts[("HubSpot", "hiring_signal")].evidence_summary
        assert ("Pipedrive", "pricing_change") not in alerts
        for alert in alerts.values():
            assert alert.competitor in generate_outreach(alert, llm=False)

    def test_endpoints(self, db, monkeypatch):
        from fastapi.testclient import TestClient

        from backend.main import app
        from ingestion.signal_fixtures import seed_market_signals

        seed_market_signals()
        client = TestClient(app)

        pricing = client.get("/api/signals/pricing", params={"competitor": "HubSpot"}).json()
        page = pricing["pages"][0]
        assert page["is_synthetic"] and page["last_change"]["date"] == "2025-12-29"
        assert page["last_checked"] == "2026-01-01" and page["versions"] == 2

        hiring = client.get("/api/signals/hiring", params={"competitor": "Salesforce"}).json()
        assert hiring["board"]["recent_only"] is True and hiring["by_category"][0]["category"] == "support"
        assert client.get("/api/signals/hiring", params={"competitor": "Pipedrive"}).json()["board"] is None

        assert client.get("/api/signals/pricing", params={"competitor": "Nope"}).status_code == 404

        monkeypatch.setenv("DEMO_MODE", "true")
        resp = client.post("/api/signals/refresh", json={"competitor": "HubSpot"})
        assert resp.status_code == 409
