-- RivalSense database schema
-- Run: sqlite3 rivalsense.db < database/schema.sql
-- Safe to re-run — all statements use IF NOT EXISTS.

CREATE TABLE IF NOT EXISTS reviews (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    source          TEXT    NOT NULL,               -- g2 | trustpilot | reddit | newsapi
    competitor_name TEXT    NOT NULL,
    review_text     TEXT    NOT NULL,
    rating          REAL,                           -- NULL for news/reddit sources
    date            TEXT,                           -- ISO 8601 (YYYY-MM-DD)
    author_id       TEXT,
    helpful_count   INTEGER DEFAULT 0,
    created_at      TEXT    DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS processed_reviews (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    review_id       INTEGER UNIQUE REFERENCES reviews(id),
    source          TEXT    NOT NULL,
    competitor_name TEXT    NOT NULL,
    review_text     TEXT    NOT NULL,
    rating          REAL,
    date            TEXT,
    topic_cluster   INTEGER,                        -- BERTopic cluster id; -1 = outlier
    topic_label     TEXT,                           -- human-readable topic string
    sentiment_score REAL,                           -- float in [-1.0, 1.0]
    sentiment_delta REAL,                           -- change vs prior 30-day avg
    entities        TEXT,                           -- JSON: [{text, label}, ...]
    wish_phrases    TEXT,                           -- JSON: ["I wish ...", ...]
    created_at      TEXT    DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_reviews_competitor    ON reviews(competitor_name);
CREATE INDEX IF NOT EXISTS idx_reviews_source        ON reviews(source);
CREATE INDEX IF NOT EXISTS idx_processed_competitor  ON processed_reviews(competitor_name);
CREATE INDEX IF NOT EXISTS idx_processed_topic       ON processed_reviews(topic_label);
CREATE INDEX IF NOT EXISTS idx_processed_date        ON processed_reviews(date);
CREATE INDEX IF NOT EXISTS idx_processed_sentiment   ON processed_reviews(sentiment_score);
