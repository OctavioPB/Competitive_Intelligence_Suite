# PLAN.md — RivalSense Development Sprints

> Agile sprint plan for the RivalSense prototype.
> Timeline: **17 working days** across **7 sprints** (Sprint 0 + Sprints 1–6).
> Team assumption: 1–2 data scientists working full-time on the prototype.
> All UI and copy decisions must reference `BRAND.md` before implementation.

---

## Sprint Overview

| Sprint | Name | Days | Deliverable |
|--------|------|------|-------------|
| S0 | Project Scaffold | Day 0 | Repo, env, schema, CI skeleton |
| S1 | Data Foundation | Days 1–2 | Ingestion + NLP pipeline → seeded SQLite |
| S2 | Pain Point Radar | Days 3–5 | M01 live in Streamlit — demo centrepiece |
| S3 | Timeline + Wish Miner | Days 6–8 | M02 + M03 live in Streamlit |
| S4 | Battlecard Generator | Days 9–10 | M04 — Claude API wired, PDF export |
| S5 | Alerts + Prospects | Days 11–14 | M05 + M06 + APScheduler |
| S6 | Demo Polish | Days 15–17 | Demo dataset, CRM exports, full integration |

---

## Dependency Graph

```
S0 ──► S1 ──► S2 ──► S3 ──► S4 ──► S5 ──► S6
              │             ▲      ▲
              └─────────────┘      │
                   M01 feeds M04   │
                                   │
              S3 ─────────────────►┘
                   M02 feeds M05
```

No sprint can start until its predecessor's **Definition of Done** is fully met.

---

## Sprint 0 — Project Scaffold

**Duration:** Day 0 (half-day)
**Goal:** Every developer (or Claude Code session) can clone the repo, activate the environment, and have the folder structure ready to receive code. No business logic yet.

### Tasks

- [ ] Initialize git repo with `.gitignore` (Python, `.env`, `*.db`, `__pycache__`)
- [ ] Create full directory tree as specified in `CLAUDE.md` — all folders and empty `__init__.py` files
- [ ] Write `requirements.txt` with pinned versions for all dependencies
- [ ] Write `.env.example` with all required keys (values empty, comments explaining each)
- [ ] Write `database/schema.sql` — both `reviews` and `processed_reviews` tables with all fields
- [ ] Write `database/db.py` — SQLite connection, `get_conn()`, generic `query_df(sql, params)` helper
- [ ] Write `config.py` — initial `COMPETITORS` list (3 competitors), `OWN_FEATURES`, `SUBREDDITS`
- [ ] Write empty stub files for all modules, scrapers, and pipeline scripts with docstrings only
- [ ] Write `BRAND.md` — placeholder structure (fill in before S2 UI work)
- [ ] Set up `pytest` with a single smoke test confirming DB schema creates without errors
- [ ] Validate: `pytest tests/` passes. `python -c "from database.db import get_conn; print('DB OK')"` runs.

### Definition of Done

- [ ] Repo is cloned fresh and `pip install -r requirements.txt` completes without errors
- [ ] `python -m spacy download en_core_web_sm` succeeds
- [ ] `sqlite3 rivalsense.db < database/schema.sql` creates both tables
- [ ] `pytest tests/` returns 1 passed, 0 failed
- [ ] `BRAND.md` exists with at least color palette and typography sections stubbed

### Risks

| Risk | Mitigation |
|------|-----------|
| Dependency version conflicts (BERTopic + sentence-transformers) | Pin to known-compatible versions; test on clean venv before committing |
| spaCy model download blocked by corporate network | Bundle `en_core_web_sm` wheel in `/vendor/` as fallback |

---

## Sprint 1 — Data Foundation

**Duration:** Days 1–2
**Goal:** Real review data is ingested from at least two sources and stored in SQLite. The NLP pipeline processes raw reviews into `processed_reviews` with sensible `topic_label` and `sentiment_score` values. This is the shared foundation every module depends on.

### Day 1 — Ingestion Layer

