"""Fetch a competitor's open job postings from its public ATS job board.

Supported boards — all expose the same JSON their own careers pages use, no
login or API key needed:

* Greenhouse  https://boards-api.greenhouse.io/v1/boards/<board>/jobs
* Lever       https://api.lever.co/v0/postings/<board>
* Ashby       https://api.ashbyhq.com/posting-api/job-board/<board>
* Workday     https://<tenant>.wdN.myworkdayjobs.com/<site>  (paged, newest first)
"""

from __future__ import annotations

import logging
import re
import time
from datetime import date, datetime, timedelta, timezone
from typing import Any, Callable
from urllib.parse import urlparse

import requests

from config import CareersConfig
from ingestion.browser import USER_AGENT
from ingestion.scraper_g2 import ScrapingError

logger = logging.getLogger(__name__)

_HEADERS = {"User-Agent": USER_AGENT, "Accept": "application/json"}
_TIMEOUT = 30
_WORKDAY_PAGE = 20              # the largest page Workday's job search accepts
_WORKDAY_MAX_PAGES = 120        # hard stop: 2,400 postings
_WORKDAY_DELAY = 0.25

Posting = dict[str, Any]        # external_id, title, department, location, url, posted_date


def _iso_day(value: str | int | float | None) -> str | None:
    """ISO timestamp / epoch-ms → YYYY-MM-DD (None when missing or unparseable)."""
    if value in (None, ""):
        return None
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(value / 1000, tz=timezone.utc).date().isoformat()
    text = str(value)
    return text[:10] if re.match(r"\d{4}-\d{2}-\d{2}", text) else None


def _get_json(url: str, **params: Any) -> Any:
    try:
        resp = requests.get(url, params=params or None, headers=_HEADERS, timeout=_TIMEOUT)
    except requests.RequestException as exc:
        raise ScrapingError(f"job board request failed: {exc}") from exc
    if resp.status_code == 404:
        raise ScrapingError(f"job board not found ({url})")
    if resp.status_code != 200:
        raise ScrapingError(f"job board returned HTTP {resp.status_code} ({url})")
    return resp.json()


# ── Providers ─────────────────────────────────────────────────────────────────


def _greenhouse(board: str, **_: Any) -> list[Posting]:
    data = _get_json(f"https://boards-api.greenhouse.io/v1/boards/{board}/jobs", content="true")
    return [
        {
            "external_id": str(job["id"]),
            "title": job.get("title", "").strip(),
            "department": ", ".join(d["name"] for d in job.get("departments", []) if d.get("name")) or None,
            "location": (job.get("location") or {}).get("name"),
            "url": job.get("absolute_url"),
            "posted_date": _iso_day(job.get("first_published") or job.get("updated_at")),
        }
        for job in data.get("jobs", [])
    ]


def _lever(board: str, **_: Any) -> list[Posting]:
    data = _get_json(f"https://api.lever.co/v0/postings/{board}", mode="json")
    postings = []
    for job in data:
        cats = job.get("categories") or {}
        dept = " / ".join(x for x in (cats.get("department"), cats.get("team")) if x)
        postings.append({
            "external_id": str(job["id"]),
            "title": job.get("text", "").strip(),
            "department": dept or None,
            "location": cats.get("location"),
            "url": job.get("hostedUrl"),
            "posted_date": _iso_day(job.get("createdAt")),
        })
    return postings


def _ashby(board: str, **_: Any) -> list[Posting]:
    data = _get_json(f"https://api.ashbyhq.com/posting-api/job-board/{board}")
    postings = []
    for job in data.get("jobs", []):
        dept = " / ".join(x for x in (job.get("department"), job.get("team")) if x)
        postings.append({
            "external_id": str(job["id"]),
            "title": job.get("title", "").strip(),
            "department": dept or None,
            "location": job.get("location"),
            "url": job.get("jobUrl"),
            "posted_date": _iso_day(job.get("publishedAt")),
        })
    return postings


