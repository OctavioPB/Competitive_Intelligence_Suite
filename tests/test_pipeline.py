"""Pipeline tests — Sprint 0 schema smoke tests + Sprint 1 NLP pipeline tests."""

import json
import sqlite3
from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

SCHEMA_PATH = Path(__file__).parent.parent / "database" / "schema.sql"

# ── Sprint 0 — schema smoke tests ─────────────────────────────────────────────


def test_schema_creates_without_errors() -> None:
    """schema.sql executes against an in-memory DB and creates both required tables."""
    conn = sqlite3.connect(":memory:")
    try:
        conn.executescript(SCHEMA_PATH.read_text())
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        )
        tables = {row[0] for row in cursor.fetchall()}
    finally:
        conn.close()

    assert "reviews" in tables, "reviews table not created by schema.sql"
    assert "processed_reviews" in tables, "processed_reviews table not created by schema.sql"


def test_schema_is_idempotent() -> None:
    """Running schema.sql twice does not raise — all statements use IF NOT EXISTS."""
    conn = sqlite3.connect(":memory:")
    schema_sql = SCHEMA_PATH.read_text()
    try:
        conn.executescript(schema_sql)
        conn.executescript(schema_sql)  # second run must not raise
    finally:
        conn.close()


def test_reviews_table_columns() -> None:
    """reviews table has all expected columns."""
    conn = sqlite3.connect(":memory:")
    conn.executescript(SCHEMA_PATH.read_text())
    cursor = conn.execute("PRAGMA table_info(reviews)")
    columns = {row[1] for row in cursor.fetchall()}
    conn.close()

    required = {
        "id", "source", "competitor_name", "review_text",
        "rating", "date", "author_id", "helpful_count", "created_at",
    }
    assert required.issubset(columns), f"Missing columns: {required - columns}"


def test_processed_reviews_table_columns() -> None:
    """processed_reviews table has all expected columns."""
    conn = sqlite3.connect(":memory:")
    conn.executescript(SCHEMA_PATH.read_text())
    cursor = conn.execute("PRAGMA table_info(processed_reviews)")
    columns = {row[1] for row in cursor.fetchall()}
    conn.close()

    required = {
        "id", "review_id", "source", "competitor_name", "review_text",
        "rating", "date", "topic_cluster", "topic_label",
        "sentiment_score", "sentiment_delta", "entities", "wish_phrases", "created_at",
    }
    assert required.issubset(columns), f"Missing columns: {required - columns}"


# ── Sprint 1 — NLP pipeline unit tests ────────────────────────────────────────

# Five synthetic reviews covering distinct sentiment signals
_FIXTURE_REVIEWS = [
    {
        "id": 1, "source": "g2", "competitor_name": "Salesforce",
        "review_text": "Salesforce is absolutely terrible. The pricing is outrageous and support is useless.",
        "rating": 1.0, "date": "2025-06-01",
    },
    {
        "id": 2, "source": "g2", "competitor_name": "Salesforce",
        "review_text": "Salesforce is a great product. I love the reporting and automation features.",
        "rating": 5.0, "date": "2025-07-15",
    },
    {
        "id": 3, "source": "trustpilot", "competitor_name": "Salesforce",
        "review_text": "Average CRM. Does the job but the interface is confusing. I wish they had a better mobile app.",
        "rating": 3.0, "date": "2025-08-20",
    },
    {
        "id": 4, "source": "reddit", "competitor_name": "Salesforce",
        "review_text": "Switching away from Salesforce after 3 years. Too expensive and the learning curve never ends.",
        "rating": None, "date": "2025-09-10",
    },
    {
        "id": 5, "source": "newsapi", "competitor_name": "Salesforce",
        "review_text": "Salesforce reports record revenue despite customer complaints about pricing and complexity.",
        "rating": None, "date": "2025-10-05",
    },
]


