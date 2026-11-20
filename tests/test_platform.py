"""Tests for authentication, editable settings, win/loss and Ask RivalSense."""

import pytest


@pytest.fixture()
def db():
    from database.db import init_schema

    init_schema()


@pytest.fixture()
def client():
    from fastapi.testclient import TestClient

    from backend.main import app

    return TestClient(app)


@pytest.fixture()
def auth_on(monkeypatch, db):
    monkeypatch.setenv("AUTH_DISABLED", "false")


def _admin(client, email="admin@example.com", password="correct horse battery"):
    from modules.auth import create_user

    create_user(email, "Admin", password, role="admin")
    assert client.post("/api/auth/login", json={"email": email, "password": password}).status_code == 200


# ── Authentication ────────────────────────────────────────────────────────────


class TestAuth:
    def test_passwords_are_salted_scrypt(self):
        from modules.auth import hash_password, verify_password

        a, b = hash_password("s3cret-password"), hash_password("s3cret-password")
        assert a != b and a.startswith("scrypt$")
        assert verify_password("s3cret-password", a) and not verify_password("wrong", a)
        assert not verify_password("x", "garbage")

    def test_api_requires_a_session(self, auth_on, client):
        assert client.get("/api/meta/competitors").status_code == 401
        assert client.get("/api/auth/status").json()["setup_required"] is True
        _admin(client)
        assert client.get("/api/meta/competitors").status_code == 200
        assert client.get("/api/auth/me").json()["role"] == "admin"
        client.post("/api/auth/logout")
        assert client.get("/api/meta/competitors").status_code == 401

    def test_session_cookie_is_hardened_and_token_not_stored(self, auth_on, client):
        from database.db import query_rows
        from modules.auth import create_user

        create_user("a@example.com", "A", "long enough password")
        resp = client.post("/api/auth/login", json={"email": "A@Example.com", "password": "long enough password"})
        cookie = resp.headers["set-cookie"].lower()
        assert "httponly" in cookie and "samesite=strict" in cookie
        token = resp.cookies.get("rs_session")
        stored = query_rows("SELECT token_hash FROM sessions")[0]["token_hash"]
        assert token and stored != token and len(stored) == 64

    def test_wrong_password_and_lockout(self, auth_on, client):
        from modules.auth import MAX_FAILURES, create_user

        create_user("b@example.com", "B", "long enough password")
        for _ in range(MAX_FAILURES):
            r = client.post("/api/auth/login", json={"email": "b@example.com", "password": "nope"})
            assert r.status_code == 401 and r.json()["detail"] == "Wrong email or password."
        locked = client.post("/api/auth/login", json={"email": "b@example.com", "password": "long enough password"})
        assert locked.status_code == 401 and "Too many" in locked.json()["detail"]

    def test_setup_only_once_and_only_locally(self, auth_on, client, monkeypatch):
        body = {"email": "first@example.com", "name": "First", "password": "long enough password"}
        # TestClient's client host is "testclient": not this machine → refused.
        assert client.post("/api/auth/setup", json=body).status_code == 403
        monkeypatch.setenv("RIVALSENSE_SETUP_TOKEN", "s3t-up")
        assert client.post("/api/auth/setup", json={**body, "setup_token": "bad"}).status_code == 403
        ok = client.post("/api/auth/setup", json={**body, "setup_token": "s3t-up"})
        assert ok.status_code == 200 and ok.json()["role"] == "admin"
        assert client.post("/api/auth/setup", json={**body, "setup_token": "s3t-up"}).status_code == 409

    def test_members_cannot_administer(self, auth_on, client):
        from modules.auth import create_user

        create_user("m@example.com", "Member", "long enough password", role="member")
        client.post("/api/auth/login", json={"email": "m@example.com", "password": "long enough password"})
        assert client.get("/api/settings").status_code == 200                     # can read
        assert client.post("/api/settings/competitors", json={"name": "X", "reddit_keywords": ["x"]}).status_code == 403
        assert client.get("/api/auth/users").status_code == 403

    def test_user_management_guards(self, auth_on, client):
        _admin(client)
        me = client.get("/api/auth/me").json()
        made = client.post("/api/auth/users", json={"email": "rep@example.com", "name": "Rep",
                                                    "password": "long enough password", "role": "member"})
        assert made.status_code == 200
        assert client.post("/api/auth/users", json={"email": "rep@example.com", "name": "Rep",
                                                    "password": "long enough password"}).status_code == 422
        assert client.post("/api/auth/users", json={"email": "x@example.com", "name": "X",
                                                    "password": "short"}).status_code == 422
        assert client.delete(f"/api/auth/users/{me['id']}").status_code == 422     # not yourself
        assert client.patch(f"/api/auth/users/{me['id']}", json={"role": "member"}).status_code == 422
        assert client.delete(f"/api/auth/users/{made.json()['id']}").status_code == 200

    def test_password_change_signs_out_everywhere(self, auth_on, client):
        from modules.auth import create_user, update_user, user_for_token

        user = create_user("c@example.com", "C", "long enough password")
        r = client.post("/api/auth/login", json={"email": "c@example.com", "password": "long enough password"})
        token = r.cookies.get("rs_session")
        assert user_for_token(token)
        update_user(user["id"], password="another long password")
        assert user_for_token(token) is None


