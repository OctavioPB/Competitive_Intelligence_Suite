# RivalSense — Competitive Intelligence Suite

> Six intelligence modules. Public data. Actionable signals for your sales team.

RivalSense is a Competitive Intelligence Suite that scrapes public reviews, social media, and news; processes them through a shared NLP pipeline; and surfaces six distinct intelligence outputs — ranked pain points, sentiment timelines, feature gap analysis, AI-generated battlecards, vulnerability alerts, and switching-intent prospect leads.

All-in-one competitive intelligence tool that turns messy public data into a clear edge for your business. By tracking what customers and the news are saying about competitors in real-time, the platform identifies exactly where other companies are failing and where you can win. It provides practical tools—like ready-to-use battlecards for sales teams and lists of unhappy customers ready to switch—allowing you to act on market gaps before the competition even realizes they exist. Investing in this suite means moving from guessing what the market wants to having a data-backed roadmap for capturing more market share.

---

## Modules

| # | Module | What it does |
|---|--------|-------------|
| M01 | **Pain Point Radar** | Clusters competitor reviews by topic (BERTopic), ranks by severity and trend direction |
| M02 | **Sentiment Timeline** | 18-month sentiment curve per competitor with NewsAPI event overlay |
| M03 | **Feature Wish Miner** | Extracts feature requests from reviews, clusters semantically, flags gaps your product already covers |
| M04 | **Battlecard Generator** | Claude-powered objection handler + pitch per competitor, exported as JSON/Markdown/HTML |
| M05 | **Trigger Alerts** | Detects sentiment drops, negative news, and review spikes; drafts outreach with one click |
| M06 | **Hot Prospect Finder** | Scans Reddit for switching-intent posts, scores urgency, enriches leads with company signals |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│  LAYER 1 — INGESTION                                            │
│  G2 · Trustpilot · Reddit (PRAW) · NewsAPI                     │
│  ingestion/run_ingestion.py  →  SQLite: reviews                 │
└──────────────────────────┬──────────────────────────────────────┘
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│  LAYER 2 — NLP PIPELINE                                         │
│  BERTopic · VADER + sentence-transformers · spaCy NER           │
│  pipeline/run_pipeline.py  →  SQLite: processed_reviews         │
└──────────────────────────┬──────────────────────────────────────┘
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│  LAYER 3 — INTELLIGENCE MODULES                                 │
│  modules/{pain_point_radar,sentiment_timeline,…}.py             │
│  All read processed_reviews; M04 and M05 call Claude API        │
└──────────────────────────┬──────────────────────────────────────┘
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│  LAYER 4 — OUTPUTS                                              │
│  Streamlit dashboard · Slack webhooks · SendGrid email          │
│  CSV/JSON CRM export · HTML/PDF battlecards                     │
└─────────────────────────────────────────────────────────────────┘
```

---

## Quick Start

### Demo mode (no API keys needed, ~10 seconds)

```bash
git clone https://github.com/your-org/rivalsense.git
cd rivalsense

python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS / Linux

pip install -r requirements.txt
python -m spacy download en_core_web_sm

# Generate the pre-seeded demo database
python scripts/seed_demo_db.py

# Launch
set DEMO_MODE=true              # Windows
# export DEMO_MODE=true         # macOS / Linux
streamlit run main.py
```

### Live mode (requires API keys)

```bash
cp .env.example .env
# Fill in ANTHROPIC_API_KEY, NEWSAPI_KEY, REDDIT_CLIENT_ID/SECRET, SLACK_WEBHOOK_URL

python ingestion/run_ingestion.py   # ~30–60 min first run
python pipeline/run_pipeline.py

set DEMO_MODE=false
streamlit run main.py
```

---

## Environment Variables

Copy `.env.example` to `.env` and populate:

```bash
# LLM — required for M04 (battlecards) and M05 (LLM outreach drafts)
ANTHROPIC_API_KEY=sk-ant-...

# Data sources
NEWSAPI_KEY=...
REDDIT_CLIENT_ID=...
REDDIT_CLIENT_SECRET=...
REDDIT_USER_AGENT=rivalsense/1.0

# Alerts
SLACK_WEBHOOK_URL=https://hooks.slack.com/...

# Optional
SENDGRID_API_KEY=...     # weekly email digest
DATABASE_URL=rivalsense.db

