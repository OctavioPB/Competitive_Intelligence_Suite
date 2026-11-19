"""Fetch pages that need JavaScript, and recognise anti-bot walls.

Two tools for the scrapers:

* ``fetch_html`` — plain HTTP first, headless Chromium (Playwright) only when
  the static HTML lacks what the caller needs. Many pricing pages ship their
  content in the HTML; others (HubSpot) render it client-side.
* ``bot_wall`` — names the protection (DataDome, Cloudflare, Akamai…) when a
  site served a challenge instead of content, so callers can report *why* a
  source returned nothing instead of failing silently.

The browser is a normal headless Chromium. It deliberately does not try to
disguise automation: sites that block it (G2, Capterra) are reported as
blocked rather than worked around.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Callable

import requests

logger = logging.getLogger(__name__)

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/131.0.0.0 Safari/537.36"
)
_HEADERS = {"User-Agent": USER_AGENT, "Accept-Language": "en-US,en;q=0.9"}
_RENDER_SETTLE_MS = 6000

# Challenge scripts loaded from the protection vendor's own host.
_DATADOME_HOST = re.compile(r"//(?:[a-z0-9-]+\.)*captcha-delivery\.com\b")
_CLOUDFLARE_HOST = re.compile(r"//challenges\.cloudflare\.com\b")

# (name, test) pairs, checked in order. Each test sees status, lower-cased HTML and title.
_WALLS: tuple[tuple[str, Callable[[int, str, str], bool]], ...] = (
    ("DataDome", lambda s, h, t: bool(_DATADOME_HOST.search(h)) or ("datadome" in h and s in (401, 403))),
    ("Cloudflare", lambda s, h, t: t.startswith("just a moment") or bool(_CLOUDFLARE_HOST.search(h))
     or "cf-chl-" in h),
    ("Akamai", lambda s, h, t: t == "access denied" and "reference #" in h),
    ("PerimeterX", lambda s, h, t: "px-captcha" in h or ("perimeterx" in h and s in (401, 403))),
    ("captcha", lambda s, h, t: s in (401, 403, 429) and "captcha" in h),
)


class FetchError(Exception):
    """Raised when a page could not be fetched or only served an anti-bot wall."""


@dataclass
class Page:
    url: str
    status: int
    html: str
    title: str
    rendered: bool        # True when the HTML came from headless Chromium


def _title(html: str) -> str:
    m = re.search(r"<title[^>]*>(.*?)</title>", html, re.I | re.S)
    return re.sub(r"\s+", " ", m.group(1)).strip() if m else ""


def bot_wall(status: int, html: str, title: str = "") -> str | None:
    """Return the name of the anti-bot protection that served this page, if any."""
    low = html.lower()
    t = (title or _title(html)).lower()
    for name, test in _WALLS:
        if test(status, low, t):
            return name
    return None


def playwright_available() -> bool:
    try:
        import playwright.sync_api  # noqa: F401
    except ImportError:
        return False
    return True


def fetch_static(url: str, timeout: int = 20) -> Page:
    try:
        resp = requests.get(url, headers=_HEADERS, timeout=timeout)
    except requests.RequestException as exc:
        raise FetchError(f"request failed: {exc}") from exc
    return Page(url, resp.status_code, resp.text, _title(resp.text), rendered=False)


def render(url: str, wait_for: str | None = None, timeout_ms: int = 45_000) -> Page:
    """Load ``url`` in headless Chromium and return the rendered HTML.

    Args:
        wait_for: Optional CSS selector to wait for (up to the timeout) before
            reading the DOM; otherwise the page gets a fixed settle time.

    Raises:
        FetchError: Playwright or its browser is not installed, or navigation failed.
    """
    try:
        from playwright.sync_api import Error as PlaywrightError
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise FetchError(
            "Playwright is not installed (pip install playwright && playwright install chromium)"
        ) from exc

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            try:
                page = browser.new_page(user_agent=USER_AGENT, locale="en-US")
                resp = page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
                if wait_for:
                    try:
                        page.wait_for_selector(wait_for, timeout=timeout_ms // 3)
                    except PlaywrightError:
                        pass  # the caller inspects the HTML and decides
                else:
                    page.wait_for_timeout(_RENDER_SETTLE_MS)
                html = page.content()
                return Page(url, resp.status if resp else 0, html, page.title(), rendered=True)
            finally:
                browser.close()
    except PlaywrightError as exc:
        raise FetchError(f"headless browser failed: {exc}") from exc


def fetch_html(
    url: str,
    has_content: Callable[[str], bool],
    *,
    wait_for: str | None = None,
) -> Page:
    """Return the first version of ``url`` that ``has_content`` accepts.

    Tries plain HTTP, then — if Playwright is installed — headless Chromium.

    Raises:
        FetchError: Neither attempt produced usable content. The message names
            the anti-bot wall when one was detected.
    """
    reasons: list[str] = []
    attempts: list[Callable[[], Page]] = [lambda: fetch_static(url)]
    if playwright_available():
        attempts.append(lambda: render(url, wait_for=wait_for))
    else:
        reasons.append("headless browser unavailable (Playwright not installed)")

    for attempt in attempts:
        try:
            page = attempt()
        except FetchError as exc:
            reasons.append(str(exc))
            continue
        mode = "rendered" if page.rendered else "static"
        wall = bot_wall(page.status, page.html, page.title)
        if wall:
            reasons.append(f"{mode}: blocked by {wall} (HTTP {page.status})")
            continue
        if page.status == 200 and has_content(page.html):
            logger.debug("Fetched %s (%s)", url, mode)
            return page
        reasons.append(f"{mode}: HTTP {page.status}, no usable content")

    raise FetchError("; ".join(reasons))
