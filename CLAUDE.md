# RivalSense — notes for coding agents

Competitive intelligence suite: Python ingestion + NLP pipeline + intelligence
modules behind a FastAPI backend, React 18 + Vite frontend. README.md has the full
architecture; this file is the short list of rules.

## Commands

```bash
pytest                         # 163 tests, ~25 s — no network, no real API calls
ruff check .                   # rules in ruff.toml (bugs only, no style)
cd frontend && npm run build   # strict tsc + vite build
python scripts/check_live_sources.py   # hits the real websites; not part of CI on PRs
```

Demo stack: `DEMO_MODE=true uvicorn backend.main:app` + `npm run dev` in `frontend/`
(Vite proxies `/api` to 127.0.0.1:8000). Demo data lives in `rivalsense_demo.db`,
built by `scripts/seed_demo_db.py`; databases are git-ignored.

## Layout

- `ingestion/` scrapers → `reviews`; `run_signals.py` → `pricing_snapshots`, `job_postings`
- `pipeline/` NLP (BERTopic, sentiment, spaCy) → `processed_reviews`
- `modules/` one file per feature (M01–M10); `backend/routers/` one router per module
- `frontend/src/services/api.ts` is the only place that calls the API
- Competitors and own features: read them through `modules.settings_store`
  (`competitors()`, `competitor_names()`, `own_features()`), never `config.py` —
  config only seeds a new database; admins edit them in Settings

## Rules

- **Tests never touch the network, Claude or a real DB.** `tests/conftest.py` gives
  every test its own empty SQLite file and blanks `ANTHROPIC_API_KEY`; call
  `init_schema()` when a test needs tables. Mock HTTP (see `tests/test_integrations.py`).
- **Sample data is always flagged.** Fixture/seeded rows set `is_synthetic = 1`;
  live checks refuse to run in `DEMO_MODE`; sample leads never reach a CRM.
- **Validate competitor names** with `backend.deps.known_competitor` before they reach
  SQL, file names or prompts. SQL is always parameterised.
- **Time windows anchor on the latest stored date** (`MAX(date)` per competitor), not
  on today, so fixture data behaves like live data.
- **Scrapers:** a blocked source raises `ScrapingError` and ingestion carries on with
  the others. Do not add anti-bot evasion (stealth flags, captcha solving, fake
  fingerprints) — G2 and Capterra are reported as blocked by design.
- **Claude calls** go through `utils/llm.py` (`call_claude`, `parse_json_object`).
- **Reading rows for JSON:** use `database.db.query_rows` (NULL stays None). `query_df`
  turns all-NULL columns into NaN, which is truthy and breaks JSON responses.
- **Alerts and leads keep state** in `alert_history` / `prospect_leads`; never reset a
  status or note on re-scan, and only Slack-notify rows from `pending_notifications`.
- **Auth:** every `/api` route needs a session (middleware in `backend/main.py`);
  admin-only routes use `Depends(require_admin)`. Tests run with `AUTH_DISABLED=true`
  unless they set it to false (see `tests/test_platform.py`).
- **Frontend:** colours come from CSS tokens in `styles/tokens.css` (they flip in dark
  mode); shared styles in `styles/shared.ts`.
