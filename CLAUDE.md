# CLAUDE.md — RivalSense

> This file is the authoritative reference for any developer or AI agent working inside this codebase.
> Read it fully before writing any code.

---

## What Is RivalSense?

RivalSense is a modular competitive intelligence suite built for Business Development and sales teams. It scrapes public data from review platforms, social media, and news sources; processes it through a shared NLP pipeline; and surfaces six distinct intelligence modules — each producing a different actionable output (heatmaps, timelines, battlecards, alerts, and lead profiles). The system uses **only publicly available data** — no internal company data required. The primary deliverable is a Streamlit prototype that demonstrates live competitor intelligence to business stakeholders using real G2, Trustpilot, Reddit, and NewsAPI data.

> **UI and wording decisions:** All copy, color, layout, and component styling choices must reference [`BRAND.md`](./BRAND.md) before implementation. If `BRAND.md` and this file conflict on a UI matter, `BRAND.md` wins.

---

## Quick Start

```bash
# 1. Clone and enter the project
git clone https://github.com/your-org/rivalsense.git
cd rivalsense

# 2. Create and activate a virtual environment
python3.11 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt
python -m spacy download en_core_web_sm

# 4. Configure environment variables
cp .env.example .env
# Edit .env and fill in your API keys (see Environment Variables section)

# 5a. DEMO MODE — use pre-seeded database (fastest, no API calls needed)
cp rivalsense_demo.db rivalsense.db
DEMO_MODE=true streamlit run main.py

# 5b. LIVE MODE — run full ingestion + NLP pipeline, then launch
python ingestion/run_ingestion.py     # ~30–60 min first run
python pipeline/run_pipeline.py
DEMO_MODE=false streamlit run main.py
```

> Validate live mode is working: `sqlite3 rivalsense.db "SELECT * FROM processed_reviews LIMIT 20;"` — you should see sensible `topic_label` and `sentiment_score` values.

---

## How the Data Flows

```
┌─────────────────────────────────────────────────────────────────┐
│  LAYER 1 — INGESTION                                            │
│  G2 · Trustpilot · Reddit (PRAW) · NewsAPI · App Store         │
│  → ingestion/run_ingestion.py                                   │
│  → SQLite: reviews table                                        │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│  LAYER 2 — NLP PIPELINE                                         │
│  BERTopic (topics) · VADER + sentence-transformers (sentiment)  │
│  spaCy NER (entities)                                           │
│  → pipeline/run_pipeline.py                                     │
│  → SQLite: processed_reviews table                              │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│  LAYER 3 — INTELLIGENCE MODULES (all read processed_reviews)    │
│                                                                 │
│  M01 Pain Point Radar  ──────────────────────────────────┐      │
│  M02 Sentiment Timeline  ──────────────────────────┐     │      │
│  M03 Feature Wish Miner  ──────────────────────┐   │     │      │
│  M04 Battlecard Generator (Claude API) ────────┘───┘     │      │
│  M05 Trigger Alerts (Claude API, optional) ──────────────┘      │
│  M06 Hot Prospect Finder                                        │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│  LAYER 4 — OUTPUTS                                              │
│  Streamlit Dashboard · Slack Webhooks · SendGrid Email          │
│  CSV / JSON CRM Export (Salesforce, HubSpot)                   │
│  PDF Battlecards (weasyprint)                                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## Module Reference

| # | Module | File | Inputs | Key Output | Feeds Into |
|---|--------|------|--------|------------|------------|
| 01 | Pain Point Radar | `modules/pain_point_radar.py` | `processed_reviews` WHERE competitor | `DataFrame(topic_label, mention_count, avg_severity, trend_direction)` | M04, M02 |
| 02 | Sentiment Timeline | `modules/sentiment_timeline.py` | `processed_reviews` + NewsAPI events | `DataFrame(month, competitor, avg_sentiment, stddev, top_event)` | M05 |
| 03 | Feature Wish Miner | `modules/feature_wish_miner.py` | `processed_reviews.wish_phrases` | `DataFrame(wish_phrase_cluster, count, sample_quotes, your_product_has_it)` | M04 |
| 04 | Battlecard Generator | `modules/battlecard_generator.py` | M01 + M03 outputs + Claude API | Markdown battlecard (+ PDF via weasyprint) | Slack, CRM |
| 05 | Trigger Alerts | `modules/trigger_alerts.py` | Sentiment timeline + NewsAPI (cron) | `Alert(trigger_type, competitor, evidence_summary, outreach_draft)` | M06, CRM |
| 06 | Hot Prospect Finder | `modules/hot_prospect_finder.py` | Reddit PRAW + G2 "switching" flags | `DataFrame(source, username, complaint_summary, company_signals, urgency_score)` | CRM export |

**Key functions per module:**

- `get_pain_points(competitor, top_n=10)` / `compute_trend(topic_id, window_days=30)`
- `build_timeline(competitor, months=18)` / `fetch_news_events(competitor, date_range)`
- `extract_wishes(competitor)` / `flag_own_features(wish_df, own_feature_list)`
- `generate_battlecard(competitor)` / `refresh_all_battlecards()`
- `check_triggers(competitor_list)` / `send_slack_alert(alert)` / `generate_outreach(alert, llm=True)`
- `scan_reddit(competitor_list, subreddits)` / `score_urgency(post)` / `enrich_lead(lead)`

---

## Environment Variables

Copy `.env.example` to `.env` and populate all required keys before running anything.

```bash
# Required — Claude API (Modules 04 and optionally 05)
ANTHROPIC_API_KEY=