- [ ] `ingestion/scraper_g2.py` — scrape reviews for all competitors in `config.COMPETITORS`
  - Respect `robots.txt`. Add `time.sleep(random.uniform(1, 2))` between requests.
  - Parse: `source`, `competitor_name`, `review_text`, `rating`, `date`, `author_id`, `helpful_count`
  - Store to `reviews` table via `database/db.py`
- [ ] `ingestion/scraper_trustpilot.py` — same structure, different HTML selectors
- [ ] `ingestion/scraper_reddit.py` — PRAW-based; pull top posts mentioning competitor keywords
- [ ] `ingestion/scraper_newsapi.py` — fetch news articles per competitor for the last 18 months
- [ ] `ingestion/run_ingestion.py` — orchestrates all scrapers; accepts `--competitor` flag
- [ ] Validate: `SELECT COUNT(*) FROM reviews GROUP BY competitor_name` shows ≥ 100 rows per competitor

### Day 2 — NLP Pipeline

- [ ] `pipeline/sentiment.py` — VADER baseline score + `sentence-transformers` fine-tuned score; output `sentiment_score` (float, -1 to 1) and `sentiment_delta` (vs prior 30-day avg)
- [ ] `pipeline/topic_model.py` — BERTopic training on `review_text`; assign `topic_cluster` (int) and `topic_label` (str) to each review
  - Guard: if fewer than 100 reviews for a competitor, log a warning and skip BERTopic — assign `topic_label = "insufficient_data"`
- [ ] `pipeline/entity_extractor.py` — spaCy NER; extract product names, feature names, company names into `entities` (JSON list)
- [ ] `pipeline/run_pipeline.py` — reads from `reviews`, writes to `processed_reviews`; accepts `--competitor` flag; idempotent (re-running does not duplicate rows)
- [ ] Write `tests/test_pipeline.py` — fixture with 5 synthetic reviews; assert `processed_reviews` schema and non-null fields. No real API calls.
- [ ] Validate: `SELECT topic_label, sentiment_score FROM processed_reviews LIMIT 20` shows human-readable labels and scores in [-1, 1]

### Definition of Done

- [ ] `python ingestion/run_ingestion.py` completes without exceptions for all 3 competitors
- [ ] `python pipeline/run_pipeline.py` completes without exceptions
- [ ] `processed_reviews` contains ≥ 100 rows per competitor with non-null `topic_label`, `sentiment_score`, `entities`
- [ ] `pytest tests/test_pipeline.py` passes
- [ ] No hardcoded competitor names anywhere outside `config.py`

### Risks

| Risk | Mitigation |
|------|-----------|
| G2 / Trustpilot blocks scraper | Switch to pre-cached HTML fixtures stored in `tests/fixtures/`; use fixture data for demo too |
| BERTopic training takes > 30 min on sample data | Reduce `min_topic_size` parameter; use `embedding_model="all-MiniLM-L6-v2"` (faster, smaller) |
| Reddit PRAW rate limit hit | Implement exponential backoff in `scraper_reddit.py`; cache results locally |

---

## Sprint 2 — Pain Point Radar (M01)

**Duration:** Days 3–5
**Goal:** Module 01 is complete and live in Streamlit. A stakeholder can select a competitor from a dropdown and see a live bar chart of ranked pain points updated from real data. This is the demo centrepiece.

### Day 3 — Module Logic

- [ ] `modules/pain_point_radar.py`
  - `get_pain_points(competitor: str, top_n: int = 10) -> pd.DataFrame`
    - Query `processed_reviews` WHERE `competitor_name = competitor`
    - Group by `topic_label`, compute `mention_count`, `avg_severity` (inverse of avg sentiment), `trend_direction`
    - Return DataFrame sorted by `avg_severity DESC`
  - `compute_trend(topic_id: int, window_days: int = 30) -> str`
    - Compare mention count in last `window_days` vs prior equivalent window
    - Return `"rising"`, `"stable"`, or `"declining"`
