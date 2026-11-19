"""Tests for alert history, the prospect pipeline, "what changed" and the comparison view."""

import json
from datetime import date

import pytest


@pytest.fixture()
def db():
    from database.db import init_schema

    init_schema()


def _alert(kind="sentiment_drop", competitor="Salesforce", evidence="drop", key=""):
    from modules.trigger_alerts import Alert

    return Alert(trigger_type=kind, competitor=competitor, evidence_summary=evidence, dedupe_key=key)


# ── Alert history ─────────────────────────────────────────────────────────────


class TestAlertHistory:
    def test_ongoing_signal_is_one_alert(self, db):
        from modules.alert_history import record_alerts

        first = record_alerts([_alert(evidence="delta -0.6")], date(2026, 1, 1))[0]
        again = record_alerts([_alert(evidence="delta -0.6")], date(2026, 1, 1))[0]
        later = record_alerts([_alert(evidence="delta -0.7")], date(2026, 1, 5))[0]

        assert first["is_new"] and not again["is_new"] and not later["is_new"]
        assert first["id"] == again["id"] == later["id"]
        assert again["times_seen"] == 1                     # same day does not count twice
        assert later["times_seen"] == 2 and later["evidence_summary"] == "delta -0.7"
        assert (later["first_seen"], later["last_seen"]) == ("2026-01-01", "2026-01-05")

    def test_status_survives_rescans_and_resets_after_a_gap(self, db):
        from modules.alert_history import record_alerts, set_status

        row = record_alerts([_alert()], date(2026, 1, 1))[0]
        set_status(row["id"], "dismissed")
        assert record_alerts([_alert()], date(2026, 1, 6))[0]["status"] == "dismissed"

        # Gone for more than a week, then back: a new episode, a new alert.
        back = record_alerts([_alert()], date(2026, 1, 20))[0]
        assert back["is_new"] and back["status"] == "new" and back["id"] != row["id"]

    def test_dedupe_key_separates_distinct_events(self, db):
        from modules.alert_history import record_alerts

        rows = record_alerts([
            _alert("negative_news", key="2026-01-01|Outage"),
            _alert("negative_news", key="2026-01-03|Lawsuit"),
        ], date(2026, 1, 3))
        assert rows[0]["id"] != rows[1]["id"] and all(r["is_new"] for r in rows)

    def test_counts_mark_all_seen_and_errors(self, db):
        from modules.alert_history import (
            UnknownAlertError, mark_all_seen, record_alerts, set_status, status_counts,
        )

        record_alerts([_alert(), _alert("review_spike")], date(2026, 1, 1))
        assert status_counts() == {"new": 2, "seen": 0, "dismissed": 0}
        assert mark_all_seen() == 2
        assert status_counts()["seen"] == 2
        with pytest.raises(ValueError):
            set_status(1, "archived")
        with pytest.raises(UnknownAlertError):
            set_status(999, "seen")

    def test_demo_alerts_are_flagged_synthetic(self, db, monkeypatch, tmp_path):
        from database import db as dbmod
        from modules.alert_history import record_alerts

        # DEMO_MODE would switch to rivalsense_demo.db; keep the isolated file.
        monkeypatch.setattr(dbmod, "_db_path", lambda: tmp_path / "isolated.db")
        monkeypatch.setenv("DEMO_MODE", "true")
        assert record_alerts([_alert()], date(2026, 1, 1))[0]["is_synthetic"] is True


class TestSchedulerNotifications:
    def _run(self, monkeypatch, alerts, webhook):
        from scheduler import jobs
        import modules.trigger_alerts as ta

        sent = []
        monkeypatch.setattr(ta, "check_triggers", lambda names: list(alerts))
        monkeypatch.setattr(ta, "send_slack_alert", lambda a: sent.append(a.trigger_type))
        if webhook:
            monkeypatch.setenv("SLACK_WEBHOOK_URL", "https://hooks.example/x")
        else:
            monkeypatch.delenv("SLACK_WEBHOOK_URL", raising=False)
        jobs.job_check_alerts()
        return sent

    def test_each_alert_reaches_slack_once(self, db, monkeypatch):
        alerts = [_alert(), _alert("pricing_change", "HubSpot", key="url|2026-01-01")]
        assert sorted(self._run(monkeypatch, alerts, webhook=True)) == ["pricing_change", "sentiment_drop"]
        assert self._run(monkeypatch, alerts, webhook=True) == []          # next day: nothing new

    def test_without_webhook_nothing_is_marked_sent(self, db, monkeypatch):
        alerts = [_alert()]
        assert self._run(monkeypatch, alerts, webhook=False) == []
        # Slack configured later: the pending alert is delivered then.
        assert self._run(monkeypatch, alerts, webhook=True) == ["sentiment_drop"]