# Required — Data sources
NEWSAPI_KEY=
REDDIT_CLIENT_ID=
REDDIT_CLIENT_SECRET=
REDDIT_USER_AGENT=

# Required — Alerts
SLACK_WEBHOOK_URL=

# Optional — Email digests
SENDGRID_API_KEY=

# Required — Database
DATABASE_URL=             # e.g. sqlite:///rivalsense.db or postgres URI

# Demo mode toggle
DEMO_MODE=false           # Set to true to use rivalsense_demo.db
```

---

## Project Structure

```
rivalsense/
├── CLAUDE.md                  ← You are here
├── BRAND.md                   ← UI/copy source of truth — read before touching UI
├── README.md
├── .env.example
├── requirements.txt
├── main.py                    # Streamlit entry point
├── config.py                  # COMPETITORS list, OWN_FEATURES, SUBREDDITS
├── database/
│   ├── schema.sql
│   ├── db.py                  # SQLite connection + query helpers
│   └── migrations/
├── ingestion/
│   ├── scraper_g2.py
│   ├── scraper_trustpilot.py
│   ├── scraper_reddit.py
│   ├── scraper_newsapi.py
│   └── run_ingestion.py
├── pipeline/
│   ├── topic_model.py         # BERTopic training + inference
│   ├── sentiment.py           # VADER + sentence-transformer scoring
│   ├── entity_extractor.py    # spaCy NER
│   └── run_pipeline.py
├── modules/
│   ├── pain_point_radar.py
│   ├── sentiment_timeline.py
│   ├── feature_wish_miner.py
│   ├── battlecard_generator.py
│   ├── trigger_alerts.py
│   └── hot_prospect_finder.py
├── outputs/
│   ├── slack_webhook.py
│   ├── crm_export.py
│   └── pdf_export.py
├── ui/
│   ├── pages/
│   │   ├── 1_pain_point_radar.py
│   │   ├── 2_sentiment_timeline.py
│   │   ├── 3_feature_wish_miner.py
│   │   ├── 4_battlecard_generator.py
│   │   ├── 5_trigger_alerts.py
│   │   └── 6_hot_prospect_radar.py
│   └── components/
│       ├── competitor_selector.py
│       └── charts.py
├── scheduler/
│   └── jobs.py                # APScheduler daily scrape + alert checks
└── tests/
    ├── test_pipeline.py
    └── test_modules.py
