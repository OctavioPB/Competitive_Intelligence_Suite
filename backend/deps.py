"""Helpers shared by the API routers."""

import math
from typing import Any

from fastapi import HTTPException

from config import COMPETITOR_NAMES


def known_competitor(name: str) -> str:
    """Return ``name`` if it is a configured competitor, else raise 404.

    Competitor names end up in SQL parameters, cache file names and LLM prompts,
    so every endpoint accepts only the names declared in config.COMPETITORS.
    """
    if name not in COMPETITOR_NAMES:
        raise HTTPException(
            status_code=404,
            detail=f"Unknown competitor '{name}'. Known: {', '.join(COMPETITOR_NAMES)}",
        )
    return name


def json_safe(value: Any) -> Any:
    """Convert NaN/inf floats to None — they are not valid JSON."""
    if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
        return None
    return value