# Toggle demo mode (uses rivalsense_demo.db, skips APScheduler)
DEMO_MODE=false
```

---

## Project Structure

```
rivalsense/
├── main.py                    # Streamlit entry point and navigation
├── config.py                  # COMPETITORS list — add new competitors here
├── BRAND.md                   # Design system — read before touching any UI
│
├── ingestion/
│   ├── run_ingestion.py       # CLI orchestrator (--use-fixtures for synthetic data)
│   ├── fixtures.py            # Deterministic synthetic review generator
│   ├── scraper_g2.py
│   ├── scraper_trustpilot.py
│   ├── scraper_reddit.py
│   └── scraper_newsapi.py
│
├── pipeline/
│   ├── run_pipeline.py        # CLI orchestrator
│   ├── topic_model.py         # BERTopic training + inference
│   ├── sentiment.py           # VADER + sentence-transformer blend
│   └── entity_extractor.py   # spaCy NER
│
├── modules/
│   ├── pain_point_radar.py    # M01
│   ├── sentiment_timeline.py  # M02
│   ├── feature_wish_miner.py  # M03
│   ├── battlecard_generator.py# M04 — Claude API
│   ├── trigger_alerts.py      # M05 — Claude API (optional)
│   └── hot_prospect_finder.py # M06 — PRAW
│
├── ui/
│   ├── pages/                 # One file per module page
│   └── components/            # competitor_selector, charts
│
├── outputs/
│   ├── crm_export.py          # CSV + JSON with CRM-canonical columns
│   ├── pdf_export.py          # weasyprint (HTML fallback on Windows)
│   ├── slack_webhook.py       # Block Kit payload helper
│   └── email_digest.py        # SendGrid weekly digest
│
├── scheduler/
│   └── jobs.py                # APScheduler daily scrape + alert jobs
│
├── scripts/
│   └── seed_demo_db.py        # Generates rivalsense_demo.db
│
├── database/
│   ├── schema.sql
│   └── db.py                  # SQLite helpers (query_df, execute, executemany)
│
└── tests/
    ├── test_pipeline.py        # 39 tests
    └── test_modules.py         # 20 tests (all 6 modules)
```

---

## Engineering Decisions

### 1. SQLite over PostgreSQL for the prototype

SQLite ships with Python, requires zero infra, and the `DATABASE_URL` variable allows a one-line migration to Postgres when needed. `db.py` wraps every query in `query_df()` (returns a DataFrame) and `executemany()` so the caller never touches a connection object. The demo DB is a frozen SQLite file committed to the repo — stakeholders can run the prototype with no server.

### 2. MAX(date) anchor for all time-windowed SQL

Every query with a relative window (`'-7 days'`, `'-30 days'`) anchors on `MAX(date)` from the dataset rather than `datetime.now()`:

```sql
date >= date(
    (SELECT MAX(date) FROM processed_reviews WHERE competitor_name = ?),
    '-7 days')
```

This means fixture data with dates ending in 2025-12 always produces meaningful signals regardless of when the query runs. Using `date('now', ...)` would return empty results the moment the fixture data ages past the window.

### 3. Two-mode database: DEMO_MODE vs DATABASE_URL

`database/db.py` reads `DEMO_MODE` at call time (not import time). When `DEMO_MODE=true` it returns `rivalsense_demo.db`; otherwise it uses `DATABASE_URL`. This means the seeder script (`seed_demo_db.py`) can target the demo DB by setting `DATABASE_URL=rivalsense_demo.db` before importing any project module — no monkey-patching required.

### 4. Lazy imports to avoid circular dependencies and selective loading

Module-level imports of heavy dependencies (PRAW, sentence-transformers, pain_point_radar) would create circular chains and load ~2 GB of model weights on every page load. Functions that need them import inside their body:

```python
def enrich_lead(lead: dict) -> dict:
    from modules.pain_point_radar import get_pain_points  # lazy
    ...
```

The same pattern applies to `send_slack_alert()` (imports `post_message` lazily). This has one testing implication: the correct `@patch` target is the **source** module (`outputs.slack_webhook.post_message`), not the calling module.

### 5. Module-level lazy model cache for sentence-transformers

Each Streamlit page rerun re-executes the module file from the top. Without a cache, `SentenceTransformer("all-MiniLM-L6-v2")` would reload 90 MB of weights on every user interaction. A module-level singleton solves this:

```python
_model: Any = None

