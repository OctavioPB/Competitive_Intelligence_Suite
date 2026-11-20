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
    is_synthetic    INTEGER NOT NULL DEFAULT 0,     -- 1 = fixture / sample data, not scraped
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
    is_synthetic    INTEGER NOT NULL DEFAULT 0,     -- copied from reviews.is_synthetic
    created_at      TEXT    DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_reviews_competitor    ON reviews(competitor_name);
CREATE INDEX IF NOT EXISTS idx_reviews_source        ON reviews(source);
CREATE INDEX IF NOT EXISTS idx_processed_competitor  ON processed_reviews(competitor_name);
CREATE INDEX IF NOT EXISTS idx_processed_topic       ON processed_reviews(topic_label);
CREATE INDEX IF NOT EXISTS idx_processed_date        ON processed_reviews(date);
CREATE INDEX IF NOT EXISTS idx_processed_sentiment   ON processed_reviews(sentiment_score);
-- Every module filters by competitor plus a date window — serve that from one index.
CREATE INDEX IF NOT EXISTS idx_processed_comp_date   ON processed_reviews(competitor_name, date);

CREATE TABLE IF NOT EXISTS digests (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    generated_at  TEXT    NOT NULL,
    report_json   TEXT    NOT NULL,
    is_synthetic  INTEGER NOT NULL DEFAULT 0
);

