"""Tests for the battlecard export and the HubSpot / Salesforce lead sync."""

import json

import pytest

_LEAD = {
    "username": "real_user",
    "post_url": "https://reddit.com/r/CRM/comments/abc123/leaving_salesforce",
    "created_at": "2026-11-10",
    "competitor_name": "Salesforce",
    "urgency_score": 0.9,
    "complaint_summary": "Renewal went up 40% <again>",
    "company_signals": ["Acme"],
    "suggested_angle": "Lead with flat pricing",
    "is_synthetic": False,
}


class FakeResponse:
    def __init__(self, status: int = 200, body=None, headers=None) -> None:
        self.status_code = status
        self._body = body if body is not None else {}
        self.headers = headers or {}

    def json(self):
        return self._body


class FakeSession:
    """Records every call; answers from a list of (method, url-substring, response)."""

    def __init__(self, routes) -> None:
        self.routes = list(routes)
        self.calls: list[tuple[str, str, dict]] = []
        self.headers: dict = {}

    def request(self, method, url, **kwargs):
        self.calls.append((method, url, kwargs))
        for i, (m, fragment, resp) in enumerate(self.routes):
            if m == method and fragment in url:
                if isinstance(resp, list):          # sequence of responses for retries
                    return resp.pop(0)
                return resp
        raise AssertionError(f"unexpected call {method} {url}")

    def post(self, url, **kwargs):
        return self.request("POST", url, **kwargs)


# ── Battlecard export ─────────────────────────────────────────────────────────


class TestBattlecardExport:
    _CARD = {
        "competitor": "Salesforce",
        "generated_at": "2025-12-27T09:00:00+00:00",
        "recommended_pitch": "Pitch <script>alert(1)</script>",
        "objections": [{"objection": "Cost", "evidence": "e", "counter": "c", "proof_quote": "q"}],
        "feature_gaps": [],
    }

    def test_html_fallback_is_escaped_and_print_ready(self, monkeypatch) -> None:
        from outputs import pdf_export

        monkeypatch.setattr(pdf_export, "_WEASYPRINT_AVAILABLE", False)
        content, mime = pdf_export.generate_pdf_bytes(self._CARD)
        html = content.decode("utf-8")

        assert mime == "text/html"
        assert "<script>alert(1)</script>" not in html and "&lt;script&gt;" in html
        assert "@media print" in html

    def test_export_filename(self) -> None:
        from outputs.pdf_export import export_filename

        assert export_filename("Salesforce", "application/pdf") == "battlecard_salesforce.pdf"
        assert export_filename("Monday.com CRM", "text/html") == "battlecard_monday_com_crm.html"

    def test_endpoint(self, monkeypatch) -> None:
        from fastapi.testclient import TestClient

        from backend.main import app
        from backend.routers import battlecard as router

        monkeypatch.setattr(router, "load_cached_battlecard", lambda c: self._CARD if c == "Salesforce" else None)
        monkeypatch.setattr(router, "generate_pdf_bytes", lambda card: (b"%PDF-1.7", "application/pdf"))

        with TestClient(app) as client:
            ok = client.get("/api/battlecard/export", params={"competitor": "Salesforce"})
            missing = client.get("/api/battlecard/export", params={"competitor": "HubSpot"})

        assert ok.status_code == 200
        assert ok.headers["content-type"] == "application/pdf"
        assert 'filename="battlecard_salesforce.pdf"' in ok.headers["content-disposition"]
        assert missing.status_code == 404


# ── HubSpot ───────────────────────────────────────────────────────────────────


class TestHubSpot:
    def test_creates_contact_and_note(self) -> None:
        from outputs.crm_sync import HubSpotClient, push_leads

        session = FakeSession([
            ("POST", "/contacts/search", FakeResponse(body={"results": []})),
            ("POST", "/objects/contacts", FakeResponse(201, {"id": "501"})),
            ("POST", "/objects/notes", FakeResponse(201, {"id": "901"})),
        ])
        result = push_leads(HubSpotClient("tok", session), [_LEAD]).summary()

        assert result["created"] == 1 and result["results"][0]["record_id"] == "501"
        assert session.headers["Authorization"] == "Bearer tok"

        contact = session.calls[1][2]["json"]["properties"]
        assert contact["website"] == _LEAD["post_url"] and contact["lifecyclestage"] == "lead"

        note = session.calls[2][2]["json"]
        assert note["associations"][0]["to"]["id"] == "501"
        assert note["associations"][0]["types"][0]["associationTypeId"] == 202
        assert "&lt;again&gt;" in note["properties"]["hs_note_body"], "note body must be HTML-escaped"

    def test_existing_contact_is_not_duplicated(self) -> None:
        from outputs.crm_sync import HubSpotClient, push_leads

        session = FakeSession([
            ("POST", "/contacts/search", FakeResponse(body={"results": [{"id": "77"}]})),
        ])
        result = push_leads(HubSpotClient("tok", session), [_LEAD]).summary()

        assert result["exists"] == 1 and result["created"] == 0
        assert len(session.calls) == 1

    def test_retries_once_on_rate_limit(self, monkeypatch) -> None:
        from outputs import crm_sync

        monkeypatch.setattr(crm_sync.time, "sleep", lambda s: None)
        session = FakeSession([
            ("POST", "/contacts/search", [
                FakeResponse(429, {"message": "slow down"}, {"Retry-After": "1"}),
                FakeResponse(body={"results": [{"id": "77"}]}),
            ]),
        ])
        result = crm_sync.push_leads(crm_sync.HubSpotClient("tok", session), [_LEAD]).summary()

        assert result["exists"] == 1 and len(session.calls) == 2

    def test_api_error_reported_per_lead(self) -> None:
        from outputs.crm_sync import HubSpotClient, push_leads

        session = FakeSession([
            ("POST", "/contacts/search", FakeResponse(401, {"message": "Authentication credentials not found"})),
        ])
        result = push_leads(HubSpotClient("bad", session), [_LEAD, {**_LEAD, "username": "second"}]).summary()

        assert result["failed"] == 2
        assert "Authentication credentials not found" in result["results"][0]["error"]