class TestSentimentScoring:
    def test_negative_review_has_negative_score(self) -> None:
        from pipeline.sentiment import score_sentiment

        result = score_sentiment(_FIXTURE_REVIEWS[0]["review_text"])
        assert result["sentiment_score"] < 0, "Clearly negative review must have negative score"

    def test_positive_review_has_positive_score(self) -> None:
        from pipeline.sentiment import score_sentiment

        result = score_sentiment(_FIXTURE_REVIEWS[1]["review_text"])
        assert result["sentiment_score"] > 0, "Clearly positive review must have positive score"

    def test_score_is_in_valid_range(self) -> None:
        from pipeline.sentiment import score_sentiment

        for review in _FIXTURE_REVIEWS:
            result = score_sentiment(review["review_text"])
            assert -1.0 <= result["sentiment_score"] <= 1.0, (
                f"Sentiment score {result['sentiment_score']} is out of [-1, 1]"
            )

    def test_result_has_required_keys(self) -> None:
        from pipeline.sentiment import score_sentiment

        result = score_sentiment("Some review text.")
        assert "sentiment_score" in result
        assert "vader_score" in result

    def test_sentiment_delta_shape_matches_input(self) -> None:
        from pipeline.sentiment import compute_sentiment_delta

        df = pd.DataFrame(
            {"date": [r["date"] for r in _FIXTURE_REVIEWS],
             "sentiment_score": [0.5, -0.3, 0.1, -0.8, 0.2]}
        )
        deltas = compute_sentiment_delta(df)
        assert len(deltas) == len(_FIXTURE_REVIEWS)
        assert deltas.dtype == float


class TestWishPhraseExtraction:
    def test_wish_phrase_detected(self) -> None:
        from pipeline.sentiment import extract_wish_phrases

        text = "I wish they had a better mobile app. Please add offline mode."
        wishes = extract_wish_phrases(text)
        assert len(wishes) >= 1, "Expected at least one wish phrase"

    def test_no_false_positives_on_plain_text(self) -> None:
        from pipeline.sentiment import extract_wish_phrases

        text = "The product is good. The UI is clean. Support is responsive."
        wishes = extract_wish_phrases(text)
        assert len(wishes) == 0, f"Expected 0 wish phrases, got: {wishes}"


class TestEntityExtraction:
    def test_extracts_named_entity(self) -> None:
        from pipeline.entity_extractor import extract_entities

        entities = extract_entities("Salesforce is the market leader in enterprise CRM.")
        # en_core_web_sm may label "Salesforce" as ORG or PRODUCT depending on context
        labels = {e["label"] for e in entities}
        assert labels & {"ORG", "PRODUCT"}, "Expected at least one ORG or PRODUCT entity"

    def test_returns_list_of_dicts(self) -> None:
        from pipeline.entity_extractor import extract_entities

        entities = extract_entities("HubSpot is used by thousands of companies in Europe.")
        assert isinstance(entities, list)
        for e in entities:
            assert "text" in e and "label" in e

    def test_deduplication(self) -> None:
        from pipeline.entity_extractor import extract_entities

        # Salesforce mentioned twice — should appear once in results
        entities = extract_entities("Salesforce is expensive. I hate Salesforce pricing.")
        sf_entities = [e for e in entities if e["text"].lower() == "salesforce"]
        assert len(sf_entities) == 1, "Duplicate entities should be deduplicated"


