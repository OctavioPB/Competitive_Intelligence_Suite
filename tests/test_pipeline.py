"""Pipeline tests — Sprint 0 smoke test: schema creation."""

import sqlite3
from pathlib import Path

SCHEMA_PATH = Path(__file__).parent.parent / "database" / "schema.sql"


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