# ── Salesforce ────────────────────────────────────────────────────────────────


class TestSalesforce:
    def test_creates_lead_with_record_url(self, monkeypatch) -> None:
        from outputs.crm_sync import SalesforceClient, push_leads

        session = FakeSession([
            ("GET", "/query", FakeResponse(body={"records": []})),
            ("POST", "/sobjects/Lead/", FakeResponse(201, {"id": "00Q1", "success": True})),
        ])
        client = SalesforceClient("https://acme.my.salesforce.com/", "tok", session)
        result = push_leads(client, [_LEAD]).summary()

        assert result["created"] == 1
        assert result["results"][0]["record_url"] == "https://acme.my.salesforce.com/lightning/r/Lead/00Q1/view"
        body = session.calls[1][2]["json"]
        assert body["LastName"] == "real_user" and body["Website"] == _LEAD["post_url"]
        assert body["Company"]  # required field on Lead
        assert "Lead with flat pricing" in body["Description"]

    def test_soql_value_is_escaped(self) -> None:
        from outputs.crm_sync import SalesforceClient

        session = FakeSession([("GET", "/query", FakeResponse(body={"records": []}))])
        SalesforceClient("https://x.my.salesforce.com", "tok", session).find_existing("https://r.com/it's\\x")

        soql = session.calls[0][2]["params"]["q"]
        assert soql.endswith("WHERE Website = 'https://r.com/it\\'s\\\\x' LIMIT 1")

    def test_client_credentials_login(self, monkeypatch) -> None:
        from outputs.crm_sync import SalesforceClient

        monkeypatch.setenv("SALESFORCE_INSTANCE_URL", "https://acme.my.salesforce.com")
        monkeypatch.delenv("SALESFORCE_ACCESS_TOKEN", raising=False)
        monkeypatch.setenv("SALESFORCE_CLIENT_ID", "id")
        monkeypatch.setenv("SALESFORCE_CLIENT_SECRET", "secret")
        session = FakeSession([
            ("POST", "/services/oauth2/token", FakeResponse(body={
                "access_token": "fresh", "instance_url": "https://acme.my.salesforce.com",
            })),
        ])

        client = SalesforceClient.from_env(session)

        assert session.calls[0][2]["data"]["grant_type"] == "client_credentials"
        assert client._session.headers["Authorization"] == "Bearer fresh"


# ── Router safety rails ───────────────────────────────────────────────────────


class TestCrmRouter:
    @pytest.fixture
    def client(self, monkeypatch):
        from fastapi.testclient import TestClient

        from backend.main import app

        for var in ("HUBSPOT_ACCESS_TOKEN", "SALESFORCE_INSTANCE_URL", "SALESFORCE_ACCESS_TOKEN",
                    "SALESFORCE_CLIENT_ID", "SALESFORCE_CLIENT_SECRET"):
            monkeypatch.setenv(var, "")
        monkeypatch.setenv("DEMO_MODE", "false")
        with TestClient(app) as c:
            yield c

    def test_status_reports_unconfigured(self, client) -> None:
        body = client.get("/api/crm/status").json()
        assert body == {"demo_mode": False, "hubspot": False, "salesforce": False}

    def test_unconfigured_target_is_503(self, client) -> None:
        resp = client.post("/api/crm/push", json={"target": "hubspot", "leads": [_LEAD]})
        assert resp.status_code == 503

    def test_demo_mode_is_refused(self, client, monkeypatch) -> None:
        monkeypatch.setenv("DEMO_MODE", "true")
        resp = client.post("/api/crm/push", json={"target": "hubspot", "leads": [_LEAD]})
        assert resp.status_code == 409

    def test_fixture_leads_never_sent_even_if_flag_is_cleared(self, client, monkeypatch) -> None:
        from backend.routers import crm as router
        from backend.routers.prospects import FIXTURE_POST_URLS

        sent = []

        class Recorder:
            name = "hubspot"

            def find_existing(self, url):
                return None

            def create(self, lead):
                sent.append(lead["username"])
                return "1", None

        monkeypatch.setattr(router, "client_for", lambda target: Recorder())
        fixture = {**_LEAD, "username": "fixture", "post_url": sorted(FIXTURE_POST_URLS)[0], "is_synthetic": False}

        body = client.post("/api/crm/push", json={"target": "hubspot", "leads": [fixture, _LEAD]}).json()

        assert sent == ["real_user"]
        assert body["skipped"] == 1 and body["created"] == 1

    def test_demo_prospects_are_flagged(self, client) -> None:
        leads = client.get("/api/prospects/demo").json()
        assert leads and all(lead["is_synthetic"] for lead in leads)
        json.dumps(leads)
