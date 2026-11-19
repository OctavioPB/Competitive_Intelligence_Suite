"""Tests for data provenance, topic naming and the evidence drill-down."""

import json
import sqlite3
from unittest.mock import patch

import pytest

_OLD_SCHEMA = """
CREATE TABLE reviews (
    id INTEGER PRIMARY KEY AUTOINCREMENT, source TEXT NOT NULL,
    competitor_name TEXT NOT NULL, review_text TEXT NOT NULL, rating REAL,
    date TEXT, author_id TEXT, helpful_count INTEGER DEFAULT 0,
    created_at TEXT DEFAULT (datetime('now'))
);
CREATE TABLE processed_reviews (
    id INTEGER PRIMARY KEY AUTOINCREMENT, review_id INTEGER UNIQUE REFERENCES reviews(id),
    source TEXT NOT NULL, competitor_name TEXT NOT NULL, review_text TEXT NOT NULL,
    rating REAL, date TEXT, topic_cluster INTEGER, topic_label TEXT,
    sentiment_score REAL, sentiment_delta REAL, entities TEXT, wish_phrases TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);
"""


@pytest.fixture
def temp_db(tmp_path, monkeypatch):
    """Point database.db at an empty file for the duration of one test."""
    path = tmp_path / "test.db"
    monkeypatch.setenv("DEMO_MODE", "false")
    monkeypatch.setenv("DATABASE_URL", str(path))
    return path


def _insert_processed(path, rows):
    """rows: (competitor, cluster, label, text, sentiment, date, is_synthetic)."""
    from database.db import init_schema

    init_schema()
    conn = sqlite3.connect(path)
    for i, (comp, cluster, label, text, sent, day, syn) in enumerate(rows, 1):
        conn.execute(
            "INSERT INTO processed_reviews (review_id, source, competitor_name, review_text, "
            "date, topic_cluster, topic_label, sentiment_score, sentiment_delta, entities, "
            "wish_phrases, is_synthetic) VALUES (?, 'g2', ?, ?, ?, ?, ?, ?, 0, '[]', '[]', ?)",
            (i, comp, text, day, cluster, label, sent, syn),
        )
    conn.commit()
    conn.close()


# ── Synthetic-data flag ───────────────────────────────────────────────────────


class TestSyntheticFlag:
    def test_migration_adds_column_and_backfills_fixture_rows(self, temp_db) -> None:
        """A database from before is_synthetic gains the column; fixture rows are flagged."""
        conn = sqlite3.connect(temp_db)
        conn.executescript(_OLD_SCHEMA)
        conn.executemany(
            "INSERT INTO reviews (id, source, competitor_name, review_text, date, author_id) "
            "VALUES (?, 'g2', 'Salesforce', 'text', '2025-01-01', ?)",
            [(1, "fixture_user_0001"), (2, "real_reddit_user"), (3, "badweek_sf_001")],
        )
        conn.executemany(
            "INSERT INTO processed_reviews (review_id, source, competitor_name, review_text) "
            "VALUES (?, 'g2', 'Salesforce', 'text')",
            [(1,), (2,), (3,)],
        )
        conn.commit()
        conn.close()

        from database.db import init_schema

        init_schema()
        init_schema()  # idempotent

        conn = sqlite3.connect(temp_db)
        reviews = dict(conn.execute("SELECT id, is_synthetic FROM reviews"))
        processed = dict(conn.execute("SELECT review_id, is_synthetic FROM processed_reviews"))
        conn.close()
        assert reviews == {1: 1, 2: 0, 3: 1}
        assert processed == {1: 1, 2: 0, 3: 1}

    def test_fixture_generator_marks_every_row_synthetic(self) -> None:
        from config import COMPETITORS
        from ingestion.fixtures import generate

        assert all(r["is_synthetic"] == 1 for r in generate(COMPETITORS[0]))

    def test_ingestion_stores_flag(self, temp_db) -> None:
        from database.db import init_schema, query_df
        from ingestion.run_ingestion import _store_reviews

        init_schema()
        base = {"source": "g2", "competitor_name": "HubSpot", "date": "2025-01-01"}
        _store_reviews([
            {**base, "review_text": "sample", "is_synthetic": 1},
            {**base, "review_text": "scraped"},
        ])

        flags = dict(query_df("SELECT review_text, is_synthetic FROM reviews").values.tolist())
        assert flags == {"sample": 1, "scraped": 0}

    def test_data_status_endpoint_reports_share(self, temp_db) -> None:
        from fastapi.testclient import TestClient

        from backend.main import app

        _insert_processed(temp_db, [
            ("Salesforce", 0, "Pricing", "a", -0.5, "2025-01-01", 1),
            ("Salesforce", 0, "Pricing", "b", -0.5, "2025-01-02", 0),
        ])

        with TestClient(app) as client:
            body = client.get("/api/meta/data-status").json()

        assert body["demo_mode"] is False
        sf = next(c for c in body["competitors"] if c["name"] == "Salesforce")
        assert sf == {"name": "Salesforce", "reviews": 2, "synthetic": 1, "latest_date": "2025-01-02"}
        hs = next(c for c in body["competitors"] if c["name"] == "HubSpot")
        assert hs["reviews"] == 0


# ── Topic naming ──────────────────────────────────────────────────────────────