# ── Prospect pipeline ─────────────────────────────────────────────────────────

_LEAD = {
    "username": "u1", "post_url": "https://reddit.com/r/CRM/comments/1", "created_at": "2026-01-01",
    "competitor_name": "HubSpot", "urgency_score": 0.8, "complaint_summary": "too pricey",
    "company_signals": ["Acme"], "suggested_angle": "flat pricing", "is_synthetic": False,
}


class TestProspectPipeline:
    def test_rescans_keep_stage_and_note(self, db):
        from modules.prospect_pipeline import set_stage, upsert_leads

        assert upsert_leads([_LEAD])[0]["status"] == "new"
        set_stage(_LEAD["post_url"], "contacted", "Emailed Monday")
        again = upsert_leads([{**_LEAD, "urgency_score": 0.9}])[0]
        assert (again["status"], again["note"], again["urgency_score"]) == ("contacted", "Emailed Monday", 0.9)

    def test_pipeline_counts_and_dismissed(self, db):
        from modules.prospect_pipeline import get_pipeline, set_stage, upsert_leads

        upsert_leads([_LEAD, {**_LEAD, "username": "u2", "post_url": "https://reddit.com/x/2"}])
        set_stage("https://reddit.com/x/2", "dismissed")
        pipe = get_pipeline()
        assert {s["id"]: s["count"] for s in pipe["stages"]}["dismissed"] == 1
        assert [lead["username"] for lead in pipe["leads"]] == ["u1"]
        assert len(get_pipeline(include_dismissed=True)["leads"]) == 2
        assert pipe["leads"][0]["note"] is None                 # NULL stays None, never NaN

    def test_stage_validation(self, db):
        from modules.prospect_pipeline import UnknownLeadError, set_stage

        with pytest.raises(ValueError):
            set_stage("x", "won")
        with pytest.raises(UnknownLeadError):
            set_stage("https://nowhere", "contacted")


# ── What changed ──────────────────────────────────────────────────────────────


def _reviews(rows):
    from contextlib import closing

    from database.db import get_conn

    with closing(get_conn()) as conn, conn:
        conn.executemany(
            """INSERT INTO processed_reviews (review_id, source, competitor_name, review_text, rating, date,
                   topic_cluster, topic_label, sentiment_score, is_synthetic)
               VALUES (?, 'g2', 'HubSpot', 'text', ?, ?, 1, ?, ?, 0)""",
            [(i, *r) for i, r in enumerate(rows)],
        )