- [ ] Unit test in `tests/test_modules.py` — fixture DataFrame; assert output columns and sort order

### Day 4 — UI Page

- [ ] `ui/components/competitor_selector.py` — reusable `st.selectbox` populated from `config.COMPETITORS`
- [ ] `ui/components/charts.py` — `render_bar_chart(df, x, y, title)` wrapper using Plotly; apply brand colors from `BRAND.md`
- [ ] `ui/pages/1_pain_point_radar.py`
  - Import `competitor_selector`, `get_pain_points`, `render_bar_chart`
  - No business logic in this file — only UI wiring
  - Heatmap: color cells by `avg_severity` (red = high pain)
  - Show `trend_direction` as icon alongside each topic (↑ ↗ → ↘ ↓)
  - **Read `BRAND.md` before writing any label, color, or layout**

### Day 5 — Integration + Smoke Test

- [ ] Wire `ui/pages/1_pain_point_radar.py` into `main.py` sidebar
- [ ] Manual QA: select each competitor → chart updates with correct data
- [ ] `DEMO_MODE` guard: if `DEMO_MODE=true`, load from `rivalsense_demo.db` instead of live DB
- [ ] Confirm page loads in < 3 seconds in demo mode
- [ ] Document: add M01 row to the module reference table in `CLAUDE.md` if anything changed

### Definition of Done

- [ ] `streamlit run main.py` launches without errors
- [ ] Competitor dropdown populates from `config.COMPETITORS`
- [ ] Selecting a competitor renders a bar chart with ≥ 5 pain points and correct trend indicators
- [ ] All UI copy and colors comply with `BRAND.md`
- [ ] Page load ≤ 3s in demo mode
- [ ] `pytest tests/test_modules.py::test_pain_point_radar` passes

### Risks

| Risk | Mitigation |
|------|-----------|
| Fewer than 100 reviews → BERTopic noise | Show a warning banner in the UI; use fixture data to guarantee ≥ 100 rows in demo mode |
| Chart styling doesn't match BRAND.md | Review `BRAND.md` color tokens before writing any Plotly `marker_color` value |

---

## Sprint 3 — Sentiment Timeline + Feature Wish Miner (M02 + M03)

**Duration:** Days 6–8
**Goal:** Two modules built and live. Both reuse `processed_reviews` — no new scraping needed. M02 adds the NewsAPI event overlay. M03 produces the feature gap table with the "YOUR PRODUCT HAS THIS ✓" badge column.

### Day 6 — M02 Module Logic

- [ ] `modules/sentiment_timeline.py`
  - `build_timeline(competitor: str, months: int = 18) -> pd.DataFrame`
    - Aggregate `processed_reviews` by month: `avg_sentiment`, `stddev`, `review_count`
    - Join with news events from `scraper_newsapi.py` results stored in `reviews`
    - Return `DataFrame(month, competitor, avg_sentiment, stddev, top_event, event_url)`
  - `fetch_news_events(competitor: str, date_range: tuple) -> list[dict]`
    - Pull from NewsAPI records in SQLite (already ingested in S1)
    - Filter for negative-sentiment articles; return top 1 per month

### Day 7 — M02 UI + M03 Module Logic

- [ ] `ui/pages/2_sentiment_timeline.py`
  - Interactive Plotly line chart with monthly sentiment
  - Clickable markers on news event dates — tooltip shows `top_event` headline
  - Date range slider to zoom in/out
  - **Read `BRAND.md` before any styling**
- [ ] `modules/feature_wish_miner.py`
  - `extract_wishes(competitor: str) -> pd.DataFrame`
    - Filter `processed_reviews.wish_phrases` using regex patterns (`"I wish"`, `"would be nice if"`, `"please add"`, `"missing"`, `"need"`, etc.)
    - Cluster similar wishes using sentence embeddings (cosine similarity > 0.8 → same cluster)
    - Return `DataFrame(wish_phrase_cluster, count, sample_quotes)`
  - `flag_own_features(wish_df: pd.DataFrame, own_feature_list: list) -> pd.DataFrame`
    - For each `wish_phrase_cluster`, check semantic similarity against `config.OWN_FEATURES`
    - Add boolean column `your_product_has_it`; add string column `matched_feature`

