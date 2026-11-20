# RivalSense — Competitive Intelligence Suite

[![CI](https://github.com/OctavioPB/Competitive_Intelligence_Suite/actions/workflows/ci.yml/badge.svg?branch=master)](https://github.com/OctavioPB/Competitive_Intelligence_Suite/actions/workflows/ci.yml)
[![CodeQL](https://github.com/OctavioPB/Competitive_Intelligence_Suite/actions/workflows/codeql.yml/badge.svg?branch=master)](https://github.com/OctavioPB/Competitive_Intelligence_Suite/actions/workflows/codeql.yml)
[![Live sources](https://github.com/OctavioPB/Competitive_Intelligence_Suite/actions/workflows/live-sources.yml/badge.svg)](https://github.com/OctavioPB/Competitive_Intelligence_Suite/actions/workflows/live-sources.yml)
[![Python 3.11](https://img.shields.io/badge/python-3.11-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![React 18](https://img.shields.io/badge/react-18-61DAFB?logo=react&logoColor=black)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5-3178C6?logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![Claude](https://img.shields.io/badge/LLM-Claude-D97757?logo=anthropic&logoColor=white)](https://www.anthropic.com/claude)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Dependabot](https://img.shields.io/badge/dependabot-enabled-025E8C?logo=dependabot&logoColor=white)](.github/dependabot.yml)
[![License: Proprietary](https://img.shields.io/badge/license-proprietary-lightgrey)](LICENSE)

> Ten intelligence modules. Public data. Actionable signals for your sales team.

RivalSense is a Competitive Intelligence Suite that scrapes public reviews, social media, news, competitor pricing pages and job boards; processes them through a shared NLP pipeline; and surfaces ten distinct intelligence outputs — ranked pain points, sentiment timelines, feature gap analysis, AI-generated battlecards, vulnerability alerts, switching-intent prospect leads, churn reason analysis, executive digests, personalised outreach generation, and pricing / hiring market signals.

---

## Modules

| # | Module | What it does |
|---|--------|-------------|
| M01 | **Pain Point Radar** | Clusters competitor reviews by topic (BERTopic), ranks by severity and trend direction |
| M02 | **Sentiment Timeline** | 18-month sentiment curve per competitor with NewsAPI event overlay |
| M03 | **Feature Wish Miner** | Extracts feature requests from reviews, clusters semantically, flags gaps your product already covers |
| M04 | **Battlecard Generator** | Claude-powered objection handler + pitch per competitor, exported as JSON/Markdown |
| M05 | **Trigger Alerts** | Detects sentiment drops, negative news, review spikes, pricing-page changes and hiring waves; drafts outreach with one click |
| M06 | **Hot Prospect Finder** | Scans Reddit for switching-intent posts, scores urgency, enriches leads with company signals |
| M07 | **Churn Intelligence** | Categorises why users leave each competitor into 5 structured buckets with proof quotes |
| M08 | **Intelligence Digest** | Claude-synthesised weekly executive brief across all competitors — one page, three action bullets each |
| M09 | **Outreach Composer** | Generates personalised email, LinkedIn DM, and cold call bullets from a prospect's complaint |
| M10 | **Market Signals** | Watches competitor pricing pages for price changes and their job boards for support or integration hiring waves |

Daily-workflow views on top of the modules:

| View | What it does |
|------|-------------|
| **What Changed** | This period vs the one before for one competitor: review volume, sentiment and rating, new / rising / fading complaint topics, battlecard version diff, digest diff, new alerts, pricing changes and new roles — summarised as a few highlights |
| **Compare** | Every competitor side by side: monthly sentiment overlay, 30-day sentiment and rating, top pain points, cached churn reasons, active alerts, last price change, support hiring share |
| **Alert history** | Alerts are stored with a status (new / seen / dismissed); an ongoing signal stays one alert and reaches Slack once |
| **Prospect pipeline** | Every lead found is kept with a stage (new → contacted → replied → opportunity, or not a fit) and a note |
| **Ask RivalSense** | Chat over every stored review: semantic search (the pipeline's sentence-transformer vectors) + a Claude answer that cites its reviews as [n]; without an API key it returns the matching reviews |
| **Win / Loss** | Reps log why each deal was won or lost; each reason area is set against the share of that competitor's review complaints (contested / their strength / proven angle / untapped) |
| **Settings** | Competitors (and all their sources) and your own features, edited in the UI and stored per database; admins also manage user accounts |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│  LAYER 1 — INGESTION                                            │
│  G2 · Capterra · Trustpilot · App Store · Reddit · NewsAPI      │
│  ingestion/run_ingestion.py  →  SQLite: reviews                 │
│  Pricing pages · job boards (Greenhouse/Lever/Ashby/Workday)    │
│  ingestion/run_signals.py  →  pricing_snapshots, job_postings   │
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

# Launch React + FastAPI stack (builds rivalsense_demo.db on first run)
.\demo.ps1
```

On first open the app asks you to **create the first admin account** (allowed only from the
machine running the API). For a single-user local setup you can skip sign-in with
`AUTH_DISABLED=true`.

### Live mode (requires API keys)

```powershell
cp .env.example .env
# Fill in ANTHROPIC_API_KEY, NEWSAPI_KEY, REDDIT_CLIENT_ID/SECRET, SLACK_WEBHOOK_URL

python ingestion/run_ingestion.py   # ~30–60 min first run
python pipeline/run_pipeline.py
python ingestion/run_signals.py     # pricing pages + job boards, ~2 min

# Optional: headless Chromium for JavaScript-rendered pages (HubSpot pricing, G2)
playwright install chromium

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
ANTHROPIC_MODEL=...      # override the Claude model for every module
ENABLE_SCHEDULER=false   # run daily scrape / alerts / weekly digest inside the API process
CORS_ORIGINS=...         # extra browser origins allowed to call the API directly

# CRM sync (optional) — "Send to HubSpot / Salesforce" on the Prospects page
HUBSPOT_ACCESS_TOKEN=...       # private app; scopes crm.objects.contacts.read + write
SALESFORCE_INSTANCE_URL=...    # https://yourcompany.my.salesforce.com
SALESFORCE_ACCESS_TOKEN=...    # or SALESFORCE_CLIENT_ID + SALESFORCE_CLIENT_SECRET (client-credentials flow)
DATABASE_URL=rivalsense.db

# Toggle demo mode (uses rivalsense_demo.db, skips APScheduler)
DEMO_MODE=false

# Authentication (see Authentication below)
AUTH_DISABLED=false            # true = no sign-in; every request acts as a local admin
RIVALSENSE_SETUP_TOKEN=...     # lets the first admin be created from another machine
COOKIE_SECURE=false            # true when served over HTTPS
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
│   ├── run_signals.py         # Pricing pages + job boards → market-signal tables
│   ├── signal_fixtures.py     # Sample pricing change + hiring waves for the demo DB
│   ├── history_fixtures.py    # Earlier battlecard version + two weekly digests for the demo
│   ├── browser.py             # Static fetch → headless Chromium fallback, anti-bot wall detection
│   ├── structured_reviews.py  # schema.org JSON-LD review parser (G2, Capterra)
│   ├── scraper_g2.py
│   ├── scraper_capterra.py
│   ├── scraper_appstore.py    # Apple's public customer-reviews feed
│   ├── scraper_pricing.py     # Price points with plan + unit context
│   ├── scraper_jobs.py        # Greenhouse · Lever · Ashby · Workday job boards
│   ├── scraper_trustpilot.py
│   ├── scraper_reddit.py
│   └── scraper_newsapi.py
│
├── pipeline/
│   ├── run_pipeline.py        # CLI orchestrator
│   ├── topic_model.py         # BERTopic training + inference
│   ├── topic_labeler.py       # Readable topic names (Claude, or keyword fallback)
│   ├── sentiment.py           # VADER + sentence-transformer blend
│   └── entity_extractor.py   # spaCy NER
│
├── modules/
│   ├── review_evidence.py         # Reviews behind a pain point / month + data-provenance stats
│   ├── market_signals.py          # M10 — pricing diffs, role classification, hiring signals
│   ├── alert_history.py           # Stored alerts with status; de-duplicates ongoing signals
│   ├── prospect_pipeline.py       # Leads kept across scans with a pipeline stage and note
│   ├── change_tracker.py          # What changed: review windows, battlecard + digest diffs
│   ├── competitor_compare.py      # All competitors side by side
│   ├── settings_store.py          # Competitors + own features in the DB (seeded from config.py)
│   ├── auth.py                    # Users, scrypt passwords, sessions, login throttling
│   ├── winloss.py                 # Deals and the deal-reason vs review-complaint cross-check
│   ├── ask.py                     # Review embeddings index, retrieval and cited answers
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
│   ├── deps.py                # Shared helpers: competitor validation, JSON-safe floats
│   ├── auth_deps.py           # Sign-in plumbing: current user, admin check, AUTH_DISABLED
│   └── routers/               # One router per module (REST endpoints) + auth, settings, winloss, ask
│
├── frontend/
│   ├── src/
│   │   ├── App.tsx            # Sign-in gate + page routing
│   │   ├── pages/             # One page component per module
│   │   ├── components/        # Nav, Footer, KpiCard, Eyebrow, …
│   │   ├── services/api.ts    # All HTTP calls — no fetch in components
│   │   ├── stores/appStore.ts # Zustand (competitor, outreach prefill)
│   │   ├── hooks/             # useTheme, useToast
│   │   ├── utils/download.ts  # File download + CSV escaping
│   │   └── styles/            # tokens.css (OPB design tokens), shared.ts (shared style objects)
│   ├── index.html
│   └── vite.config.ts         # Proxies /api/* → FastAPI :8000
│
├── outputs/
│   ├── crm_export.py          # CSV + JSON with CRM-canonical columns (scripts)
│   ├── crm_sync.py            # Push leads to HubSpot (contact + note) / Salesforce (Lead)
│   ├── pdf_export.py          # Battlecard → PDF (weasyprint) or print-ready HTML
│   ├── slack_webhook.py       # Block Kit payload helper
│   └── email_digest.py        # SendGrid weekly digest
│
├── scheduler/
│   └── jobs.py                # APScheduler: daily scrape, market signals, alert check (new alerts only), weekly digest
│
├── scripts/
│   ├── seed_demo_db.py        # Generates rivalsense_demo.db
│   ├── create_user.py         # Create an account / reset a password from the server
│   └── check_live_sources.py  # Hits every real source once (weekly Live sources workflow)
│
├── utils/
│   ├── llm.py                 # Claude client, retry, JSON parse/repair (shared by all LLM modules)
│   └── embeddings.py          # Process-wide sentence-transformer singleton
│
├── database/
│   ├── schema.sql             # reviews, processed_reviews, digests, pricing_snapshots, job_postings,
│   │                          # alert_history, prospect_leads, competitors, own_features,
│   │                          # users, sessions, deals, review_embeddings
│   └── db.py                  # SQLite helpers (query_df, query_rows, execute, executemany)
│
└── tests/
    ├── test_features.py        # 13 tests (data provenance, topic names, evidence)
    ├── test_integrations.py    # 15 tests (battlecard export, HubSpot / Salesforce sync)
    ├── test_signals.py         # 31 tests (pricing diffs, job boards, review sources, new alerts)
    ├── test_workflow.py        # 16 tests (alert history, Slack de-dup, pipeline, what changed, compare)
    ├── test_platform.py        # 28 tests (auth, settings, win/loss, Ask RivalSense)
    ├── test_pipeline.py        # 20 tests
    └── test_modules.py         # 40 tests (all modules)
```

---

## Engineering Decisions

### 1. SQLite over PostgreSQL for the prototype

SQLite ships with Python, requires zero infra, and the `DATABASE_URL` variable allows a one-line migration to Postgres when needed. `db.py` wraps every query in `query_df()` (returns a DataFrame) and `executemany()` so the caller never touches a connection object. The demo DB is a SQLite file generated locally by `scripts/seed_demo_db.py` (database files are git-ignored) — stakeholders can run the prototype with no server.

### 2. MAX(date) anchor for all time-windowed SQL

Every query with a relative window (`'-7 days'`, `'-30 days'`) anchors on `MAX(date)` from the dataset rather than `datetime.now()`:

```sql
date >= date(
    (SELECT MAX(date) FROM processed_reviews WHERE competitor_name = ?),
    '-7 days')
```

This means fixture data with dates ending in 2025-12 always produces meaningful signals regardless of when the query runs. Using `date('now', ...)` would return empty results the moment the fixture data ages past the window. The rule applies to every module with a window — pain-point trends, trigger alerts, churn analysis and the digest — and the anchor is always scoped to the competitor being analysed.

### 3. Two-mode database: DEMO_MODE vs DATABASE_URL

`database/db.py` reads `DEMO_MODE` at call time (not import time). When `DEMO_MODE=true` it returns `rivalsense_demo.db`; otherwise it uses `DATABASE_URL`. Relative paths resolve against the repo root, so the app finds the same file whatever directory it is launched from. This means the seeder script (`seed_demo_db.py`) can target the demo DB by setting `DATABASE_URL=rivalsense_demo.db` before importing any project module — no monkey-patching required.

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
# utils/embeddings.py — shared by the pipeline (sentiment, BERTopic) and M03
@lru_cache(maxsize=1)
def get_embedding_model():
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer("all-MiniLM-L6-v2")
```

The pipeline embeds each review once per run and passes the vectors to topic training, topic inference and sentiment scoring. The Feature Wish Miner memoises its clustering on the exact phrase list, so repeat requests skip the model entirely and new reviews invalidate the cache automatically.

### 6. Claude API used only for generation, never for retrieval

The LLM is called in five places: M04 (battlecards), M05 (outreach drafts), M07 (churn categorisation), M08 (digest synthesis), M09 (outreach composition). Every other intelligence function — topic clustering, sentiment scoring, entity extraction, urgency scoring — runs entirely local. This keeps the marginal cost of a demo under $0.20 and makes the app functional with `ANTHROPIC_API_KEY` absent for the analytical modules.

All LLM calls go through `call_claude()` in `utils/llm.py`, which retries rate limits, connection errors and 5xx responses with exponential backoff (3 attempts). Non-retryable errors such as a bad API key fail immediately; a missing key is reported to the UI as a clear 503 message. The model is set in one place (`utils.llm.MODEL`, overridable with `ANTHROPIC_MODEL`).

### 7. JSON-first LLM schema

All Claude calls instruct the model to return a strict JSON object, then each module renders it separately. Raw-Markdown responses from LLMs are brittle to parse. JSON failures trigger a second "repair" call (`utils.llm.parse_json_object`) before raising. Schemas are documented as constants in each module for reference.

### 8. Stub battlecards for demo — no API cost at seeding time

`seed_demo_db.py` writes pre-built `_STUB_BATTLECARDS` JSON objects to `outputs/battlecards/`. They are loaded by `load_cached_battlecard()` identically to Claude-generated cards. Regenerating live costs ~$0.06 for all three competitors; stubs cost zero and are reproducible.

### 9. Sentiment drop alert uses a rolling-baseline design

The `sentiment_delta` column in `processed_reviews` stores each review's score minus its 30-day rolling predecessor average (computed by `compute_sentiment_delta()` in the pipeline). The trigger alert then reads `AVG(sentiment_delta)` for the last 7 days:

- Threshold: `avg_delta < -0.5`
- To make the demo DB fire this alert, `seed_demo_db.py` inserts 15 strongly positive reviews 30–40 days before the bad week to create a high baseline.

### 10. Topic names are written for humans

BERTopic names a cluster after its raw top tokens (`connectors_the_getting_than`). After topic assignment the pipeline renames every cluster in `pipeline/topic_labeler.py`:

- With `ANTHROPIC_API_KEY`: one Claude call per competitor turns each cluster's keywords and sample reviews into a 2–4 word name ("Per-Seat Pricing").
- Without it: the cluster's most distinctive keywords and adjacent-word phrases, ignoring stop words, generic review vocabulary, the competitor's name and anything seen in under 20% of the cluster's reviews ("Critical issue / Premium support").

Names are de-duplicated because modules group by `topic_label`. To rename an existing database without retraining: `python pipeline/run_pipeline.py --relabel`.

### 11. Synthetic data is always labelled

Live ingestion falls back to fixture reviews when a scraper is blocked, so every row carries `is_synthetic` (set by the fixture generator and the demo seeder; older databases are back-filled by `init_schema()`). `GET /api/meta/data-status` reports the synthetic share per competitor, the UI shows a banner whenever any data is synthetic, and evidence lists tag each sample review.

### 12. Every aggregate links to its evidence

`GET /api/reviews?competitor=&topic=&month=&sort=&limit=` returns the reviews behind a number. In the UI, clicking a Pain Point Radar row or a Sentiment Timeline month opens them, most negative first.

### 13. Exports go where the sales team works

- **Battlecard PDF.** `GET /api/battlecard/export` renders the cached battlecard. With weasyprint (Linux/macOS, or Windows + GTK) the server returns a PDF; otherwise it returns the same branded page as print-ready HTML and the UI opens the browser's print dialog ("Save as PDF"), so the button works on every machine.
- **CRM sync.** `POST /api/crm/push` creates the selected Prospects in HubSpot (a lead-stage Contact plus a Note with complaint, urgency and suggested angle) or Salesforce (a Lead). Reddit leads have no e-mail, so the post URL — stored in the standard Website field — is the de-duplication key: re-sending a lead never creates a second record. Sample leads are never sent: the push is refused in demo mode, and the server drops any lead whose URL belongs to the built-in fixtures, whatever flag the browser sends.

### 14. Market signals beyond reviews

- **Pricing pages.** `scraper_pricing.py` extracts *price points* — a price plus the plan name before it and the unit after it ("Professional: $90 /mo/seat") — and `market_signals.record_pricing_check` stores a new version only when that set changes, with what was added and removed. Comparing price points instead of raw HTML ignores rotating banners and markup churn. A change in the last 14 days raises a `pricing_change` alert ("Professional: $90 /mo/seat → $100 /mo/seat").
- **Job boards.** `scraper_jobs.py` reads the public JSON behind Greenhouse, Lever, Ashby and Workday career sites (no keys). Roles are classified by function from title and department; product names such as "Sales Cloud" are ignored so a Sales Cloud engineer counts as engineering. A `hiring_signal` alert fires when ≥5 new roles and ≥25 % of new roles are support/success, or ≥3 new engineering roles are about integrations/APIs. Workday lists newest first, so it is read back 30 days only.
- **Static first, headless second.** `browser.fetch_html` tries plain HTTP and only renders with Playwright when the static HTML lacks the content (HubSpot's pricing needs it; Salesforce and Pipedrive do not — their headless view is actually emptier).

### 15. Blocked sources are reported, not worked around

G2 (DataDome) and Capterra (Cloudflare) serve a challenge page to both plain requests and headless Chromium. `browser.bot_wall` names the protection, the scraper raises `ScrapingError("… blocked by DataDome")`, and ingestion carries on: every source is independent, and fixtures are used only when *all* live sources return nothing. The browser deliberately does not disguise automation. For rated reviews that load reliably, the App Store's official RSS feed is used instead.

### 16. Alerts and leads have memory

`check_triggers` recomputes alerts from the data on every scan, which is right for detection but wrong for a workflow: the scheduler used to post the same sentiment drop to Slack every day it lasted. `alert_history` now stores each detection. A detection with the same competitor, type and `dedupe_key` (a headline, a price-change date, "support" vs "integrations" hiring) seen within the last 7 days updates the existing row; anything else is a new alert. The daily job sends only rows never notified — and marks nothing as notified while `SLACK_WEBHOOK_URL` is unset, so configuring Slack later still delivers them. Statuses (new / seen / dismissed) survive re-scans; a dismissed alert comes back only as a new episode after a week without the signal. Prospect leads work the same way, keyed by post URL: a re-scan refreshes urgency and summary but never the stage or note a rep set.

### 17. BERTopic minimum data requirement

BERTopic requires at least 100 documents to produce coherent clusters. Below that, `train_topics()` logs a warning and all reviews receive `topic_label='insufficient_data'`. The fixture generator produces ~126 reviews per competitor to stay above this threshold.

### 18. APScheduler guarded by a module-level boolean

`start_scheduler()` in `scheduler/jobs.py` checks a module-level `_scheduler_started` flag before creating the `BackgroundScheduler`. Without this guard, repeated calls would spawn duplicate scheduler threads and register duplicate jobs. The scheduler is opt-in: the FastAPI lifespan starts it only when `ENABLE_SCHEDULER=true`, and never when `DEMO_MODE=true`. Ingestion skips reviews that are already stored, so the daily job is safe to re-run.

---

## Adding a Competitor

1. As an admin, open **Settings → Add competitor** (`name` and Reddit keywords required; G2 / Trustpilot slugs, pricing pages, job board, App Store id and Capterra URL optional — each one switches on a source). `config.py` only holds the defaults a new database starts with.
2. `python ingestion/run_ingestion.py --competitor "Name"` to collect data (`--use-fixtures` has sample data only for the three built-in competitors)
3. `python pipeline/run_pipeline.py --competitor "Name"` to process it
4. Regenerate battlecards if needed

---

## Authentication

Every `/api` route requires a signed-in user, except the four used to sign in (`/api/auth/status|login|logout|setup`).

- **Accounts.** Passwords are hashed with scrypt and a per-user salt. Sessions are random 32-byte tokens in an `HttpOnly`, `SameSite=Strict` cookie; only their SHA-256 is stored. Sessions last 14 days; changing a password signs that account out everywhere.
- **Roles.** `admin` edits Settings and manages users; `member` uses everything else and can read Settings.
- **First admin.** Created from the sign-in screen only by a direct request from the API's own machine, or anywhere with `RIVALSENSE_SETUP_TOKEN`; or with `python scripts/create_user.py you@company.com "Your Name" --role admin`.
- **Brute force.** Five failed logins for an email or a client address lock further attempts for 15 minutes.
- **Local single-user.** `AUTH_DISABLED=true` turns sign-in off (every request acts as a local admin).

## Running Tests

```bash
pytest tests/ -v
# 163 tests, ~25 seconds
```

Tests use fixture-based mock data throughout. No real API calls are made, and every test runs against its own empty SQLite file (`tests/conftest.py`), so results never depend on your local database. Patch targets for lazy imports use the source module path (e.g. `outputs.slack_webhook.post_message`), not the calling module path.

### Continuous integration

`.github/workflows/ci.yml` runs on every pull request, on pushes to `master`, and on demand (*Actions → CI → Run workflow*):

| Job | What it checks |
|-----|----------------|
| **Lint** | `ruff check .` — syntax errors, undefined names, unused imports/variables (rules in `ruff.toml`; style is not enforced) |
| **Backend tests** | Full `pytest` suite on Python 3.11, with CPU-only torch, spaCy `en_core_web_sm` and a cached sentence-transformer model |
| **Frontend** | `npm ci && npm run build` — strict TypeScript check plus the production Vite build |

Run the same checks locally before pushing:

```bash
ruff check .
pytest
cd frontend && npm run build
```

### Other workflows and automation

| File | When | What it does |
|------|------|--------------|
| `workflows/live-sources.yml` | Mondays + on demand | Runs `scripts/check_live_sources.py` against the real sites (pricing pages, job boards, App Store; G2 informational). Fails — and GitHub emails the owner — when a source that should work returns nothing, i.e. a scraper broke because a site changed. |
| `workflows/codeql.yml` | PRs to `master`, pushes, weekly | GitHub CodeQL security analysis for Python and TypeScript (results under *Security → Code scanning*). |
| `workflows/claude-code-review.yml` | Every non-draft PR from this repo | Claude reviews the diff and posts inline comments plus a summary, following the rules in `CLAUDE.md`. |
| `workflows/claude.yml` | `@claude` in an issue, PR comment or review | Claude answers, reviews or implements the request (on a `claude/…` branch). Only owners, members and collaborators can trigger it. |
| `dependabot.yml` | Weekly (Actions monthly) | Grouped minor/patch update PRs for pip, npm and GitHub Actions. |

The two Claude workflows need an `ANTHROPIC_API_KEY` repository secret (*Settings → Secrets and variables → Actions*) and the Claude GitHub app installed on the repo — `/install-github-app` in Claude Code does both. Until the secret exists the PR review is skipped with a notice (no red check), and `@claude` mentions do nothing useful.

---

## Known Limitations

| Limitation | Detail |
|------------|--------|
| **Scraping rate limits** | G2 and Trustpilot throttle at <1 req/s. Use `--use-fixtures` for offline development. |
| **BERTopic minimum** | Topic labels show as `insufficient_data` below 100 reviews per competitor. |
| **Reddit API** | Free tier: 100 req/min, 1,000 posts/query. Sufficient for prototype, not for production monitoring. |
| **SQLite concurrency** | Single writer. Migrate to PostgreSQL via `DATABASE_URL` for multi-user production. |
| **Exposing the app** | Sign-in is built in, but serve it behind HTTPS (set `COOKIE_SECURE=true`) and create the first admin before opening the port. There is no password-reset email: admins reset passwords in Settings or with `scripts/create_user.py --reset`. |
| **One client per database** | Competitors, features, users and data live in one SQLite file. Serving several clients means one deployment (or `DATABASE_URL`) per client. |
| **G2 and Capterra block automated access** | Both serve an anti-bot challenge (DataDome / Cloudflare) even to headless Chromium. The scrapers detect it and skip the source; ingestion continues with the others. For G2 data at scale, use G2's own data products rather than scraping. |
| **Fixtures only when every source fails** | `run_ingestion.py` stores synthetic reviews for a competitor only if no live source returned anything; they are flagged and the UI banner says so. |
| **Pipedrive has no job board configured** | No public ATS feed was found for Pipedrive's careers site; add `careers` in `config.py` if one appears. |
| **Pricing labels are heuristic** | Plan names are inferred from the text around each price. Labels stay stable between checks (which is what change detection needs) but can be imperfect on unusual layouts. |
| **weasyprint on Windows** | Without GTK the server cannot render PDFs; the Download PDF button falls back to the browser's print dialog. |
| **CRM sync tested against mocks only** | HubSpot and Salesforce calls are covered by unit tests with a fake HTTP session; run one push against a sandbox portal / org before relying on it. |

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
| Scraping | PRAW (Reddit), requests + BeautifulSoup, Playwright (headless Chromium, optional), newsapi-python, public ATS JSON (Greenhouse/Lever/Ashby/Workday), App Store RSS |
| Scheduling | APScheduler |
| Alerts | Slack Webhooks, SendGrid |
| Export | pandas, weasyprint (PDF/HTML battlecards) |
| Testing | pytest, unittest.mock |

---

## License

Proprietary — all rights reserved. Using, copying, modifying or distributing RivalSense requires prior written approval from the copyright holder; see [LICENSE](LICENSE). Third-party libraries keep their own licenses.

---

*RivalSense v0.2.0 · OPB AI Mastery Lab*