def _get_model() -> Any:
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model
```

### 6. Claude API used only for generation, never for retrieval

The LLM is called in two places: `battlecard_generator.py` (M04, ~$0.02/call) and `trigger_alerts.py` (M05 outreach drafts, ~$0.005/call). Every other intelligence function — topic clustering, sentiment scoring, entity extraction, urgency scoring — runs entirely local. This keeps the marginal cost of a demo under $0.10 and makes the app functional with `ANTHROPIC_API_KEY` absent.

All LLM calls are wrapped with `@retry_with_backoff` (exponential backoff, 3 retries) from `utils/llm.py`.

### 7. JSON-first battlecard schema

`generate_battlecard()` instructs Claude to return a strict JSON object, then renders it to Markdown separately. Raw-Markdown responses from LLMs are brittle to parse (variable heading depth, inconsistent bullet styles). JSON failures trigger a second "repair" call with `_REPAIR_SYSTEM_PROMPT` before raising. The schema is documented as `BATTLECARD_SCHEMA` in the module for reference.

### 8. Stub battlecards for demo — no API cost at seeding time

`seed_demo_db.py` writes pre-built `_STUB_BATTLECARDS` JSON objects to `outputs/battlecards/`. They are loaded by `load_cached_battlecard()` identically to Claude-generated cards. Regenerating live costs ~$0.06 for all three competitors; stubs cost zero and are reproducible.

### 9. Sentiment drop alert uses a rolling-baseline design

The `sentiment_delta` column in `processed_reviews` stores each review's score minus its 30-day rolling predecessor average (computed by `compute_sentiment_delta()` in the pipeline). The trigger alert then reads `AVG(sentiment_delta)` for the last 7 days:

- Threshold: `avg_delta < -0.5`
- To make the demo DB fire this alert, `seed_demo_db.py` inserts 15 strongly positive reviews 30–40 days before the bad week to create a high baseline. The 15 bad-week reviews score around -0.6, producing deltas around -0.55 on average.

### 10. BERTopic minimum data requirement

BERTopic requires at least 100 documents to produce coherent clusters. Below that, `train_topics()` logs a warning and all reviews receive `topic_label='insufficient_data'`. The fixture generator produces ~126 reviews per competitor (8 topics × 3 seeds × 5 elaborations + 6 news articles) to stay above this threshold.

### 11. weasyprint optional — HTML fallback on Windows

`weasyprint` requires the GTK+ runtime binaries on Windows. `pdf_export.py` detects availability at import time and falls back to HTML bytes when absent. The download button in M04's UI adapts its label and MIME type automatically. No runtime crash, no conditional logic in the UI layer.

### 12. APScheduler guarded by session_state

`start_scheduler()` in `scheduler/jobs.py` checks `st.session_state["_scheduler_started"]` before creating the `BackgroundScheduler`. Streamlit reruns the entire script on every user interaction; without this guard, each rerun would spawn a new scheduler thread and register duplicate jobs. The scheduler is also disabled entirely when `DEMO_MODE=true`.

---

## Adding a Competitor

1. Add a dict to `COMPETITORS` in `config.py` (all four fields required)
2. `python ingestion/run_ingestion.py --competitor "Name" --use-fixtures` to seed data
3. `python pipeline/run_pipeline.py --competitor "Name"` to process it
4. Regenerate battlecards if needed

---

## Running Tests

```bash
pytest tests/ -v
# 59 tests, ~15 seconds
```

Tests use fixture-based mock data throughout. No real API calls are made. Patch targets for lazy imports use the source module path (e.g. `outputs.slack_webhook.post_message`), not the calling module path.

---

## Known Limitations

| Limitation | Detail |
|------------|--------|
| **Scraping rate limits** | G2 and Trustpilot throttle at <1 req/s. Use `--use-fixtures` for offline development. |
| **BERTopic minimum** | Topic labels show as `insufficient_data` below 100 reviews per competitor. |
| **Reddit API** | Free tier: 100 req/min, 1,000 posts/query. Sufficient for prototype, not for production monitoring. |
| **SQLite concurrency** | Single writer. Migrate to PostgreSQL via `DATABASE_URL` for multi-user production. |
| **No authentication** | Streamlit prototype is unauthenticated. Add `streamlit-authenticator` before any public exposure. |
| **weasyprint on Windows** | PDF export falls back to HTML without GTK+ binaries. True PDF works on Linux/macOS. |

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Language | Python 3.11+ |
| NLP | `sentence-transformers` (all-MiniLM-L6-v2), `BERTopic`, `spaCy` (en_core_web_sm), `vaderSentiment` |
| LLM | Anthropic Claude API (`claude-sonnet-4-6`) |
| Database | SQLite → PostgreSQL (via `DATABASE_URL`) |
| Dashboard | Streamlit |
| Scraping | PRAW (Reddit), requests + BeautifulSoup (G2/Trustpilot), newsapi-python |
| Scheduling | APScheduler |
| Alerts | Slack Webhooks, SendGrid |
| Export | pandas, weasyprint (PDF/HTML battlecards) |
| Testing | pytest, unittest.mock |

---

*RivalSense v0.1.0-prototype · OPB AI Mastery Lab*
