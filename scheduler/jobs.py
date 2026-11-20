"""APScheduler job definitions for daily scraping and alert checks."""

import logging
import os

logger = logging.getLogger(__name__)


def job_scrape_and_process() -> None:
    """Daily job: run full ingestion then NLP pipeline for all competitors."""
    from modules.settings_store import competitors
    from ingestion.run_ingestion import run_for_competitor as ingest
    from pipeline.run_pipeline import run_for_competitor as process

    logger.info("Scheduled job: starting daily scrape and process...")
    for competitor in competitors():
        try:
            ingest(competitor)
            process(competitor)
            logger.info("Processed competitor: %s", competitor["name"])
        except Exception as exc:  # noqa: BLE001
            logger.error("Failed to process %s: %s", competitor["name"], exc)
    logger.info("Scheduled job: scrape and process complete.")


def job_market_signals() -> None:
    """Daily job: re-check competitor pricing pages and job boards."""
    from modules.settings_store import competitors
    from ingestion.run_signals import check_competitor

    logger.info("Scheduled job: checking pricing pages and job boards ...")
    for competitor in competitors():
        try:
            report = check_competitor(competitor)
            for error in report["errors"]:
                logger.warning("[%s] %s", competitor["name"], error)
        except Exception as exc:  # noqa: BLE001 — one competitor must not stop the rest
            logger.error("Market signals failed for %s: %s", competitor["name"], exc)
    logger.info("Scheduled job: market signals complete.")


def job_check_alerts() -> None:
    """Daily job: detect trigger signals and send Slack messages for new ones only.

    Detections are stored in alert_history first, so an ongoing signal (a
    sentiment drop that lasts a week) is one alert and one message, not one a day.
    """
    from modules.settings_store import competitor_names
    from modules.alert_history import mark_notified, pending_notifications, record_alerts
    from modules.trigger_alerts import check_triggers, generate_outreach, send_slack_alert

    logger.info("Scheduled job: checking alert triggers for %d competitors...", len(competitor_names()))
    alerts = check_triggers(competitor_names())
    rows = record_alerts(alerts)
    # Without a webhook nothing is sent, so nothing may be marked as notified —
    # otherwise configuring Slack later would never deliver these.
    webhook_set = bool(os.getenv("SLACK_WEBHOOK_URL"))
    to_send = {r["id"] for r in pending_notifications(rows)} if webhook_set else set()

    delivered: list[int] = []
    for alert, row in zip(alerts, rows):
        if row["id"] not in to_send:
            continue
        try:
            alert.outreach_draft = generate_outreach(alert, llm=False)
            send_slack_alert(alert)
            delivered.append(row["id"])
        except Exception as exc:  # noqa: BLE001 — one bad webhook call must not drop the rest
            logger.error(
                "Could not deliver alert %s / %s: %s",
                alert.competitor, alert.trigger_type, exc,
            )
    mark_notified(delivered)

    logger.info(
        "Scheduled job: %d alert(s) detected, %d new, %d sent to Slack.",
        len(alerts), sum(r["is_new"] for r in rows), len(delivered),
    )


def job_send_digest() -> None:
    """Weekly job: generate the intelligence digest and email the week's alerts."""
    from modules.settings_store import competitor_names
    from modules.digest_generator import generate_digest
    from modules.trigger_alerts import check_triggers

    logger.info("Scheduled job: generating weekly intelligence digest ...")
    try:
        digest = generate_digest(competitor_names())
        logger.info("Digest generated: %s", digest.get("generated_at", ""))
    except Exception as exc:  # noqa: BLE001
        logger.error("Digest generation failed: %s", exc)
        return

    to_email = os.getenv("DIGEST_EMAIL", "")
    if to_email:
        from outputs.email_digest import send_weekly_digest

        # The email body is built from the alert list — sending it empty made
        # every weekly email read "No alerts detected this week".
        send_weekly_digest(
            alerts=check_triggers(competitor_names()),
            leads_df=None,
            to_email=to_email,
        )

    logger.info("Scheduled job: digest complete.")


_scheduler_started = False


def start_scheduler() -> None:
    """Start the APScheduler BackgroundScheduler with all recurring jobs.

    Called from the FastAPI lifespan when ENABLE_SCHEDULER=true. Never starts
    when DEMO_MODE is 'true'. A module-level boolean guards against
    double-initialisation on repeated calls.
    """
    global _scheduler_started

    if os.getenv("DEMO_MODE", "false").lower() == "true":
        logger.info("DEMO_MODE=true — APScheduler not started.")
        return

    if _scheduler_started:
        return

    from apscheduler.schedulers.background import BackgroundScheduler  # type: ignore[import]

    scheduler = BackgroundScheduler()
    scheduler.add_job(job_scrape_and_process, "cron", hour=2, minute=0, id="daily_scrape")
    scheduler.add_job(job_market_signals, "cron", hour=2, minute=40, id="daily_market_signals")
    scheduler.add_job(job_check_alerts, "cron", hour=3, minute=0, id="daily_alerts")
    scheduler.add_job(job_send_digest, "cron", day_of_week="mon", hour=7, minute=0, id="weekly_digest")
    scheduler.start()

    _scheduler_started = True
    logger.info(
        "APScheduler started: daily_scrape@02:00, daily_market_signals@02:40, "
        "daily_alerts@03:00, weekly_digest@Mon07:00."
    )