```

---

## Competitor Configuration (`config.py`)

Adding or modifying competitors is the most common maintenance task. Always do it here — never hardcode competitor names elsewhere.

```python
COMPETITORS = [
  {
    "name": "Salesforce",
    "g2_slug": "salesforce-crm",
    "trustpilot_slug": "salesforce.com",
    "reddit_keywords": ["salesforce", "sfdc"]
  },
  {
    "name": "HubSpot",
    "g2_slug": "hubspot",
    "trustpilot_slug": "hubspot.com",
    "reddit_keywords": ["hubspot"]
  },
  # Add new competitors here
]

OWN_FEATURES = [
  "ai email suggestions",
  "flat rate pricing",
  "offline mobile",
  # Add your product's differentiating features here
]
```

---

## When Working on This Project

### Adding a New Competitor

1. Add the competitor dict to `COMPETITORS` in `config.py` — include all four fields (`name`, `g2_slug`, `trustpilot_slug`, `reddit_keywords`).
2. Run `python ingestion/run_ingestion.py --competitor "CompetitorName"` to seed initial data.
3. Run `python pipeline/run_pipeline.py --competitor "CompetitorName"` to process it.
4. Validate: `processed_reviews` should contain at least 100 rows for the competitor before topic modeling will produce meaningful clusters.
5. Regenerate battlecards: `python -c "from modules.battlecard_generator import refresh_all_battlecards; refresh_all_battlecards()"`.

### Retraining the Topic Model

- BERTopic requires **minimum 100 reviews per competitor** to cluster reliably. Below that, topic labels will be noisy.
- Retrain only when you have significantly more data (>500 new reviews) or when topic labels become stale.
- Run: `python pipeline/topic_model.py --retrain`
- After retraining, re-run `pipeline/run_pipeline.py` to refresh `topic_label` and `topic_cluster` for all existing records.
- **Do not retrain mid-demo** — it invalidates historical topic continuity.

### Modifying the Battlecard Prompt (Module 04)

- The system prompt and user prompt are defined in `modules/battlecard_generator.py`.
- The system prompt defines the **battlecard format** (objection → evidence → counter → proof quote). Do not change the JSON schema it returns unless you also update the markdown renderer.
- The user prompt **injects ranked pain points and feature gaps** at call time — this is the variable part.
- Always request **JSON output** from the LLM and render to markdown separately. Never ask for raw markdown directly — JSON is more reliable to parse.
- After any prompt change, run `generate_battlecard("Salesforce")` manually and inspect the output before committing.
- All LLM calls must use the `@retry_with_backoff` decorator defined in `utils/llm.py`.

### Adding a New Streamlit Page

1. Create `ui/pages/N_module_name.py` where `N` is the next integer in sequence.
2. Import **only from `modules/`** — no business logic or DB queries in UI files.
3. Use `ui/components/competitor_selector.py` for the competitor dropdown — do not re-implement it.
4. Use `ui/components/charts.py` for all chart wrappers — keeps chart styling consistent.
5. **Before writing any copy or choosing colors/layout:** open `BRAND.md` and follow the guidelines there. Every label, heading, button text, and color token must comply with the brand system.
6. Add the page to the sidebar navigation order in `main.py`.

### Coding Conventions

- All module functions return `pandas.DataFrame` or plain Python `dict` — no side effects.
- Use type hints on all public functions. All public functions must have docstrings.
- All scrapers must respect `robots.txt` and include a `1–2s` delay between requests.
- All LLM calls must be wrapped with the `@retry_with_backoff` decorator (exponential backoff, max 3 retries).
- Tests use `pytest` with fixture-based mock data. **No real API calls in tests.**
- UI files import from `modules/` only.

---

## Demo Data Strategy

Two modes are supported, toggled via `DEMO_MODE` in `.env`:

| Mode | How to activate | Data source | Startup time |
|------|----------------|-------------|-------------|
| `DEMO_MODE=true` | Copy `rivalsense_demo.db` → `rivalsense.db` | Pre-seeded frozen snapshot | ~5 seconds |
| `DEMO_MODE=false` | Run ingestion + pipeline scripts | Live scraping | 30–60 min first run |

**For stakeholder demos:** always use `DEMO_MODE=true`. The demo database contains curated real data frozen at a specific snapshot date, ensuring a consistent and reproducible demo experience. Never run live scraping during a demo.

The demo database ships with a pre-loaded "bad week" scenario for Module 05 (Trigger Alerts) — a simulated sentiment drop for one competitor — so that alert firing can be demonstrated without waiting for a real event.

---

## Build Order (Recommended)

Follow this sequence. Each step depends on the prior one.

```
Step 1  Days 1–2   ingestion/ + pipeline/          → SQLite foundation
Step 2  Days 3–5   modules/pain_point_radar.py      → Demo centrepiece
Step 3  Days 6–8   sentiment_timeline + wish_miner  → Reuse processed_reviews
Step 4  Days 9–10  battlecard_generator             → Wire Claude API, test prompt
Step 5  Days 11–14 trigger_alerts + hot_prospects   → Add APScheduler
Step 6  Days 15–17 Polish + demo prep               → Sidebar, Slack, demo dataset
```

---

## Known Limitations (Prototype)

| Limitation | Detail |
|------------|--------|
| **Scraping rate limits** | G2 and Trustpilot throttle aggressive scrapers. Keep delays at 1–2s minimum. If blocked, switch to cached HTML fixtures for the demo. |
| **BERTopic minimum data** | Topic modeling produces unreliable clusters below ~100 reviews per competitor. With sparse data, `topic_label` may show as `-1 (outlier)` — expected behavior, not a bug. |
| **Claude API cost** | Each `generate_battlecard()` call costs approximately $0.01–$0.04 depending on input size (using `claude-sonnet-4-6`). `refresh_all_battlecards()` across 10 competitors = ~$0.40. Budget accordingly and avoid unnecessary regeneration. |
| **Reddit API tier** | The free Reddit API tier (Personal Use Script) limits to 100 requests/minute and 1,000 posts per query. For Module 06 (Hot Prospect Finder), this is sufficient for prototype use but insufficient for production-scale monitoring. |
| **No authentication** | The Streamlit prototype has no user authentication. Do not expose it on a public URL without adding auth (e.g., `streamlit-authenticator`). |
| **SQLite concurrency** | SQLite does not support concurrent writes. In dev this is fine. Before production, migrate to PostgreSQL (`DATABASE_URL` already supports this). |

---

## Extending RivalSense

Three suggested next modules once the core six are stable:

### M07 — Win/Loss Interview Analyzer
Ingest structured win/loss interview transcripts (from Gong, Chorus, or CSV uploads). Use the same NLP pipeline to extract recurring loss reasons and winning differentiators. Output: ranked loss-reason report per competitor, with trend over time.

### M08 — LinkedIn Champion Monitor
Monitor LinkedIn public posts (via LinkedIn API or Phantombuster) for mentions of competitor products by people with buyer or champion personas. Surface contacts who are publicly dissatisfied or exploring alternatives. Enriches Module 06 leads with professional context.

### M09 — Pricing Intelligence Tracker
Scrape and monitor competitor pricing pages over time. Detect pricing changes, new tiers, and promotional offers. Alert sales when a competitor drops price (potential panic discount signal) or raises price (opportunity to position on value).

---

## Tech Stack Reference

| Layer | Technology |
|-------|-----------|
| Language | Python 3.11+ |
| NLP | `sentence-transformers`, `BERTopic`, `spaCy` (`en_core_web_sm`), `vaderSentiment` |
| LLM | Anthropic Claude API (`claude-sonnet-4-6`) — Modules 04 and 05 only |
| Database | SQLite (dev) → PostgreSQL (prod) |
| Dashboard | Streamlit (primary UI) |
| Scraping | `PRAW` (Reddit), `requests` + `BeautifulSoup` (G2/Trustpilot), `newsapi-python` |
| Scheduling | `APScheduler` (cron for alerts + scraping) |
| Alerts | Slack Webhooks, SendGrid (email) |
| Export | `pandas` + `openpyxl` (Excel/CSV), `weasyprint` (PDF battlecards) |
| Env | `python-dotenv` |

---

*Last updated: see git log. This file is maintained alongside the codebase — update it when architecture changes.*
