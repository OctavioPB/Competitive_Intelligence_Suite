"""Market signals: competitor pricing-page changes and hiring patterns.

Two kinds of evidence that do not come from reviews:

* **Pricing changes.** Each check of a pricing page stores the extracted price
  points. A new version is only written when they differ, together with what
  was added and removed — "Professional: $90 → $100 /mo/seat" is one of the
  best moments to reach out to that competitor's customers.
* **Hiring.** Open roles from the competitor's job board are classified by
  function. A wave of support hires says support is under strain; engineers
  hired for integrations say where the product is going (or hurting).

Storage lives in ``pricing_snapshots`` and ``job_postings``; Trigger Alerts
reads :func:`pricing_change_signal` and :func:`hiring_signals`.
"""

from __future__ import annotations

import hashlib
import json
import re
from contextlib import closing
from datetime import date
from typing import Any

from database.db import get_conn, query_df

# ── Tunables ──────────────────────────────────────────────────────────────────

PRICING_ALERT_DAYS = 14        # a price change stays "news" for two weeks
HIRING_WINDOW_DAYS = 30
SUPPORT_MIN_ROLES = 5          # support wave: at least this many new support roles…
SUPPORT_MIN_SHARE = 0.25       # …making up at least this share of all new roles
INTEGRATION_MIN_ROLES = 3      # integration push: this many new integration engineering roles

# ── Role classification ───────────────────────────────────────────────────────

CATEGORY_LABELS: dict[str, str] = {
    "support": "Support & Success",
    "engineering": "Engineering",
    "sales": "Sales",
    "product": "Product & Design",
    "marketing": "Marketing",
    "other": "Other",
}

# Checked in order — the first match wins. Sales engineers are pre-sales, so
# "sales" runs before "engineering"; "Support Engineer" is support, so that runs first.
_CATEGORY_RULES: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("support", re.compile(
        r"\b(support|customer success|success (?:manager|architect|engineer|specialist|partner)|customer service|customer care|customer experience|customer risk"
        r"|help ?desk|service desk|technical account manager|scaled cs|csm|onboarding|implementation specialist)\b")),
    ("sales", re.compile(
        r"\b(sales|account executive|account manager|account management|renewals?|business development"
        r"|bdr|sdr|solutions? engineer|solutions? architect|solutions? consultant|pre-?sales"
        r"|partner manager|alliances?|channel|revenue)\b")),
    ("engineering", re.compile(
        r"\b(engineer(ing)?|developer|software|sre|site reliability|devops|architect|data scientist"
        r"|machine learning|ml|ai research|security|qa|quality assurance|infrastructure|platform)\b")),
    # Before "product": a Product Marketing Manager is marketing.
    ("marketing", re.compile(
        r"\b(marketing|content|brand|communications|seo|demand gen|growth|events|social media|copywriter)\b")),
    ("product", re.compile(r"\b(product|designer|design|ux|ui|user research|researcher)\b")),
)

_INTEGRATION = re.compile(
    r"\b(integrations?|apis?|connectors?|ecosystem|marketplace|app partners?|interoperab\w*"
    r"|data sync|webhooks?|sdks?|extensibility|mulesoft)\b"
)
# "Integration" that is not about the product: post-acquisition IT, internal tooling.
_NOT_PRODUCT = re.compile(r"(m&a|merger|acquisition|\binternal\b|corporate it|business systems)")


# Product names that contain function words: "Software Engineer, Sales Cloud" is
# engineering, "Product Manager, Marketing Hub" is product.
_PRODUCT_NAMES = re.compile(
    r"\b(sales|service|marketing|commerce|data|experience|revenue|analytics|success|content|operations)"
    r"\s+(cloud|hub)\b"
)


