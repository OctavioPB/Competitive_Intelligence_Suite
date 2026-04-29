"""APScheduler job definitions for daily scraping and alert checks."""

import logging
import os

logger = logging.getLogger(__name__)


def job_scrape_and_process() -> None:
    """Daily job: run ingestion pipeline then NLP pipeline for all competitors."""
    raise NotImplementedError("Implement in Sprint 5 — Day 13")


def job_check_alerts() -> None:
    """Daily job: check all trigger conditions and fire Slack alerts for new signals."""
    raise NotImplementedError("Implement in Sprint 5 — Day 13")


def start_scheduler() -> None:
    """Start the APScheduler BackgroundScheduler with all daily jobs.

    Only starts if DEMO_MODE env var is not 'true'. Safe to call from main.py
    — guards against double-initialisation via st.session_state.
    """
    raise NotImplementedError("Implement in Sprint 5 — Day 13")