### Day 8 — M03 UI + Tests

- [ ] `ui/pages/3_feature_wish_miner.py`
  - Table with columns: Wish Cluster | Mentions | Sample Quote | ✓ Your Product Has This
  - Filter toggle: "Show only gaps your product fills"
  - Badge styling for `your_product_has_it = True` — use brand accent color from `BRAND.md`
- [ ] Tests for both modules in `tests/test_modules.py` — fixture-based, no API calls
- [ ] Wire both pages into `main.py` sidebar

### Definition of Done

- [ ] M02: Timeline chart renders for all competitors; clicking a news marker shows headline
- [ ] M02: Date range slider works; chart re-renders within 2s
- [ ] M03: Wish table shows ≥ 5 clusters per competitor; `your_product_has_it` column populated
- [ ] M03: Filter toggle hides/shows rows correctly
- [ ] All UI copy and colors comply with `BRAND.md`
- [ ] `pytest tests/test_modules.py` passes for M01, M02, M03

### Risks

| Risk | Mitigation |
|------|-----------|
| `wish_phrases` column sparse (regex misses many reviews) | Expand regex pattern list; add a secondary pass with zero-shot classifier |
| Sentiment timeline flat (low variance) | Ensure demo dataset includes a synthetic sentiment dip for at least one competitor |

---

## Sprint 4 — Battlecard Generator (M04)

**Duration:** Days 9–10
**Goal:** Module 04 uses Claude API to generate a structured sales battlecard from M01 + M03 outputs. The battlecard is rendered in the UI and exported as PDF. The LLM prompt is tested and stable.

### Day 9 — LLM Wiring + Prompt Engineering

- [ ] `utils/llm.py` — `@retry_with_backoff` decorator (exponential backoff, max 3 retries, catches `anthropic.RateLimitError` and `anthropic.APIStatusError`)
- [ ] `modules/battlecard_generator.py`
  - **System prompt** — defines battlecard JSON schema:
    ```json
    {
      "competitor": "string",
      "generated_at": "ISO timestamp",
      "objections": [
        {
          "objection": "string",
          "evidence": "string (pain point + mention count)",
          "counter": "string",
          "proof_quote": "string (verbatim from reviews)"
        }
      ],
      "feature_gaps": [
        {
          "gap": "string",
          "frequency": int,
          "your_advantage": "string"
        }
      ],
      "recommended_pitch": "string (2–3 sentences)"
    }
    ```
  - **User prompt** — injects top 5 pain points from M01 and top 5 feature gaps from M03
  - `generate_battlecard(competitor: str) -> dict` — calls Claude API, parses JSON response, returns dict
  - `refresh_all_battlecards() -> None` — iterates `config.COMPETITORS`, calls `generate_battlecard()` for each, saves results to `outputs/battlecards/`
- [ ] Test prompt stability: run `generate_battlecard("Salesforce")` 3 times; confirm JSON schema is consistent each time

### Day 10 — Rendering + PDF Export

- [ ] Markdown renderer: `dict → markdown` battlecard template
- [ ] `outputs/pdf_export.py` — converts markdown battlecard to PDF via `weasyprint`
- [ ] `ui/pages/4_battlecard_generator.py`
  - Competitor selector → "Generate Battlecard" button → 5-second spinner → rendered markdown card
  - "Download PDF" button below rendered card
  - Timestamp showing when card was last generated
  - "Regenerate from latest data" button — re-calls `generate_battlecard()`
  - **Read `BRAND.md` for card layout and typography**
- [ ] Cost guard: log estimated token count per call to console; warn if > 2,000 tokens
- [ ] Unit test: mock the Anthropic client; assert `generate_battlecard()` handles API errors gracefully

### Definition of Done