# ── Editable settings ─────────────────────────────────────────────────────────


class TestSettings:
    def test_seeded_from_config_then_editable(self, db, client):
        from config import COMPETITOR_NAMES, OWN_FEATURES
        from modules.settings_store import competitor_names, own_features

        assert competitor_names() == COMPETITOR_NAMES and own_features() == OWN_FEATURES

        new = {"name": "Zoho CRM", "g2_slug": "zoho-crm", "trustpilot_slug": "zoho.com",
               "reddit_keywords": "zoho, zoho crm", "pricing_urls": ["https://www.zoho.com/crm/pricing.html"],
               "careers": {"provider": "lever", "board": "zoho"}, "app_store_id": "1234"}
        saved = client.post("/api/settings/competitors", json=new).json()
        assert saved["reddit_keywords"] == ["zoho", "zoho crm"] and saved["app_store_id"] == 1234
        assert "Zoho CRM" in client.get("/api/meta/competitors").json()["competitors"]
        # The new competitor is accepted everywhere names are validated.
        assert client.get("/api/winloss", params={"competitor": "Zoho CRM"}).status_code == 200

        renamed = client.put("/api/settings/competitors/Zoho CRM", json={**new, "name": "Zoho"})
        assert renamed.status_code == 200 and "Zoho" in competitor_names() and "Zoho CRM" not in competitor_names()
        assert client.delete("/api/settings/competitors/Zoho").status_code == 200
        assert client.get("/api/winloss", params={"competitor": "Zoho"}).status_code == 404

        r = client.put("/api/settings/own-features", json={"features": ["  Flat  Rate Pricing", "flat rate pricing", "SSO"]})
        assert r.json()["own_features"] == ["flat rate pricing", "sso"]

    @pytest.mark.parametrize(("patch", "message"), [
        ({"name": ""}, "name"),
        ({"name": "Bad<script>"}, "name"),
        ({"reddit_keywords": []}, "reddit_keywords"),
        ({"pricing_urls": ["http://insecure.example.com"]}, "https"),
        ({"pricing_urls": ["javascript:alert(1)"]}, "https"),
        ({"careers": {"provider": "taleo", "board": "x"}}, "careers.provider"),
        ({"careers": {"provider": "greenhouse", "board": "../../etc"}}, "careers.board"),
        ({"app_store_id": "abc"}, "app_store_id"),
        ({"g2_slug": "a b"}, "g2_slug"),
    ])
    def test_validation(self, db, patch, message):
        from modules.settings_store import SettingsError, validate_competitor

        with pytest.raises(SettingsError, match=message):
            validate_competitor({"name": "Acme", "reddit_keywords": ["acme"], **patch})

    def test_guards(self, db, client):
        assert client.post("/api/settings/competitors", json={"name": "HubSpot", "reddit_keywords": ["x"]}).status_code == 422
        assert client.put("/api/settings/competitors/Nope", json={"name": "Nope", "reddit_keywords": ["x"]}).status_code == 404
        assert client.put("/api/settings/own-features", json={"features": ["  "]}).status_code == 422
        for name in ("Salesforce", "HubSpot"):
            assert client.delete(f"/api/settings/competitors/{name}").status_code == 200
        assert client.delete("/api/settings/competitors/Pipedrive").status_code == 422   # keep one