def classify_role(title: str, department: str | None = None) -> tuple[str, bool]:
    """Return (category, is_integration_role) for a job title (+ department)."""
    text = _PRODUCT_NAMES.sub(" ", f"{title} {department or ''}".lower())
    category = next((cat for cat, rx in _CATEGORY_RULES if rx.search(text)), "other")
    integration = (
        category in ("engineering", "product")
        and bool(_INTEGRATION.search(text))
        and not _NOT_PRODUCT.search(text)
    )
    return category, integration


# ── Pricing storage ───────────────────────────────────────────────────────────


def _hash_points(points: list[str]) -> str:
    return hashlib.sha256("\n".join(sorted(set(points))).encode("utf-8")).hexdigest()


def record_pricing_check(
    competitor: str,
    url: str,
    points: list[str],
    checked_on: date | None = None,
    *,
    is_synthetic: bool = False,
) -> dict[str, Any]:
    """Store the result of one pricing-page check.

    Returns:
        {"status": "first" | "unchanged" | "changed", "added": [...], "removed": [...]}
    """
    day = (checked_on or date.today()).isoformat()
    digest = _hash_points(points)
    with closing(get_conn()) as conn, conn:
        latest = conn.execute(
            "SELECT id, content_hash, price_points FROM pricing_snapshots "
            "WHERE competitor_name = ? AND url = ? ORDER BY first_seen DESC, id DESC LIMIT 1",
            (competitor, url),
        ).fetchone()

        if latest is not None and latest["content_hash"] == digest:
            conn.execute("UPDATE pricing_snapshots SET last_seen = ? WHERE id = ?", (day, latest["id"]))
            return {"status": "unchanged", "added": [], "removed": []}

        added = removed = None
        if latest is not None:
            before = json.loads(latest["price_points"])
            added = [p for p in points if p not in set(before)]
            removed = [p for p in before if p not in set(points)]
        conn.execute(
            """
            INSERT INTO pricing_snapshots
                (competitor_name, url, first_seen, last_seen, content_hash, price_points,
                 added, removed, is_synthetic)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                competitor, url, day, day, digest, json.dumps(points),
                None if added is None else json.dumps(added),
                None if removed is None else json.dumps(removed),
                int(is_synthetic),
            ),
        )
    if latest is None:
        return {"status": "first", "added": [], "removed": []}
    return {"status": "changed", "added": added, "removed": removed}


def _split_label(point: str) -> tuple[str, str]:
    label, sep, rest = point.partition(": ")
    return (label, rest) if sep else ("", point)


def describe_changes(added: list[str], removed: list[str]) -> list[str]:
    """Human-readable change lines; a removed and an added price with the same
    plan label are shown as one move: ``"Professional: $90 /mo/seat → $100 /mo/seat"``."""
    added_by_label: dict[str, list[str]] = {}
    for point in added:
        label, rest = _split_label(point)
        added_by_label.setdefault(label, []).append(rest)

    lines: list[str] = []
    for point in removed:
        label, before = _split_label(point)
        if label and added_by_label.get(label):
            after = added_by_label[label].pop(0)
            lines.append(f"{label}: {before} → {after}")
        else:
            lines.append(f"Removed {point}")
    for label, rests in added_by_label.items():
        lines.extend(f"New {label + ': ' if label else ''}{rest}" for rest in rests)
    return lines


# ── Job storage ───────────────────────────────────────────────────────────────


def record_job_postings(
    competitor: str,
    source: str,
    postings: list[dict[str, Any]],
    crawled_on: date | None = None,
    *,
    is_synthetic: bool = False,
) -> dict[str, int]:
    """Upsert one crawl of a job board. Roles absent from this crawl keep their
    old ``last_seen`` and therefore count as closed.

    Returns:
        {"seen": n, "new": n}
    """
    day = (crawled_on or date.today()).isoformat()
    new = 0
    with closing(get_conn()) as conn, conn:
        for p in postings:
            category, integration = classify_role(p["title"], p.get("department"))
            cur = conn.execute(
                """
                UPDATE job_postings
                SET title = ?, department = ?, location = ?, url = ?, category = ?, integration = ?,
                    posted_date = COALESCE(?, posted_date), last_seen = ?
                WHERE competitor_name = ? AND source = ? AND external_id = ?
                """,
                (p["title"], p.get("department"), p.get("location"), p.get("url"), category,
                 int(integration), p.get("posted_date"), day, competitor, source, p["external_id"]),
            )
            if cur.rowcount == 0:
                conn.execute(
                    """
                    INSERT INTO job_postings
                        (competitor_name, source, external_id, title, department, location, url,
                         category, integration, posted_date, first_seen, last_seen, is_synthetic)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (competitor, source, p["external_id"], p["title"], p.get("department"),
                     p.get("location"), p.get("url"), category, int(integration),
                     p.get("posted_date"), day, day, int(is_synthetic)),
                )
                new += 1
    return {"seen": len(postings), "new": new}