- [ ] `generate_battlecard("Salesforce")` returns a valid dict matching the JSON schema
- [ ] PDF is generated without errors and opens correctly
- [ ] UI shows rendered battlecard within 10s of button click
- [ ] "Regenerate" button works and updates the timestamp
- [ ] All LLM calls wrapped with `@retry_with_backoff`
- [ ] `pytest tests/test_modules.py::test_battlecard_generator` passes (with mocked client)
- [ ] No real API calls in tests

### Risks

| Risk | Mitigation |
|------|-----------|
| LLM returns malformed JSON | Wrap `json.loads()` in try/except; add a repair prompt as fallback; log raw response |
| `weasyprint` PDF rendering broken on Windows | Test on target OS early; have HTML-only fallback ready |
| Claude API cost accumulates during development | Use `claude-haiku-3-5` for prompt iteration; switch to `claude-sonnet-4-6` only for final validation |

---

## Sprint 5 — Trigger Alerts + Hot Prospect Finder (M05 + M06)

**Duration:** Days 11–14
**Goal:** Monitoring and lead generation are live. M05 fires Slack alerts when competitor vulnerability signals are detected. M06 surfaces Reddit posts from people actively switching. APScheduler runs both on a daily cron.

### Day 11 — M05 Alert Logic

- [ ] `modules/trigger_alerts.py`
  - `check_triggers(competitor_list: list) -> list[Alert]`
    - Signal 1: `sentiment_delta < -0.5` in last 7 days (from M02 data)
    - Signal 2: NewsAPI article with negative keywords (`"outage"`, `"lawsuit"`, `"layoffs"`, `"breach"`, `"downtime"`) in last 48h
    - Signal 3: `review_count` spike > 2× 30-day average in last 7 days
    - Return list of `Alert` dataclasses: `(trigger_type, competitor, evidence_summary, timestamp)`
  - `generate_outreach(alert: Alert, llm: bool = True) -> str`
    - If `llm=True`: call Claude API with alert context; return pre-drafted outreach message
    - If `llm=False`: use template string with `alert.competitor` and `alert.trigger_type` substituted
  - `send_slack_alert(alert: Alert) -> None`
    - POST to `SLACK_WEBHOOK_URL` via `outputs/slack_webhook.py`
    - Message format: competitor name, trigger type, evidence summary, outreach draft

### Day 12 — M05 UI + M06 Module Logic

- [ ] `ui/pages/5_trigger_alerts.py`
  - Alert feed — latest 10 alerts, sorted by timestamp DESC
  - Each alert card: trigger type badge, competitor name, evidence summary, suggested outreach (expandable)
  - "Simulate bad week" button — loads the pre-seeded demo alert scenario
  - **Read `BRAND.md` for alert card styling (severity colors)**
- [ ] `modules/hot_prospect_finder.py`
  - `scan_reddit(competitor_list: list, subreddits: list) -> pd.DataFrame`
    - Search each subreddit for competitor keywords + switching intent phrases (`"looking for alternative"`, `"switching from"`, `"leaving X"`, `"X is terrible"`)
    - Return raw post DataFrame: `(source, post_id, username, post_text, post_url, created_at)`
  - `score_urgency(post: dict) -> float`
    - Score 0–1 based on: explicit switching intent keywords (+0.4), negative sentiment (+0.3), recent post (+0.2), upvotes/comments (+0.1)
  - `enrich_lead(lead: dict) -> dict`
    - Add `complaint_summary` (1-sentence NLP summary of post), `company_signals` (extracted entities), `suggested_angle` (template based on competitor pain points from M01)

### Day 13 — M06 UI + Scheduler

- [ ] `ui/pages/6_hot_prospect_finder.py`
  - Weekly digest view: table of top 10 leads by `urgency_score`
  - Columns: Source | Summary | Company Signals | Urgency | Suggested Angle | Post Link
  - "Export to CRM (CSV)" button
  - **Read `BRAND.md` for table styling and urgency indicator colors**
