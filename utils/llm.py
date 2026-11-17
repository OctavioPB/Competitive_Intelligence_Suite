"""Shared LLM utilities: client, retry decorator, call wrapper and JSON parsing."""

import functools
import json
import logging
import os
import time
from typing import Callable, TypeVar

import anthropic

logger = logging.getLogger(__name__)

F = TypeVar("F", bound=Callable)

# Single place to change the model for every module (override with ANTHROPIC_MODEL).
MODEL = os.getenv("ANTHROPIC_MODEL") or "claude-sonnet-4-6"

_MAX_RETRIES = 3
_BASE_DELAY_SECONDS = 1.0
_BACKOFF_FACTOR = 2.0

# Only errors that can succeed on a second attempt. 4xx such as a bad API key or
# an invalid request fail identically every time, so they are raised immediately.
_TRANSIENT_ERRORS = (
    anthropic.RateLimitError,
    anthropic.APIConnectionError,
    anthropic.InternalServerError,
)

REPAIR_SYSTEM_PROMPT = """\
The following text should be valid JSON but has a syntax error. \
Return ONLY the corrected JSON — no explanation, no markdown fences. \
The response must start with { and end with }.
"""


class LLMConfigError(RuntimeError):
    """Raised when the Claude API cannot be used because it is not configured."""


def retry_with_backoff(func: F) -> F:
    """Decorator: retry an LLM call with exponential backoff on transient errors.

    Retries rate limits, connection failures and 5xx responses. Gives up after
    _MAX_RETRIES attempts and re-raises the last exception.

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
            except _TRANSIENT_ERRORS as exc:
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


@functools.lru_cache(maxsize=1)
def get_client() -> anthropic.Anthropic:
    """Return the process-wide Anthropic client (reads ANTHROPIC_API_KEY from env).

    Cached so every call reuses one HTTP connection pool. The SDK's own retry
    layer is disabled because retry_with_backoff already handles retries.

    Returns:
        anthropic.Anthropic instance.
    """
    if not (os.getenv("ANTHROPIC_API_KEY") or os.getenv("ANTHROPIC_AUTH_TOKEN")):
        raise LLMConfigError(
            "ANTHROPIC_API_KEY is not set — add it to .env to use the AI-powered modules."
        )
    return anthropic.Anthropic(max_retries=0)


@retry_with_backoff
def call_claude(
    system: str | None,
    user: str,
    *,
    max_tokens: int = 2048,
    label: str = "LLM",
) -> str:
    """Make a single Claude API call and return the text of the response.

    Args:
        system: System prompt, or None to send no system prompt.
        user: User message content.
        max_tokens: Output token cap.
        label: Short name used in the token-usage log line.

    Returns:
        Raw text of the first content block.
    """
    kwargs = {"system": system} if system else {}
    response = get_client().messages.create(
        model=MODEL,
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": user}],
        **kwargs,
    )
    logger.info(
        "%s token usage: %d in + %d out",
        label,
        response.usage.input_tokens,
        response.usage.output_tokens,
    )
    if response.stop_reason == "max_tokens":
        logger.warning("%s response hit max_tokens=%d and was truncated.", label, max_tokens)
    return response.content[0].text


def strip_code_fences(text: str) -> str:
    """Remove a wrapping ```…``` markdown fence that models sometimes emit."""
    text = text.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if len(lines) > 2:
            text = "\n".join(lines[1:-1])
    return text


def parse_json_object(
    raw: str,
    *,
    context: str,
    repair: Callable[[str], str] | None = None,
) -> dict:
    """Parse an LLM response as a JSON object, optionally with one repair attempt.

    Args:
        raw: Raw model output.
        context: Human-readable description for log and error messages.
        repair: Optional callable that receives the broken text and returns a
            corrected version (typically a second LLM call).

    Returns:
        Parsed dict.

    Raises:
        ValueError: If the text (and the repaired text, when repair is given)
            is not a valid JSON object.
    """
    text = strip_code_fences(raw)
    candidates = [lambda: text]
    if repair is not None:
        candidates.append(lambda: strip_code_fences(repair(text)))

    last_exc: Exception | None = None
    for attempt, get_text in enumerate(candidates):
        if attempt:
            logger.warning("%s: JSON parse failed — attempting repair.", context)
        try:
            data = json.loads(get_text())
        except json.JSONDecodeError as exc:
            last_exc = exc
            continue
        if isinstance(data, dict):
            return data
        last_exc = TypeError(f"expected a JSON object, got {type(data).__name__}")

    logger.error("%s: could not parse JSON. Raw: %.500s", context, raw)
    raise ValueError(f"Failed to parse {context} JSON") from last_exc