# ── Read models (API + alerts) ────────────────────────────────────────────────


def _loads(value: Any) -> list[str]:
    return json.loads(value) if isinstance(value, str) and value else []


def get_pricing_overview(competitor: str) -> dict[str, Any]:
    """Current price points and the latest change for each monitored pricing page."""
    df = query_df(
        "SELECT * FROM pricing_snapshots WHERE competitor_name = ? ORDER BY url, first_seen, id",
        (competitor,),
    )
    pages = []
    for url, group in df.groupby("url", sort=False):
        rows = group.to_dict("records")
        current = rows[-1]
        changes = [r for r in rows if r["added"] is not None or r["removed"] is not None]
        last_change = None
        if changes:
            ch = changes[-1]
            added, removed = _loads(ch["added"]), _loads(ch["removed"])
            last_change = {
                "date": ch["first_seen"],
                "changes": describe_changes(added, removed),
                "added": added,
                "removed": removed,
            }
        pages.append({
            "url": url,
            "last_checked": current["last_seen"],
            "monitored_since": rows[0]["first_seen"],
            "versions": len(rows),
            "price_points": _loads(current["price_points"]),
            "last_change": last_change,
            "is_synthetic": bool(current["is_synthetic"]),
        })
    return {"competitor": competitor, "pages": pages}


_OPEN_ROLES_SQL = """
    SELECT title, department, location, url, category, integration, posted_date, first_seen,
           is_synthetic, source,
           COALESCE(posted_date, first_seen) >= date(:anchor, :window) AS is_new
    FROM job_postings
    WHERE competitor_name = :competitor AND last_seen = :anchor
    ORDER BY COALESCE(posted_date, first_seen) DESC, title
"""


def _latest_crawl(competitor: str) -> str | None:
    df = query_df("SELECT MAX(last_seen) AS d FROM job_postings WHERE competitor_name = ?", (competitor,))
    value = df["d"].iloc[0] if not df.empty else None
    return value if isinstance(value, str) else None


def get_hiring_overview(competitor: str) -> dict[str, Any]:
    """Open roles by function, with what was posted in the last 30 days."""
    anchor = _latest_crawl(competitor)
    empty = {
        "competitor": competitor, "crawled_on": None, "source": None, "window_days": HIRING_WINDOW_DAYS,
        "open_roles": 0, "new_roles": 0, "by_category": [], "integration_new": 0, "integration_roles": [],
        "recent_roles": [], "is_synthetic": False,
    }
    if anchor is None:
        return empty

    df = query_df(_OPEN_ROLES_SQL, {
        "competitor": competitor, "anchor": anchor, "window": f"-{HIRING_WINDOW_DAYS} days",
    })
    if df.empty:
        return {**empty, "crawled_on": anchor}

    new = df[df["is_new"] == 1]
    by_category = [
        {
            "category": cat,
            "label": label,
            "open": int((df["category"] == cat).sum()),
            "new": int((new["category"] == cat).sum()),
        }
        for cat, label in CATEGORY_LABELS.items()
    ]
    by_category = [c for c in by_category if c["open"]]
    by_category.sort(key=lambda c: (-c["new"], -c["open"]))

    def roles(frame) -> list[dict[str, Any]]:
        return [
            {
                "title": r.title, "department": r.department, "location": r.location, "url": r.url,
                "category": r.category, "posted_date": r.posted_date or r.first_seen,
            }
            for r in frame.itertuples()
        ]

    return {
        "competitor": competitor,
        "crawled_on": anchor,
        "source": str(df["source"].iloc[0]),
        "window_days": HIRING_WINDOW_DAYS,
        "open_roles": int(len(df)),
        "new_roles": int(len(new)),
        "by_category": by_category,
        "integration_new": int((new["integration"] == 1).sum()),
        "integration_roles": roles(new[new["integration"] == 1])[:12],
        "recent_roles": roles(new)[:25],
        "is_synthetic": bool(df["is_synthetic"].max()),
    }