class TestChanges:
    def test_review_windows_and_topics(self, db):
        from modules.change_tracker import review_changes

        _reviews([
            (4.0, "2026-01-03", "Support", 0.5), (4.0, "2026-01-04", "Pricing", 0.4),
            (1.0, "2026-01-10", "Pricing", -0.6), (1.0, "2026-01-12", "Pricing", -0.7),
            (2.0, "2026-01-13", "Contact limits", -0.5), (2.0, "2026-01-14", "Contact limits", -0.4),
        ])
        r = review_changes("HubSpot", days=7)
        assert r["anchor_date"] == "2026-01-14"
        assert r["current"]["reviews"] == 4 and r["previous"]["reviews"] == 2
        assert r["current"]["sentiment"] < 0 < r["previous"]["sentiment"]
        assert [t["topic"] for t in r["topics"]["new"]] == ["Contact limits"]
        assert [t["topic"] for t in r["topics"]["rising"]] == ["Pricing"]
        assert [t["topic"] for t in r["topics"]["fading"]] == ["Support"]

    def test_battlecard_versions_are_diffed(self, db, tmp_path, monkeypatch):
        import modules.battlecard_generator as bg
        from modules.change_tracker import battlecard_changes

        monkeypatch.setattr(bg, "_BATTLECARD_DIR", tmp_path)
        old = {"recommended_pitch": "Lead with price.", "objections": [{"objection": "Too risky"}],
               "feature_gaps": [{"gap": "SSO"}]}
        new = {"recommended_pitch": "Lead with support.", "objections": [{"objection": "too  RISKY"}, {"objection": "Lock-in"}],
               "feature_gaps": [{"gap": "Audit log"}]}
        (tmp_path / "hubspot_20251220.json").write_text(json.dumps(old), encoding="utf-8")
        (tmp_path / "hubspot_20251227.json").write_text(json.dumps(new), encoding="utf-8")
        (tmp_path / "hubspot_latest.json").write_text(json.dumps(new), encoding="utf-8")   # not a version

        diff = battlecard_changes("HubSpot")
        assert (diff["current_date"], diff["previous_date"], diff["versions"]) == ("2025-12-27", "2025-12-20", 2)
        assert diff["pitch_changed"] and diff["pitch_before"] == "Lead with price."
        assert diff["objections_added"] == ["Lock-in"] and diff["objections_removed"] == []   # whitespace/case-insensitive
        assert diff["gaps_added"] == ["Audit log"] and diff["gaps_removed"] == ["SSO"]

    def test_digest_diff_and_endpoint(self, db, monkeypatch, tmp_path):
        import modules.battlecard_generator as bg
        from fastapi.testclient import TestClient

        from backend.main import app
        from ingestion.history_fixtures import seed_digests

        monkeypatch.setattr(bg, "_BATTLECARD_DIR", tmp_path)       # no battlecards at all
        seed_digests()
        body = TestClient(app).get("/api/changes", params={"competitor": "HubSpot", "days": 7}).json()

        assert body["digest"]["before"]["top_pain"] == "Contact-tier pricing"
        assert body["digest"]["after"]["top_pain"] == "Price increase on Sales Hub"
        assert body["battlecard"] is None
        assert any("Digest top pain moved" in h for h in body["highlights"])


# ── Compare + APIs ────────────────────────────────────────────────────────────


class TestApis:
    def test_compare_lists_every_competitor(self, db):
        from fastapi.testclient import TestClient

        from backend.main import app
        from config import COMPETITOR_NAMES

        _reviews([(3.0, "2026-01-10", "Pricing", -0.2), (4.0, "2026-01-12", "Pricing", 0.1)])
        body = TestClient(app).get("/api/compare").json()
        assert [c["name"] for c in body["competitors"]] == COMPETITOR_NAMES
        hubspot = body["competitors"][1]
        assert hubspot["reviews_30d"] == 2 and hubspot["pain_points"][0]["topic"] == "Pricing"
        assert body["competitors"][0]["sentiment_30d"] is None          # no data → null, not NaN

    def test_alert_and_stage_endpoints(self, db, monkeypatch):
        from fastapi.testclient import TestClient

        import backend.routers.alerts as alerts_router
        from backend.main import app

        monkeypatch.setattr(alerts_router, "check_triggers", lambda names: [_alert()])
        client = TestClient(app)

        found = client.post("/api/alerts/scan").json()
        assert found[0]["is_new"] and found[0]["status"] == "new"
        assert client.post("/api/alerts/scan").json()[0]["is_new"] is False
        assert client.post(f"/api/alerts/{found[0]['id']}/status", json={"status": "seen"}).json()["status"] == "seen"
        assert client.post("/api/alerts/999/status", json={"status": "seen"}).status_code == 404
        assert client.post("/api/alerts/1/status", json={"status": "archived"}).status_code == 422
        assert client.get("/api/alerts/history").json()["counts"] == {"new": 0, "seen": 1, "dismissed": 0}

        leads = client.get("/api/prospects/demo").json()
        assert all(lead["status"] == "new" for lead in leads)
        moved = client.post("/api/prospects/stage", json={"post_url": leads[0]["post_url"], "status": "replied"})
        assert moved.json()["status"] == "replied"
        assert client.post("/api/prospects/stage", json={"post_url": "https://x", "status": "replied"}).status_code == 404
        assert client.get("/api/prospects/pipeline").json()["stages"][2] == {"id": "replied", "label": "Replied", "count": 1}

    def test_old_digest_tables_are_migrated(self, tmp_path, monkeypatch):
        import sqlite3

        from database.db import init_schema

        path = tmp_path / "old.db"
        with sqlite3.connect(path) as conn:
            conn.execute("CREATE TABLE digests (id INTEGER PRIMARY KEY, generated_at TEXT, report_json TEXT)")
        monkeypatch.setenv("DATABASE_URL", str(path))
        init_schema()
        with sqlite3.connect(path) as conn:
            assert "is_synthetic" in {r[1] for r in conn.execute("PRAGMA table_info(digests)")}