- [ ] `scheduler/jobs.py`
  - APScheduler `BackgroundScheduler` with two daily jobs:
    - `job_scrape_and_process()` — runs `run_ingestion.py` + `run_pipeline.py`
    - `job_check_alerts()` — runs `check_triggers()` + `send_slack_alert()` for any new alerts
  - Scheduler starts automatically when `main.py` runs (`DEMO_MODE=false` only)
- [ ] `outputs/slack_webhook.py` — `post_message(webhook_url, payload)` helper

### Day 14 — Integration + Tests

- [ ] `outputs/crm_export.py` — `export_leads_csv(df)`, `export_leads_json(df)` — standardized field names for Salesforce/HubSpot
- [ ] Tests: `tests/test_modules.py` — M05 and M06 with fixture data; mock Slack webhook
- [ ] End-to-end test: run `check_triggers(["Salesforce"])` with fixture data; assert alert fires; assert Slack payload is correctly structured (do not send)
- [ ] `pytest tests/` — full suite must pass

### Definition of Done

- [ ] `check_triggers()` correctly identifies all 3 signal types from fixture data
- [ ] Slack payload is correctly formatted (verified without sending — check payload dict)
- [ ] `scan_reddit()` returns leads with all required fields populated
- [ ] `score_urgency()` returns float in [0, 1] for all fixture posts
- [ ] APScheduler jobs registered and logging correctly in console (do not need to fire during test)
- [ ] CRM CSV export produces a valid file with correct column names
- [ ] All `pytest tests/` passes

### Risks

| Risk | Mitigation |
|------|-----------|
| Reddit posts returned by PRAW don't match switching-intent criteria | Broaden keyword list; add zero-shot NLI classifier as secondary filter |
| Slack webhook rate limit in demo | Batch alerts into single message; add 1s delay between POSTs |
| APScheduler conflicts with Streamlit's rerun model | Run scheduler in a separate thread; use `st.session_state` flag to prevent re-initialization |

---

## Sprint 6 — Demo Polish + Full Integration

**Duration:** Days 15–17
**Goal:** The suite is demo-ready. The demo database is curated and frozen. The global sidebar is wired. All exports work. A stakeholder watching the demo sees a coherent, branded, professional product.

### Day 15 — Global UI + Brand Audit

- [ ] `main.py` — global sidebar with:
  - RivalSense logo (from `BRAND.md`)
  - Navigation links to all 6 pages
  - Global competitor selector (persists across pages via `st.session_state`)
  - `DEMO_MODE` indicator badge ("DEMO DATA" vs "LIVE DATA")
- [ ] Full brand audit across all 6 UI pages — verify every color, font, label, and button text against `BRAND.md`
- [ ] Replace any default Streamlit styling that conflicts with brand
- [ ] Confirm all page titles and headings use exact copy from `BRAND.md`

### Day 16 — Demo Dataset + Outputs Wiring

- [ ] Curate `rivalsense_demo.db`:
  - ≥ 200 reviews per competitor (Salesforce, HubSpot, + 1 more)
  - Pre-computed `processed_reviews` — no pipeline run needed in demo mode
  - Pre-seeded "bad week" scenario: 7-day sentiment drop of ≥ 0.5 for one competitor
  - Pre-generated battlecards saved to `outputs/battlecards/`
  - Pre-loaded Reddit leads in hot prospect table
- [ ] Freeze demo DB: `cp rivalsense.db rivalsense_demo.db` → commit to repo (or ship as release artifact)
- [ ] `outputs/crm_export.py` — validate CSV and JSON exports open correctly in Excel and Postman
- [ ] PDF battlecard export — confirm PDF renders correctly and is < 500KB per file
- [ ] SendGrid email digest — `outputs/email_digest.py` — weekly HTML email with top alerts and leads (optional, can be stubbed)

### Day 17 — Final QA + Demo Rehearsal