# ── Signals for Trigger Alerts ────────────────────────────────────────────────


def _short_url(url: str) -> str:
    return re.sub(r"^https?://(www\.)?", "", url).rstrip("/")


def latest_pricing_change(competitor: str) -> dict[str, Any] | None:
    """The most recent pricing-page change within the last 14 days (counted back
    from the latest check, so stored sample data works too), or None.

    Returns:
        {"url", "date", "changes": [...], "evidence"}
    """
    df = query_df(
        """
        SELECT url, first_seen, added, removed
        FROM pricing_snapshots
        WHERE competitor_name = ?
          AND (added IS NOT NULL OR removed IS NOT NULL)
          AND first_seen >= date(
                (SELECT MAX(last_seen) FROM pricing_snapshots WHERE competitor_name = ?), ?)
        ORDER BY first_seen DESC, id DESC
        """,
        (competitor, competitor, f"-{PRICING_ALERT_DAYS} days"),
    )
    for row in df.itertuples():
        changes = describe_changes(_loads(row.added), _loads(row.removed))
        if not changes:
            continue
        shown = "; ".join(changes[:3]) + (f"; +{len(changes) - 3} more" if len(changes) > 3 else "")
        return {
            "url": row.url,
            "date": row.first_seen,
            "changes": changes,
            "evidence": f"Pricing page changed on {row.first_seen} ({_short_url(row.url)}): {shown}",
        }
    return None


def pricing_change_signal(competitor: str) -> str | None:
    """Evidence text for :func:`latest_pricing_change`, or None."""
    change = latest_pricing_change(competitor)
    return change["evidence"] if change else None


def hiring_signal_items(competitor: str) -> list[tuple[str, str]]:
    """(kind, evidence) for a support-hiring wave ("support") and/or an
    integration push ("integrations")."""
    overview = get_hiring_overview(competitor)
    new_total = overview["new_roles"]
    if not new_total:
        return []

    window = overview["window_days"]
    found: list[tuple[str, str]] = []
    support = next((c["new"] for c in overview["by_category"] if c["category"] == "support"), 0)
    if support >= SUPPORT_MIN_ROLES and support / new_total >= SUPPORT_MIN_SHARE:
        found.append(("support", (
            f"{support} of {new_total} roles opened in the last {window} days are customer support / "
            f"success ({support / new_total:.0%}) — a sign their support is under strain."
        )))

    n_integration = overview["integration_new"]
    if n_integration >= INTEGRATION_MIN_ROLES:
        titles = "; ".join(r["title"] for r in overview["integration_roles"][:3])
        found.append(("integrations", (
            f"{n_integration} engineering roles on integrations / APIs opened in the last "
            f"{window} days (e.g. {titles}) — they are investing where customers feel gaps."
        )))
    return found


def hiring_signals(competitor: str) -> list[str]:
    """Evidence texts for a support-hiring wave and/or an integration push."""
    return [evidence for _, evidence in hiring_signal_items(competitor)]