class TestFixtureGenerator:
    def test_fixture_returns_correct_competitor(self) -> None:
        from config import COMPETITORS
        from ingestion.fixtures import generate

        competitor = COMPETITORS[0]  # Salesforce
        reviews = generate(competitor)
        names = {r["competitor_name"] for r in reviews}
        assert names == {competitor["name"]}

    def test_fixture_has_required_fields(self) -> None:
        from config import COMPETITORS
        from ingestion.fixtures import generate

        reviews = generate(COMPETITORS[0])
        required = {"source", "competitor_name", "review_text", "rating", "date",
                    "author_id", "helpful_count"}
        for review in reviews[:5]:
            assert required.issubset(review.keys())

    def test_fixture_meets_minimum_count(self) -> None:
        from config import COMPETITORS
        from ingestion.fixtures import generate

        for competitor in COMPETITORS:
            reviews = generate(competitor)
            assert len(reviews) >= 100, (
                f"{competitor['name']} fixture has only {len(reviews)} reviews — need ≥ 100"
            )

    def test_fixture_is_deterministic(self) -> None:
        from config import COMPETITORS
        from ingestion.fixtures import generate

        competitor = COMPETITORS[0]
        run1 = [r["author_id"] for r in generate(competitor)]
        run2 = [r["author_id"] for r in generate(competitor)]
        assert run1 == run2, "Fixture generator must be deterministic (seeded random)"


class TestPipelineIntegration:
    """End-to-end pipeline test using in-memory SQLite and mocked BERTopic."""

    def _make_db(self) -> sqlite3.Connection:
        conn = sqlite3.connect(":memory:")
        conn.executescript(SCHEMA_PATH.read_text())
        for r in _FIXTURE_REVIEWS:
            conn.execute(
                "INSERT INTO reviews (id, source, competitor_name, review_text, rating, date) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (r["id"], r["source"], r["competitor_name"], r["review_text"], r["rating"], r["date"]),
            )
        conn.commit()
        return conn

    @patch("pipeline.run_pipeline.query_df")
    @patch("pipeline.run_pipeline.executemany")
    @patch("pipeline.run_pipeline.train_topics")
    @patch("pipeline.run_pipeline.assign_topics")
    def test_pipeline_writes_all_fields(
        self,
        mock_assign,
        mock_train,
        mock_executemany,
        mock_query_df,
    ) -> None:
        from config import COMPETITORS
        from pipeline.run_pipeline import run_for_competitor

        mock_query_df.return_value = pd.DataFrame(_FIXTURE_REVIEWS)
        mock_assign.return_value = [
            {"topic_cluster": 0, "topic_label": "pricing_issues"} for _ in _FIXTURE_REVIEWS
        ]

        captured_rows = []
        def capture(sql, rows):
            captured_rows.extend(rows)
        mock_executemany.side_effect = capture

        count = run_for_competitor(COMPETITORS[0])

        assert count == len(_FIXTURE_REVIEWS)
        assert len(captured_rows) == len(_FIXTURE_REVIEWS)

        # Each row must have 12 fields matching the UPSERT SQL
        for row in captured_rows:
            assert len(row) == 12, f"Expected 12 fields per row, got {len(row)}"
            review_id, source, comp, text, rating, date, tc, tl, ss, sd, ents, wishes = row
            assert isinstance(ss, float), "sentiment_score must be float"
            assert -1.0 <= ss <= 1.0, "sentiment_score must be in [-1, 1]"
            assert isinstance(json.loads(ents), list), "entities must be JSON list"
            assert isinstance(json.loads(wishes), list), "wish_phrases must be JSON list"

    @patch("pipeline.run_pipeline.query_df")
    @patch("pipeline.run_pipeline.executemany")
    @patch("pipeline.run_pipeline.train_topics")
    @patch("pipeline.run_pipeline.assign_topics")
    def test_pipeline_is_idempotent(
        self,
        mock_assign,
        mock_train,
        mock_executemany,
        mock_query_df,
    ) -> None:
        """Running the pipeline twice with the same data must not raise."""
        from config import COMPETITORS
        from pipeline.run_pipeline import run_for_competitor

        mock_query_df.return_value = pd.DataFrame(_FIXTURE_REVIEWS)
        mock_assign.return_value = [
            {"topic_cluster": 0, "topic_label": "pricing"} for _ in _FIXTURE_REVIEWS
        ]

        run_for_competitor(COMPETITORS[0])
        run_for_competitor(COMPETITORS[0])  # second run must not raise
        assert mock_executemany.call_count == 2