_TEXTS = [
    "The per seat pricing is outrageous and renewal costs keep rising",
    "Pricing went up again at renewal, licence costs are absurd",
    "Every renewal brings a pricing increase we cannot justify",
    "The mobile app crashes constantly and loses meeting notes",
    "Mobile app keeps crashing in the field, offline mode missing",
    "Our reps hate the mobile app, crashes on every submit",
    "Totally unrelated outlier text",
]
_CLUSTERS = [0, 0, 0, 1, 1, 1, -1]


class TestTopicLabeler:
    def test_keyword_fallback_drops_stop_words_and_competitor_name(self) -> None:
        from pipeline.topic_labeler import label_topics

        labels = label_topics("Salesforce", _TEXTS, _CLUSTERS, use_llm=False)

        assert set(labels) == {0, 1}, "outlier cluster -1 must not get a topic name"
        assert "pricing" in labels[0].lower() or "renewal" in labels[0].lower()
        assert "mobile" in labels[1].lower() or "crash" in labels[1].lower()
        for name in labels.values():
            words = {w.strip().lower() for w in name.split("/")}
            assert not words & {"the", "and", "is", "salesforce"}

    def test_uses_claude_names_when_available(self) -> None:
        from pipeline.topic_labeler import label_topics

        reply = json.dumps({"0": "Renewal Price Hikes", "1": "Mobile App Crashes"})
        with patch("utils.llm.call_claude", return_value=reply) as mock_claude:
            labels = label_topics("Salesforce", _TEXTS, _CLUSTERS)

        assert labels == {0: "Renewal Price Hikes", 1: "Mobile App Crashes"}
        assert mock_claude.call_count == 1, "one Claude call per competitor"

    def test_falls_back_when_claude_fails(self) -> None:
        """No API key (conftest) → keyword names, no exception."""
        from pipeline.topic_labeler import label_topics

        labels = label_topics("Salesforce", _TEXTS, _CLUSTERS)
        assert set(labels) == {0, 1} and all(labels.values())

    def test_duplicate_names_are_made_unique(self) -> None:
        from pipeline.topic_labeler import label_topics

        reply = json.dumps({"0": "Pricing", "1": "pricing"})
        with patch("utils.llm.call_claude", return_value=reply):
            labels = label_topics("Salesforce", _TEXTS, _CLUSTERS)

        assert len({v.lower() for v in labels.values()}) == 2

    def test_relabel_updates_db_and_resets_outliers(self, temp_db) -> None:
        from database.db import query_df
        from pipeline.topic_labeler import relabel_competitor

        _insert_processed(temp_db, [
            ("Salesforce", c, f"old_label_{c}", t, -0.3, "2025-01-01", 0)
            for t, c in zip(_TEXTS, _CLUSTERS)
        ])

        renamed = relabel_competitor("Salesforce", use_llm=False)

        labels = dict(query_df(
            "SELECT DISTINCT topic_cluster, topic_label FROM processed_reviews"
        ).values.tolist())
        assert renamed == 2
        assert labels[-1] == "misc"
        assert not any(str(v).startswith("old_label") for v in labels.values())


# ── Evidence drill-down ───────────────────────────────────────────────────────


class TestReviewEvidence:
    @pytest.fixture
    def seeded(self, temp_db):
        _insert_processed(temp_db, [
            ("Salesforce", 0, "Pricing", "worst pricing", -0.9, "2025-11-30", 1),
            ("Salesforce", 0, "Pricing", "bad pricing", -0.4, "2025-12-01", 0),
            ("Salesforce", 1, "Mobile", "mobile crash", -0.7, "2025-12-31", 0),
            ("Salesforce", 1, "Mobile", "mobile ok", 0.6, "2026-01-01", 0),
            ("HubSpot", 0, "Pricing", "hubspot pricing", -0.8, "2025-12-15", 0),
        ])
        return temp_db

    def test_topic_filter_sorted_worst_first(self, seeded) -> None:
        from modules.review_evidence import get_reviews

        result = get_reviews("Salesforce", topic="Pricing")

        assert result["total"] == 2
        assert [r["review_text"] for r in result["reviews"]] == ["worst pricing", "bad pricing"]
        assert result["reviews"][0]["is_synthetic"] is True

    def test_month_filter_includes_whole_month_only(self, seeded) -> None:
        from modules.review_evidence import get_reviews

        result = get_reviews("Salesforce", month="2025-12", sort="positive")

        assert {r["review_text"] for r in result["reviews"]} == {"bad pricing", "mobile crash"}

    def test_limit_keeps_total(self, seeded) -> None:
        from modules.review_evidence import get_reviews

        result = get_reviews("Salesforce", limit=1)
        assert result["total"] == 4 and len(result["reviews"]) == 1

    def test_endpoint_validates_input(self, seeded) -> None:
        from fastapi.testclient import TestClient

        from backend.main import app

        with TestClient(app) as client:
            ok = client.get("/api/reviews", params={"competitor": "Salesforce", "topic": "Mobile"})
            bad_month = client.get("/api/reviews", params={"competitor": "Salesforce", "month": "2025-13"})
            unknown = client.get("/api/reviews", params={"competitor": "Nope"})

        assert ok.status_code == 200 and ok.json()["total"] == 2
        assert bad_month.status_code == 422
        assert unknown.status_code == 404
