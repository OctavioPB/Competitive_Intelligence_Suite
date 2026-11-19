"""Read reviews from schema.org JSON-LD embedded in review-site pages.

Review sites publish ``Review`` objects as JSON-LD for search engines. Reading
those is sturdier than CSS selectors, which break with every redesign.
"""

from __future__ import annotations

import json
from typing import Any, Iterator

from bs4 import BeautifulSoup


def _walk(node: Any) -> Iterator[dict]:
    if isinstance(node, dict):
        yield node
        for value in node.values():
            yield from _walk(value)
    elif isinstance(node, list):
        for item in node:
            yield from _walk(item)


def _is_review(node: dict) -> bool:
    kind = node.get("@type")
    kinds = kind if isinstance(kind, list) else [kind]
    return "Review" in kinds


def _text(node: dict) -> str:
    parts = [str(node.get(k) or "").strip() for k in ("name", "reviewBody", "description")]
    title, body = parts[0], parts[1] or parts[2]
    if title and body and not body.startswith(title):
        return f"{title}. {body}"
    return body or title


def _rating(node: dict) -> float | None:
    rating = node.get("reviewRating") or {}
    value = rating.get("ratingValue") if isinstance(rating, dict) else rating
    try:
        value = float(value)
    except (TypeError, ValueError):
        return None
    best = rating.get("bestRating") if isinstance(rating, dict) else None
    try:
        best = float(best) if best is not None else 5.0
    except (TypeError, ValueError):
        best = 5.0
    return round(value * 5.0 / best, 2) if best and best != 5.0 else value


def _author(node: dict) -> str:
    author = node.get("author")
    if isinstance(author, list):
        author = author[0] if author else None
    if isinstance(author, dict):
        return str(author.get("name") or "")
    return str(author or "")


def jsonld_reviews(html: str) -> list[dict[str, Any]]:
    """All schema.org ``Review`` objects in the page as {text, rating, date, author}."""
    soup = BeautifulSoup(html, "html.parser")
    found: list[dict[str, Any]] = []
    seen: set[str] = set()
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string or script.get_text() or "")
        except (json.JSONDecodeError, TypeError):
            continue
        for node in _walk(data):
            if not _is_review(node):
                continue
            text = _text(node)
            if not text or text in seen:
                continue
            seen.add(text)
            found.append({
                "text": text,
                "rating": _rating(node),
                "date": str(node.get("datePublished") or "")[:10],
                "author": _author(node),
            })
    return found