-- Every alert ever detected. A detection that matches an alert seen in the last
-- 7 days updates that row instead of creating a new one, so a signal that lasts
-- a week is one alert (and one Slack message), not seven.
CREATE TABLE IF NOT EXISTS alert_history (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    competitor_name  TEXT    NOT NULL,
    trigger_type     TEXT    NOT NULL,
    dedupe_key       TEXT    NOT NULL DEFAULT '',   -- e.g. headline or price-change date
    evidence_summary TEXT    NOT NULL,              -- latest evidence text
    first_seen       TEXT    NOT NULL,              -- ISO date of first detection
    last_seen        TEXT    NOT NULL,              -- ISO date of latest detection
    times_seen       INTEGER NOT NULL DEFAULT 1,
    status           TEXT    NOT NULL DEFAULT 'new', -- new | seen | dismissed
    status_changed_at TEXT,
    outreach_draft   TEXT,
    notified_at      TEXT,                          -- when it was sent to Slack
    is_synthetic     INTEGER NOT NULL DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_alerts_lookup ON alert_history(competitor_name, trigger_type, dedupe_key, last_seen);
CREATE INDEX IF NOT EXISTS idx_alerts_status ON alert_history(status, last_seen);

-- Hot Prospect leads kept across scans, with where each one stands.
CREATE TABLE IF NOT EXISTS prospect_leads (
    post_url          TEXT    PRIMARY KEY,
    username          TEXT    NOT NULL,
    competitor_name   TEXT,
    created_at        TEXT,                         -- when the Reddit post was written
    urgency_score     REAL    NOT NULL DEFAULT 0,
    complaint_summary TEXT,
    company_signals   TEXT,                         -- JSON list
    suggested_angle   TEXT,
    status            TEXT    NOT NULL DEFAULT 'new', -- new | contacted | replied | opportunity | dismissed
    note              TEXT,
    first_seen        TEXT    NOT NULL,
    last_seen         TEXT    NOT NULL,
    status_changed_at TEXT,
    is_synthetic      INTEGER NOT NULL DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_leads_status ON prospect_leads(status, urgency_score);

CREATE INDEX IF NOT EXISTS idx_digests_generated ON digests(generated_at);

-- ── Market signals ─────────────────────────────────────────────────────────────

-- One row per distinct version of a competitor pricing page. A new row is only
-- written when the extracted price points change; otherwise last_seen moves.
CREATE TABLE IF NOT EXISTS pricing_snapshots (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    competitor_name TEXT    NOT NULL,
    url             TEXT    NOT NULL,
    first_seen      TEXT    NOT NULL,               -- ISO 8601 date this version appeared
    last_seen       TEXT    NOT NULL,               -- ISO 8601 date of the latest check
    content_hash    TEXT    NOT NULL,               -- sha256 of the sorted price points
    price_points    TEXT    NOT NULL,               -- JSON: ["Starter $7 /mo/seat", ...]
    added           TEXT,                           -- JSON diff vs previous version; NULL for the first
    removed         TEXT,
    is_synthetic    INTEGER NOT NULL DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_pricing_comp_url ON pricing_snapshots(competitor_name, url, last_seen);

-- Competitor job postings from public ATS feeds (Greenhouse, Lever, Ashby, Workday).
CREATE TABLE IF NOT EXISTS job_postings (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    competitor_name TEXT    NOT NULL,
    source          TEXT    NOT NULL,               -- greenhouse | lever | ashby | workday
    external_id     TEXT    NOT NULL,
    title           TEXT    NOT NULL,
    department      TEXT,
    location        TEXT,
    url             TEXT,
    category        TEXT    NOT NULL,               -- support | engineering | sales | ... (see market_signals)
    integration     INTEGER NOT NULL DEFAULT 0,     -- 1 = engineering role about integrations / APIs
    posted_date     TEXT,                           -- ISO 8601 date the board says it was posted
    first_seen      TEXT    NOT NULL,
    last_seen       TEXT    NOT NULL,               -- equals the latest crawl date while the role is open
    is_synthetic    INTEGER NOT NULL DEFAULT 0,
    UNIQUE (competitor_name, source, external_id)
);

CREATE INDEX IF NOT EXISTS idx_jobs_comp_seen ON job_postings(competitor_name, last_seen);

-- ── Platform ───────────────────────────────────────────────────────────────────

-- Competitors and own features, editable from the UI. Seeded from config.py the
-- first time the table is empty (modules/settings_store.py).
CREATE TABLE IF NOT EXISTS competitors (
    name        TEXT    PRIMARY KEY,
    config_json TEXT    NOT NULL,                   -- CompetitorConfig without "name"
    position    INTEGER NOT NULL DEFAULT 0,
    updated_at  TEXT
);

CREATE TABLE IF NOT EXISTS own_features (
    feature  TEXT    PRIMARY KEY,
    position INTEGER NOT NULL DEFAULT 0
);

-- Accounts. Passwords are scrypt hashes; sessions store only a hash of the token.
CREATE TABLE IF NOT EXISTS users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    email         TEXT    NOT NULL UNIQUE COLLATE NOCASE,
    name          TEXT    NOT NULL,
    password_hash TEXT    NOT NULL,
    role          TEXT    NOT NULL DEFAULT 'member', -- admin | member
    created_at    TEXT    NOT NULL,
    last_login    TEXT
);

CREATE TABLE IF NOT EXISTS sessions (
    token_hash TEXT    PRIMARY KEY,
    user_id    INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at TEXT    NOT NULL,
    expires_at TEXT    NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions(user_id);

-- Win/loss: why each deal against a competitor was won or lost.
CREATE TABLE IF NOT EXISTS deals (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    competitor_name TEXT    NOT NULL,
    outcome         TEXT    NOT NULL,               -- won | lost
    reason_category TEXT    NOT NULL,               -- pricing | features | support | ux | reliability | integrations | other
    reason_text     TEXT,
    deal_name       TEXT,
    amount          REAL,
    closed_on       TEXT    NOT NULL,               -- ISO date
    created_by      TEXT,
    created_at      TEXT    NOT NULL,
    is_synthetic    INTEGER NOT NULL DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_deals_comp ON deals(competitor_name, closed_on);

-- Sentence-transformer vectors of processed reviews for "Ask RivalSense".
CREATE TABLE IF NOT EXISTS review_embeddings (
    review_id INTEGER PRIMARY KEY,                  -- reviews.id (= processed_reviews.review_id)
    model     TEXT    NOT NULL,
    vector    BLOB    NOT NULL                      -- float32, L2-normalised
);
