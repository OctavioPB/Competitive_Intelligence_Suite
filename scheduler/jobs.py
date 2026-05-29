"""APScheduler job definitions for daily scraping and alert checks."""

import logging
import os

logger = logging.getLogger(__name__)


def job_scrape_and_process() -> None:
    """Daily job: run full ingestion then NLP pipeline for all competitors."""
    from config import COMPETITORS
    from ingestion.run_ingestion import run_for_competitor as ingest
    from pipeline.run_pipeline import run_for_competitor as process

    logger.info("Scheduled job: starting daily scrape and process...")
    for competitor in COMPETITORS:
        try:
            ingest(competitor)
            process(competitor)
            logger.info("Processed competitor: %s", competitor["name"])
        except Exception as exc:  # noqa: BLE001
            logger.error("Failed to process %s: %s", competitor["name"], exc)
    logger.info("Scheduled job: scrape and process complete.")


def job_check_alerts() -> None:
    """Daily job: detect trigger signals and fire Slack alerts for new ones."""
    from config import COMPETITOR_NAMES
    from modules.trigger_alerts import check_triggers, generate_outreach, send_slack_alert

    logger.info("Scheduled job: checking alert triggers for %d competitors...", len(COMPETITOR_NAMES))
    alerts = check_triggers(COMPETITOR_NAMES)

    for alert in alerts:
        alert.outreach_draft = generate_outreach(alert, llm=False)
        send_slack_alert(alert)

    logger.info("Scheduled job: %d alert(s) fired.", len(alerts))


def job_send_digest() -> None:
    """Weekly job: generate intelligence digest and send via email + Slack."""
    import os

    from config import COMPETITOR_NAMES
    from modules.digest_generator import generate_digest

    logger.info("Scheduled job: generating weekly intelligence digest ...")
    try:
        digest = generate_digest(COMPETITOR_NAMES)
        logger.info("Digest generated: %s", digest.get("generated_at", ""))
    except Exception as exc:  # noqa: BLE001
        logger.error("Digest generation failed: %s", exc)
        return

    to_email = os.getenv("DIGEST_EMAIL", "")
    if to_email:
        from outputs.email_digest import send_weekly_digest
        send_weekly_digest(alerts=[], leads_df=None, to_email=to_email)

    logger.info("Scheduled job: digest complete.")


def start_scheduler() -> None:
    """Start the APScheduler BackgroundScheduler with all daily jobs.

    Only starts when DEMO_MODE is not 'true'. Guards against double-initialisation
    via st.session_state so Streamlit reruns don't spawn multiple schedulers.
    """
    import streamlit as st
    from apscheduler.schedulers.background import BackgroundScheduler  # type: ignore[import]

    demo_mode = os.getenv("DEMO_MODE", "false").lower() == "true"
    if demo_mode:
        logger.info("DEMO_MODE=true — APScheduler not started.")
        return

    if st.session_state.get("_scheduler_started"):
        return

    scheduler = BackgroundScheduler()
    scheduler.add_job(job_scrape_and_process, "cron", hour=2, minute=0, id="daily_scrape")
    scheduler.add_job(job_check_alerts, "cron", hour=3, minute=0, id="daily_alerts")
    scheduler.add_job(job_send_digest, "cron", day_of_week="mon", hour=7, minute=0, id="weekly_digest")
    scheduler.start()

    st.session_state["_scheduler_started"] = True
    logger.info(
        "APScheduler started: daily_scrape@02:00, daily_alerts@03:00."
    )