# ── Win / loss ────────────────────────────────────────────────────────────────


class TestWinLoss:
    def test_categorize(self):
        from modules.winloss import categorize

        assert categorize("Contact-tier pricing jumps") == "pricing"
        assert categorize("Terrible / Outage / Awful") == "reliability"
        assert categorize("Connectors / API limits") == "integrations"
        assert categorize("Support response times") == "support"
        assert categorize("Weather") == "other"

    def test_deal_validation(self, db):
        from modules.winloss import DealError, record_deal

        with pytest.raises(DealError):
            record_deal("HubSpot", "tied", "pricing")
        with pytest.raises(DealError):
            record_deal("HubSpot", "lost", "vibes")
        with pytest.raises(DealError, match="future"):
            record_deal("HubSpot", "lost", "pricing", closed_on="2999-01-01")

    def test_insights_cross_deals_with_reviews(self, db, monkeypatch):
        import pandas as pd

        import modules.pain_point_radar as ppr
        from modules.winloss import record_deal, winloss_insights

        monkeypatch.setattr(ppr, "get_pain_points", lambda c, top_n=20: pd.DataFrame([
            {"topic_label": "Pricing tiers / Contact limits", "mention_count": 40, "avg_severity": 0.8},
            {"topic_label": "Outage / Downtime", "mention_count": 10, "avg_severity": 0.9},
        ]))
        for _ in range(3):
            record_deal("HubSpot", "lost", "pricing", amount=1000, closed_on="2026-01-01")
        record_deal("HubSpot", "lost", "ux", closed_on="2026-01-02")
        record_deal("HubSpot", "won", "pricing", closed_on="2026-01-03")

        data = winloss_insights("HubSpot")
        assert (data["deals"], data["won"], data["lost"], data["win_rate"], data["amount_lost"]) == (5, 1, 4, 0.2, 3000)
        rows = {r["category"]: r for r in data["categories"]}
        assert rows["pricing"]["reading"] == "contested"        # lost on it, and their customers complain
        assert rows["ux"]["reading"] == "strength"              # lost on it, reviews are quiet
        assert rows["reliability"]["reading"] == "untapped"     # reviews complain, deals never mention it
        assert rows["pricing"]["review_topics"] == ["Pricing tiers / Contact limits"]

    def test_api(self, db, client):
        r = client.post("/api/winloss/deals", json={"competitor": "HubSpot", "outcome": "lost",
                                                     "reason_category": "pricing", "deal_name": "Acme"})
        assert r.status_code == 200 and r.json()["created_by"] == "local@localhost"
        assert client.post("/api/winloss/deals", json={"competitor": "Nope", "outcome": "lost",
                                                        "reason_category": "pricing"}).status_code == 404
        body = client.get("/api/winloss", params={"competitor": "HubSpot"}).json()
        assert body["recent"][0]["deal_name"] == "Acme"
        assert client.delete(f"/api/winloss/deals/{r.json()['id']}").status_code == 200
        assert client.delete("/api/winloss/deals/999").status_code == 404


# ── Ask RivalSense ────────────────────────────────────────────────────────────


def _reviews(rows):
    from contextlib import closing

    from database.db import get_conn

    with closing(get_conn()) as conn, conn:
        conn.executemany(
            """INSERT INTO processed_reviews (review_id, source, competitor_name, review_text, rating, date,
                   topic_label, sentiment_score, is_synthetic) VALUES (?, 'g2', ?, ?, 2, '2026-01-01', 'T', -0.3, ?)""",
            [(i + 1, c, t, s) for i, (c, t, s) in enumerate(rows)],
        )