_WORKDAY_AGE = re.compile(r"posted\s+(today|yesterday|(\d+)\+?\s+days?\s+ago)", re.I)


def workday_posted_date(text: str, today: date) -> tuple[str | None, bool]:
    """Parse Workday's "Posted 3 Days Ago" → (YYYY-MM-DD, is_exact).

    "Posted 30+ Days Ago" is not exact: the real date is somewhere earlier.
    """
    m = _WORKDAY_AGE.search(text or "")
    if not m:
        return None, False
    word = m.group(1).lower()
    if word == "today":
        return today.isoformat(), True
    if word == "yesterday":
        return (today - timedelta(days=1)).isoformat(), True
    days = int(m.group(2))
    return (today - timedelta(days=days)).isoformat(), "+" not in m.group(0)


def _workday(board: str, *, max_age_days: int = 30, today: date | None = None, **_: Any) -> list[Posting]:
    """Workday lists newest first, so paging stops at the first posting older
    than ``max_age_days`` — older roles are irrelevant to hiring *signals*."""
    today = today or date.today()
    parsed = urlparse(board)
    tenant = parsed.netloc.split(".")[0]
    site = parsed.path.strip("/").split("/")[-1]
    if not tenant or not site:
        raise ScrapingError(f"Workday board must look like https://<tenant>.wdN.myworkdayjobs.com/<site>: {board}")
    api = f"{parsed.scheme}://{parsed.netloc}/wday/cxs/{tenant}/{site}/jobs"
    cutoff = (today - timedelta(days=max_age_days)).isoformat()

    postings: list[Posting] = []
    for page in range(_WORKDAY_MAX_PAGES):
        body = {"appliedFacets": {}, "limit": _WORKDAY_PAGE, "offset": page * _WORKDAY_PAGE, "searchText": ""}
        try:
            resp = requests.post(api, json=body, headers=_HEADERS, timeout=_TIMEOUT)
        except requests.RequestException as exc:
            raise ScrapingError(f"Workday request failed: {exc}") from exc
        if resp.status_code != 200:
            if page == 0:
                raise ScrapingError(f"Workday returned HTTP {resp.status_code} ({api})")
            logger.warning("Workday returned HTTP %s at offset %d — stopping.", resp.status_code, page * _WORKDAY_PAGE)
            break

        batch = resp.json().get("jobPostings", [])
        if not batch:
            break
        too_old = False
        for job in batch:
            posted, exact = workday_posted_date(job.get("postedOn", ""), today)
            if posted is None or not exact or posted < cutoff:
                too_old = True
                break
            path = job.get("externalPath", "")
            ids = job.get("bulletFields") or []
            postings.append({
                "external_id": str(ids[0] if ids else path),
                "title": job.get("title", "").strip(),
                "department": None,     # not exposed in the search listing
                "location": job.get("locationsText"),
                "url": f"{board.rstrip('/')}{path}" if path else None,
                "posted_date": posted,
            })
        if too_old:
            break
        time.sleep(_WORKDAY_DELAY)
    return postings


PROVIDERS: dict[str, Callable[..., list[Posting]]] = {
    "greenhouse": _greenhouse,
    "lever": _lever,
    "ashby": _ashby,
    "workday": _workday,
}


def fetch_postings(careers: CareersConfig, **options: Any) -> list[Posting]:
    """Fetch open postings from the configured board.

    Raises:
        ScrapingError: Unknown provider, board unreachable, or zero postings.
    """
    provider = careers["provider"].lower()
    fetch = PROVIDERS.get(provider)
    if fetch is None:
        raise ScrapingError(f"Unsupported job board provider '{provider}' (use one of {sorted(PROVIDERS)})")
    postings = [p for p in fetch(careers["board"], **options) if p["title"]]
    if not postings:
        raise ScrapingError(f"{provider} board '{careers['board']}' returned no postings")
    logger.info("%s: fetched %d postings from %s", provider, len(postings), careers["board"])
    return postings
