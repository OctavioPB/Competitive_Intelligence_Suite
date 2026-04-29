"""Post structured messages to a Slack incoming webhook."""

import logging

import requests

logger = logging.getLogger(__name__)


def post_message(webhook_url: str, payload: dict) -> None:
    """POST a JSON payload to a Slack incoming webhook URL.

    Args:
        webhook_url: Full Slack webhook URL from SLACK_WEBHOOK_URL env var.
        payload: Slack Block Kit message dict.

    Raises:
        requests.HTTPError: If Slack returns a non-2xx response.
    """
    raise NotImplementedError("Implement in Sprint 5 — Day 13")