class TestAsk:
    @pytest.fixture(autouse=True)
    def _no_embeddings(self, monkeypatch):
        # Keyword retrieval keeps these tests fast and model-free.
        import modules.ask as ask_mod

        def no_model():
            raise ImportError("no sentence-transformers in this test")

        monkeypatch.setattr(ask_mod, "_model", no_model)

    def test_keyword_retrieval_and_scope(self, db):
        from modules.ask import search

        _reviews([
            ("HubSpot", "The contact tier pricing doubled our bill overnight.", 0),
            ("HubSpot", "Great email builder, love the templates.", 0),
            ("Salesforce", "Pricing is opaque and renewals are expensive.", 1),
        ])
        _reviews_more = [("HubSpot", "The contact tier pricing doubled our bill overnight.", 0)]  # exact duplicate
        from contextlib import closing

        from database.db import get_conn

        with closing(get_conn()) as conn, conn:
            conn.execute("""INSERT INTO processed_reviews (review_id, source, competitor_name, review_text, date,
                            sentiment_score, is_synthetic) VALUES (99, 'g2', ?, ?, '2026-01-02', -0.2, ?)""", _reviews_more[0])
        sources, method = search("Why is pricing a problem?")
        assert len([s for s in sources if "doubled" in s["text"]]) == 1   # duplicates cited once
        assert method == "keyword" and {s["competitor"] for s in sources} == {"HubSpot", "Salesforce"}
        assert all("pric" in s["text"].lower() for s in sources)
        scoped, _ = search("pricing", competitor="HubSpot")
        assert [s["competitor"] for s in scoped] == ["HubSpot"] and scoped[0]["n"] == 1

    def test_retrieval_mode_without_api_key(self, db, client):
        _reviews([("HubSpot", "Contact tier pricing is painful.", 1)])
        body = client.post("/api/ask", json={"question": "What about pricing?", "competitor": "HubSpot"}).json()
        assert body["mode"] == "retrieval" and body["answer"] is None
        assert body["sources"][0]["is_synthetic"] is True

    def test_answer_cites_and_bad_citations_are_dropped(self, db, client, monkeypatch):
        import utils.llm as llm

        _reviews([("HubSpot", "Contact tier pricing is painful.", 0), ("HubSpot", "Pricing jumps at 50k contacts.", 0)])
        seen = {}

        def fake_claude(system, user, **kw):
            seen["prompt"] = user
            return "Pricing tiers hurt [1][2]. Also outages [7]."

        monkeypatch.setattr(llm, "call_claude", fake_claude)
        body = client.post("/api/ask", json={
            "question": "What do they say about pricing?",
            "history": [{"role": "user", "content": "hi"}, {"role": "assistant", "content": "hello"}],
        }).json()
        assert body["mode"] == "claude" and body["cited"] == [1, 2]
        assert "[7]" not in body["answer"] and "[1]" in body["answer"]
        assert "[1] (HubSpot · g2" in seen["prompt"] and "Conversation so far" in seen["prompt"]

    def test_no_match(self, db, client):
        body = client.post("/api/ask", json={"question": "zzzz qqqq"}).json()
        assert body["mode"] == "none" and body["sources"] == []
        assert client.post("/api/ask", json={"question": "hi"}).status_code == 422        # too short
        assert client.post("/api/ask", json={"question": "pricing?", "competitor": "Nope"}).status_code == 404

    def test_vectors_round_trip(self, db):
        import numpy as np

        from modules.ask import store_vectors
        from database.db import query_rows

        store_vectors([5], np.array([[3.0, 4.0]]))
        vec = np.frombuffer(query_rows("SELECT vector FROM review_embeddings")[0]["vector"], dtype="float32")
        assert np.allclose(vec, [0.6, 0.8])                   # stored L2-normalised