- [ ] Full cold-start test: fresh clone → `pip install` → `cp rivalsense_demo.db rivalsense.db` → `DEMO_MODE=true streamlit run main.py` — must reach running state in < 60s
- [ ] Demo script walkthrough:
  1. Open Pain Point Radar → select Salesforce → bar chart loads
  2. Open Sentiment Timeline → click news event marker → tooltip shows
  3. Open Feature Wish Miner → toggle "gaps your product fills" → table filters
  4. Open Battlecard Generator → click "Regenerate" → card appears (use cached in demo)
  5. Open Trigger Alerts → click "Simulate bad week" → alert fires with outreach draft
  6. Open Hot Prospect Finder → scroll lead table → click "Export to CRM CSV"
- [ ] Fix any issues found in demo walkthrough — no new features, bugs only
- [ ] `pytest tests/` — full suite green
- [ ] Update `CLAUDE.md` with any architecture changes made during development
- [ ] Tag git release: `v0.1.0-prototype`

### Definition of Done

- [ ] Cold-start in < 60s in demo mode
- [ ] All 6 module pages load without errors in demo mode
- [ ] All UI copy and colors comply with `BRAND.md`
- [ ] PDF battlecard downloads successfully
- [ ] CRM CSV export downloads successfully
- [ ] Slack webhook tested (manually fire one alert in dev)
- [ ] `pytest tests/` — full suite green
- [ ] `v0.1.0-prototype` tag created in git

### Risks

| Risk | Mitigation |
|------|-----------|
| Demo DB too large to commit to git | Use `git-lfs` or ship as a separate release artifact download |
| Streamlit session state bugs when switching pages | Test full navigation flow in order; reset `st.session_state` keys on page load |
| Last-minute brand inconsistencies | Run brand audit on Day 15 before any new UI work, not after |

---

## Sprint Velocity Reference

```
Day 0          S0  │ Scaffold
Day 1–2        S1  │████████████████ Data Foundation
Day 3–5        S2  │████████████████████████ Pain Point Radar (M01)
Day 6–8        S3  │████████████████████████ Timeline + Wish Miner (M02, M03)
Day 9–10       S4  │████████████████ Battlecard Generator (M04)
Day 11–14      S5  │████████████████████████████████ Alerts + Prospects (M05, M06)
Day 15–17      S6  │████████████████████████ Demo Polish
```

---

## Cross-Sprint Standards

These apply in every sprint — they are not sprint-specific tasks.

**Code quality (every PR/commit):**
- All public functions have type hints and docstrings
- Module functions return `DataFrame` or `dict` — no side effects
- No business logic in `ui/pages/` files
- All LLM calls use `@retry_with_backoff`
- All scrapers include 1–2s delay between requests

**Testing (every sprint):**
- New module logic → new test in `tests/test_modules.py`
- New pipeline logic → new test in `tests/test_pipeline.py`
- No real API calls in tests — use fixtures and mocks
- `pytest tests/` must pass before closing any sprint

**UI and copy (every sprint with UI work):**
- Open `BRAND.md` before writing any label, color, heading, or button text
- Use `ui/components/competitor_selector.py` for all dropdowns — never re-implement it
- Use `ui/components/charts.py` for all Plotly charts — never call Plotly directly from pages

**Documentation:**
- Update `CLAUDE.md` if any architecture decision changes during the sprint
- Commit message format: `[S{N}] <verb> <what>` — e.g., `[S2] add get_pain_points() with trend computation`

---

## Post-Prototype Roadmap (Beyond Day 17)

Once the prototype is signed off by stakeholders, the following tracks are recommended:

| Track | What | When |
|-------|------|------|
| **Productionization** | Migrate SQLite → PostgreSQL; add Streamlit auth; containerize with Docker | Sprint 7–8 |
| **M07** | Win/Loss Interview Analyzer | Sprint 9 |
| **M08** | LinkedIn Champion Monitor | Sprint 10 |
| **M09** | Pricing Intelligence Tracker | Sprint 11 |
| **Scale** | Replace Streamlit with React frontend; add multi-tenant support | Sprint 12+ |

---

*This file is a living document. Update sprint status inline as tasks are completed.
Closed sprints should be marked with ✅ in the Sprint Overview table.*
