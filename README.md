# RivalSense — Competitive Intelligence Suite

> Nine intelligence modules. Public data. Actionable signals for your sales team.

RivalSense is a Competitive Intelligence Suite that scrapes public reviews, social media, and news; processes them through a shared NLP pipeline; and surfaces nine distinct intelligence outputs — ranked pain points, sentiment timelines, feature gap analysis, AI-generated battlecards, vulnerability alerts, switching-intent prospect leads, churn reason analysis, executive digests, and personalised outreach generation.

---

## Modules

| # | Module | What it does |
|---|--------|-------------|
| M01 | **Pain Point Radar** | Clusters competitor reviews by topic (BERTopic), ranks by severity and trend direction |
| M02 | **Sentiment Timeline** | 18-month sentiment curve per competitor with NewsAPI event overlay |
| M03 | **Feature Wish Miner** | Extracts feature requests from reviews, clusters semantically, flags gaps your product already covers |
| M04 | **Battlecard Generator** | Claude-powered objection handler + pitch per competitor, exported as JSON/Markdown |
| M05 | **Trigger Alerts** | Detects sentiment drops, negative news, and review spikes; drafts outreach with one click |
| M06 | **Hot Prospect Finder** | Scans Reddit for switching-intent posts, scores urgency, enriches leads with company signals |
| M07 | **Churn Intelligence** | Categorises why users leave each competitor into 5 structured buckets with proof quotes |
| M08 | **Intelligence Digest** | Claude-synthesised weekly executive brief across all competitors — one page, three action bullets each |
| M09 | **Outreach Composer** | Generates personalised email, LinkedIn DM, and cold call bullets from a prospect's complaint |

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
│  M04, M07, M08, M09 call Claude API                             │
└──────────────────────────┬──────────────────────────────────────┘
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│  LAYER 4 — API + FRONTEND                                       │
│  FastAPI (backend/main.py) · React 18 + Vite (frontend/)        │
│  Slack webhooks · SendGrid email · CSV/JSON export              │
└─────────────────────────────────────────────────────────────────┘
```

---

## Quick Start

### Demo mode (no API keys needed, ~10 seconds)

```powershell
git clone https://github.com/your-org/rivalsense.git
cd rivalsense

python -m venv .venv
.venv\Scripts\activate

pip install -r requirements.txt
python -m spacy download en_core_web_sm

# Generate the pre-seeded demo database
python scripts/seed_demo_db.py

# Launch React + FastAPI stack
.\demo.ps1
```

### Live mode (requires API keys)

```powershell
cp .env.example .env
# Fill in ANTHROPIC_API_KEY, NEWSAPI_KEY, REDDIT_CLIENT_ID/SECRET, SLACK_WEBHOOK_URL

python ingestion/run_ingestion.py   # ~30–60 min first run
python pipeline/run_pipeline.py

.\demo.ps1 -Demo:$false
```

---

## Environment Variables

Copy `.env.example` to `.env` and populate:

```bash
# LLM — required for M04, M07, M08, M09
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
DIGEST_EMAIL=...         # recipient for scheduled digest
DATABASE_URL=rivalsense.db

# Toggle demo mode (uses rivalsense_demo.db, skips APScheduler)
DEMO_MODE=false
```

---

## Project Structure

```
rivalsense/
├── config.py                  # COMPETITORS list — add new competitors here
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
│   ├── pain_point_radar.py        # M01
│   ├── sentiment_timeline.py      # M02
│   ├── feature_wish_miner.py      # M03
│   ├── battlecard_generator.py    # M04 — Claude API
│   ├── trigger_alerts.py          # M05 — Claude API (optional)
│   ├── hot_prospect_finder.py     # M06 — PRAW
│   ├── churn_reason_intelligence.py # M07 — Claude API
│   ├── digest_generator.py        # M08 — Claude API
│   └── outreach_composer.py       # M09 — Claude API
│
├── backend/
│   ├── main.py                # FastAPI app + router registration
│   └── routers/               # One router per module (REST endpoints)
│
├── frontend/
│   ├── src/
│   │   ├── App.tsx            # Page routing
│   │   ├── pages/             # One page component per module
│   │   ├── components/        # Nav, Footer, KpiCard, Eyebrow, …
│   │   ├── services/api.ts    # All HTTP calls — no fetch in components
│   │   ├── stores/appStore.ts # Zustand (competitor, outreach prefill)
│   │   └── styles/tokens.css  # OPB design tokens
│   ├── index.html
│   └── vite.config.ts         # Proxies /api/* → FastAPI :8000
│
├── outputs/
│   ├── crm_export.py          # CSV + JSON with CRM-canonical columns
│   ├── slack_webhook.py       # Block Kit payload helper
│   └── email_digest.py        # SendGrid weekly digest
│
├── scheduler/
│   └── jobs.py                # APScheduler: daily scrape, alert check, weekly digest
│
├── scripts/
│   └── seed_demo_db.py        # Generates rivalsense_demo.db
│
├── database/
│   ├── schema.sql             # reviews, processed_reviews, digests tables
│   └── db.py                  # SQLite helpers (query_df, execute, executemany)
│
└── tests/
    ├── test_pipeline.py        # 39 tests
    └── test_modules.py         # 20 tests (all modules)
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

