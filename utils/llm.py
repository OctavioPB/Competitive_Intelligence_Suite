"""Shared LLM utilities: retry decorator and Anthropic client factory."""

import functools
import logging
import time
from typing import Callable, TypeVar

import anthropic

logger = logging.getLogger(__name__)

F = TypeVar("F", bound=Callable)

_MAX_RETRIES = 3
_BASE_DELAY_SECONDS = 1.0
_BACKOFF_FACTOR = 2.0


def retry_with_backoff(func: F) -> F:
    """Decorator: retry an LLM call with exponential backoff on transient errors.

    Catches anthropic.RateLimitError and anthropic.APIStatusError (5xx).
    Gives up after _MAX_RETRIES attempts and re-raises the last exception.

    Args:
        func: Callable that makes an Anthropic API call.

    Returns:
        Wrapped callable with retry logic.
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        delay = _BASE_DELAY_SECONDS
        for attempt in range(1, _MAX_RETRIES + 1):
            try:
                return func(*args, **kwargs)
            except (anthropic.RateLimitError, anthropic.APIStatusError) as exc:
                if attempt == _MAX_RETRIES:
                    logger.error(
                        "LLM call failed after %d attempts: %s", _MAX_RETRIES, exc
                    )
                    raise
                logger.warning(
                    "LLM call attempt %d/%d failed (%s). Retrying in %.1fs ...",
                    attempt,
                    _MAX_RETRIES,
                    type(exc).__name__,
                    delay,
                )
                time.sleep(delay)
                delay *= _BACKOFF_FACTOR

    return wrapper  # type: ignore[return-value]


def get_client() -> anthropic.Anthropic:
    """Return a configured Anthropic client (reads ANTHROPIC_API_KEY from env).

    Returns:
        anthropic.Anthropic instance.
    """
    return anthropic.Anthropic()
