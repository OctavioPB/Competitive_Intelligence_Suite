"""Extract the price points shown on a competitor pricing page.

A "price point" is one price with the words that give it meaning — the plan
name before it and the unit after it — e.g. ``"Professional: $90 /mo/seat"``.
Comparing the sets of price points between two checks tells us what changed
without being fooled by rotating banners, A/B copy or markup changes.
"""

from __future__ import annotations

import re

from bs4 import BeautifulSoup

from ingestion.browser import FetchError, fetch_html

_PRICE = re.compile(r"(?:US\$|C\$|A\$|\$|€|£)\s?\d[\d,]*(?:\.\d{1,2})?")
_CURRENCY_ONLY = re.compile(r"^(?:[A-Z]{0,3}\$|€|£|¥|円|kr|[A-Z]{3})$")
_NUMBER_ONLY = re.compile(r"^\d[\d,]*(?:\.\d{1,2})?$")
# Case-sensitive on purpose: "GBP/User/Month" is a unit, "Pro Suite" is a plan.
_UNIT = re.compile(r"^(?:(?i:/|per\b|a month|a year|billed)|[A-Z]{3}/)")
_CURRENCY_WORDS = {
    "kr", "円", "¥", "zł", "r$", "usd", "eur", "gbp", "jpy", "sek", "nok", "dkk",
    "chf", "aud", "cad", "inr", "brl", "mxn",
}
# "user/month", "/mo/seat", "(Billed annually)" — billing terms, not plan names.
_BILLING = re.compile(r"^\(|\b(?:billed|monthly|annually)\b|/\s*(?:mo|month|yr|year|user|seat)\b", re.I)
_SYMBOL_GAP = re.compile(r"((?:US|C|A)?\$|€|£)\s+(?=\d)")

# Words that sit next to prices but say nothing about which plan they belong to.
_FILLER = {
    "starts at", "starting at", "starting from", "from", "only", "buy now", "loading",
    "try it free", "try for free", "start free trial", "talk to sales", "contact us",
    "contact sales", "billing period", "learn more", "get started", "most popular",
    "recommended", "best value", "save", "monthly", "annually", "yearly", "per month",
    "opens in new window", "compare plans", "see all features", "free trial",
}
_LABEL_MAX = 40
_SENTENCE = 60          # longer price lines are kept whole: they carry their own context
_LOOKBACK = 30          # raw lines to walk back looking for the plan name…
_TEXT_BUDGET = 2        # …but give up after this many lines of real text that are not one
_MIN_POINTS = 2


def visible_lines(html: str) -> list[str]:
    """Text lines a visitor sees, whitespace-normalised, empties dropped."""
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript", "svg", "template", "iframe"]):
        tag.decompose()
    lines = [re.sub(r"\s+", " ", ln).strip() for ln in soup.get_text("\n").splitlines()]
    lines = [ln for ln in lines if ln]

    # Rejoin prices split across elements: "US$" / "14" → "US$ 14".
    merged: list[str] = []
    i = 0
    while i < len(lines):
        if i + 1 < len(lines) and _CURRENCY_ONLY.match(lines[i]) and _NUMBER_ONLY.match(lines[i + 1]):
            merged.append(f"{lines[i]} {lines[i + 1]}")
            i += 2
            continue
        merged.append(lines[i])
        i += 1
    return merged


def _is_noise(line: str) -> bool:
    """Lines between a plan name and its price that carry no meaning of their own."""
    low = line.lower().strip(" :*")
    return (
        bool(_PRICE.search(line))
        or bool(_CURRENCY_ONLY.match(line))
        or bool(_UNIT.match(line))
        or bool(_BILLING.search(line))
        or bool(_NUMBER_ONLY.match(line))
        or low in _FILLER
        or low in _CURRENCY_WORDS
        or not any(c.isalpha() for c in line)
    )


def _plan_label(lines: list[str], i: int) -> str:
    """Nearest short line above ``lines[i]`` that reads like a plan or product name."""
    text_seen = 0
    for j in range(i - 1, max(-1, i - 1 - _LOOKBACK), -1):
        line = lines[j]
        if _is_noise(line):
            continue
        if 2 <= len(line) <= _LABEL_MAX:
            return line
        text_seen += 1          # a description or feature bullet
        if text_seen > _TEXT_BUDGET:
            break
    return ""


def extract_price_points(html: str) -> list[str]:
    """Return the distinct price points on a pricing page, in page order."""
    lines = visible_lines(html)
    points: list[str] = []
    seen: set[str] = set()

    for i, line in enumerate(lines):
        if not _PRICE.search(line):
            continue
        if len(line) > _SENTENCE:
            point = line[:160]
        else:
            label = _plan_label(lines, i)
            unit = lines[i + 1] if i + 1 < len(lines) and _UNIT.match(lines[i + 1]) else ""
            if len(unit) > _LABEL_MAX:
                unit = ""
            point = f"{label}: {line} {unit}".strip(" :") if label else f"{line} {unit}".strip()
        point = _SYMBOL_GAP.sub(r"\1", re.sub(r"\s+", " ", point))
        if point not in seen:
            seen.add(point)
            points.append(point)
    return points


def fetch_price_points(url: str) -> tuple[list[str], bool]:
    """Fetch a pricing page and extract its price points.

    Returns:
        (price_points, rendered) — rendered is True when headless Chromium was needed.

    Raises:
        FetchError: The page could not be fetched, was blocked, or showed no prices.
    """
    page = fetch_html(url, lambda html: len(extract_price_points(html)) >= _MIN_POINTS)
    return extract_price_points(page.html), page.rendered


__all__ = ["FetchError", "extract_price_points", "fetch_price_points", "visible_lines"]