Module-level imports of heavy dependencies (PRAW, sentence-transformers, pain_point_radar) would create circular chains and load ~2 GB of model weights on cold start. Functions that need them import inside their body:

```python
def enrich_lead(lead: dict) -> dict:
    from modules.pain_point_radar import get_pain_points  # lazy
    ...
```

### 5. Module-level lazy model cache for sentence-transformers

Without a cache, `SentenceTransformer("all-MiniLM-L6-v2")` would reload 90 MB of weights on every call. A module-level singleton solves this:

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

The LLM is called in five places: M04 (battlecards), M05 (outreach drafts), M07 (churn categorisation), M08 (digest synthesis), M09 (outreach composition). Every other intelligence function — topic clustering, sentiment scoring, entity extraction, urgency scoring — runs entirely local. This keeps the marginal cost of a demo under $0.20 and makes the app functional with `ANTHROPIC_API_KEY` absent for the analytical modules.

All LLM calls are wrapped with `@retry_with_backoff` (exponential backoff, 3 retries) from `utils/llm.py`.

### 7. JSON-first LLM schema

All Claude calls instruct the model to return a strict JSON object, then each module renders it separately. Raw-Markdown responses from LLMs are brittle to parse. JSON failures trigger a second "repair" call with a `_REPAIR_SYSTEM_PROMPT` before raising. Schemas are documented as constants in each module for reference.

### 8. Stub battlecards for demo — no API cost at seeding time

`seed_demo_db.py` writes pre-built `_STUB_BATTLECARDS` JSON objects to `outputs/battlecards/`. They are loaded by `load_cached_battlecard()` identically to Claude-generated cards. Regenerating live costs ~$0.06 for all three competitors; stubs cost zero and are reproducible.

### 9. Sentiment drop alert uses a rolling-baseline design

The `sentiment_delta` column in `processed_reviews` stores each review's score minus its 30-day rolling predecessor average (computed by `compute_sentiment_delta()` in the pipeline). The trigger alert then reads `AVG(sentiment_delta)` for the last 7 days:

- Threshold: `avg_delta < -0.5`
- To make the demo DB fire this alert, `seed_demo_db.py` inserts 15 strongly positive reviews 30–40 days before the bad week to create a high baseline.

### 10. BERTopic minimum data requirement

BERTopic requires at least 100 documents to produce coherent clusters. Below that, `train_topics()` logs a warning and all reviews receive `topic_label='insufficient_data'`. The fixture generator produces ~126 reviews per competitor to stay above this threshold.

### 11. APScheduler guarded by a module-level boolean

`start_scheduler()` in `scheduler/jobs.py` checks a module-level `_scheduler_started` flag before creating the `BackgroundScheduler`. Without this guard, repeated calls (e.g. from FastAPI lifespan hooks during development hot-reload) would spawn duplicate scheduler threads and register duplicate jobs. The scheduler is also disabled entirely when `DEMO_MODE=true`.

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
| **No authentication** | Add an auth layer (e.g. FastAPI middleware + JWT) before any public exposure. |
| **weasyprint on Windows** | PDF export falls back to HTML without GTK+ binaries. True PDF works on Linux/macOS. |

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Language | Python 3.11+ |
| NLP | `sentence-transformers` (all-MiniLM-L6-v2), `BERTopic`, `spaCy` (en_core_web_sm), `vaderSentiment` |
| LLM | Anthropic Claude API (`claude-sonnet-4-6`) |
| Database | SQLite → PostgreSQL (via `DATABASE_URL`) |
| Frontend | React 18 + TypeScript 5.5 + Vite 5 |
| API | FastAPI + Uvicorn |
| Scraping | PRAW (Reddit), requests + BeautifulSoup (G2/Trustpilot), newsapi-python |
| Scheduling | APScheduler |
| Alerts | Slack Webhooks, SendGrid |
| Export | pandas, weasyprint (PDF/HTML battlecards) |
| Testing | pytest, unittest.mock |

---

*RivalSense v0.2.0 · OPB AI Mastery Lab*
