"""Win/loss: why deals against a competitor were won or lost, set against what
that competitor's own customers complain about.

Reps log each closed deal with a reason category. For a competitor, every
category gets two shares — of our deal reasons, and of the complaints in its
reviews (pain-point topics mapped to the same categories by keyword) — and a
reading of what the overlap means:

* lost on X, and their customers complain about X  → "contested": the weakness
  is real but our pitch on X is not landing; bring the review evidence.
* lost on X, reviews quiet about X                 → "their strength": compete elsewhere.
* won on X, and their customers complain about X   → "proven angle": keep leading with it.
* reviews complain about X, no deal mentions X     → "untapped": raise it in discovery.
"""

from __future__ import annotations

import re
from contextlib import closing
from datetime import date, datetime, timezone
from typing import Any

from database.db import get_conn, init_schema, query_rows

CATEGORIES: dict[str, str] = {
    "pricing": "Pricing & contract",
    "features": "Features & fit",
    "support": "Support & service",
    "ux": "Ease of use",
    "reliability": "Reliability & performance",
    "integrations": "Integrations & data",
    "other": "Other",
}

_KEYWORDS: dict[str, tuple[str, ...]] = {
    "pricing": ("price", "pricing", "cost", "expensive", "cheap", "tier", "licen", "contract", "renewal",
                "seat", "budget", "fee", "plan", "billing", "discount", "tco", "contact limit"),
    "support": ("support", "ticket", "response time", "help", "service", "account manager", "csm",
                "onboarding", "training"),
    "reliability": ("outage", "downtime", "bug", "crash", "slow", "performance", "reliab", "uptime",
                    "error", "data loss", "lag"),
    "integrations": ("integration", "api", "connector", "sync", "import", "export", "webhook", "erp",
                     "zapier", "data"),
    "ux": ("ui", "ux", "interface", "learning curve", "complex", "easy", "usab", "intuitive", "clunky",
           "navigation", "mobile"),
    "features": ("feature", "missing", "custom", "report", "dashboard", "automation", "workflow",
                 "analytics", "pipeline", "forecast", "email", "field"),
}

MIN_SHARE = 0.2          # a category "matters" from this share upwards
QUIET_SHARE = 0.1        # … and is "quiet" below this


class DealError(ValueError):
    """Invalid deal; the message says which field."""


def categorize(text: str) -> str:
    """Best category for a free-text reason or a pain-point topic label."""
    low = text.lower()
    scores = {
        cat: sum(1 for kw in words if re.search(rf"\b{re.escape(kw)}", low))
        for cat, words in _KEYWORDS.items()
    }
    best = max(scores, key=lambda c: scores[c])
    return best if scores[best] else "other"


# ── Deals ─────────────────────────────────────────────────────────────────────


def _deal(r: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": int(r["id"]),
        "competitor": r["competitor_name"],
        "outcome": r["outcome"],
        "reason_category": r["reason_category"],
        "reason_label": CATEGORIES.get(r["reason_category"], r["reason_category"]),
        "reason_text": r["reason_text"],
        "deal_name": r["deal_name"],
        "amount": r["amount"],
        "closed_on": r["closed_on"],
        "created_by": r["created_by"],
        "is_synthetic": bool(r["is_synthetic"]),
    }


def record_deal(
    competitor: str,
    outcome: str,
    reason_category: str,
    *,
    reason_text: str = "",
    deal_name: str = "",
    amount: float | None = None,
    closed_on: str | None = None,
    created_by: str | None = None,
    is_synthetic: bool = False,
) -> dict[str, Any]:
    if outcome not in ("won", "lost"):
        raise DealError("outcome must be 'won' or 'lost'")
    if reason_category not in CATEGORIES:
        raise DealError(f"reason_category must be one of {list(CATEGORIES)}")
    if amount is not None and (amount < 0 or amount > 1e10):
        raise DealError("amount must be a positive number")
    day = closed_on or date.today().isoformat()
    try:
        if date.fromisoformat(day) > date.today():
            raise DealError("closed_on cannot be in the future")
    except ValueError as exc:
        if isinstance(exc, DealError):
            raise
        raise DealError("closed_on must be a date (YYYY-MM-DD)") from exc

    init_schema()
    with closing(get_conn()) as conn, conn:
        cur = conn.execute(
            """
            INSERT INTO deals (competitor_name, outcome, reason_category, reason_text, deal_name,
                               amount, closed_on, created_by, created_at, is_synthetic)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (competitor, outcome, reason_category, (reason_text or "").strip()[:2000] or None,
             (deal_name or "").strip()[:200] or None, amount, day, created_by,
             datetime.now(timezone.utc).isoformat(timespec="seconds"), int(is_synthetic)),
        )
        row = conn.execute("SELECT * FROM deals WHERE id = ?", (cur.lastrowid,)).fetchone()
    return _deal(dict(row))


def list_deals(competitor: str | None = None, limit: int = 500) -> list[dict[str, Any]]:
    init_schema()
    sql, params = "SELECT * FROM deals", []
    if competitor:
        sql += " WHERE competitor_name = ?"
        params.append(competitor)
    sql += " ORDER BY closed_on DESC, id DESC LIMIT ?"
    params.append(limit)
    return [_deal(r) for r in query_rows(sql, tuple(params))]


def delete_deal(deal_id: int) -> None:
    with closing(get_conn()) as conn, conn:
        if conn.execute("DELETE FROM deals WHERE id = ?", (deal_id,)).rowcount == 0:
            raise KeyError(deal_id)


# ── Insights ──────────────────────────────────────────────────────────────────


def _review_shares(competitor: str) -> tuple[dict[str, float], dict[str, list[str]]]:
    """Share of complaint mentions per category, from the competitor's pain points."""
    from modules.pain_point_radar import get_pain_points

    try:
        pains = get_pain_points(competitor, top_n=20).to_dict("records")
    except Exception:  # noqa: BLE001 — no processed reviews yet
        pains = []
    weights: dict[str, float] = {c: 0.0 for c in CATEGORIES}
    topics: dict[str, list[str]] = {c: [] for c in CATEGORIES}
    for p in pains:
        cat = categorize(str(p["topic_label"]))
        # Severe complaints weigh more than mild ones.
        weights[cat] += float(p["mention_count"]) * float(p["avg_severity"])
        topics[cat].append(str(p["topic_label"]))
    total = sum(weights.values())
    return ({c: (w / total if total else 0.0) for c, w in weights.items()}, topics)


def _reading(lost: float, won: float, reviews: float) -> tuple[str, str] | tuple[None, None]:
    if lost >= MIN_SHARE and reviews >= MIN_SHARE:
        return "contested", "Their customers complain about this too — your pitch here isn't landing. Bring the review evidence into the deal."
    if lost >= MIN_SHARE and reviews < QUIET_SHARE:
        return "strength", "Their customers rarely complain about this — it is a real strength. Compete on something else."
    if won >= MIN_SHARE and reviews >= MIN_SHARE:
        return "proven", "You win on this and their customers confirm the weakness — keep leading with it."
    if reviews >= MIN_SHARE and lost < QUIET_SHARE and won < QUIET_SHARE:
        return "untapped", "Their customers complain about this, but it never comes up in your deals — raise it in discovery."
    return None, None


def winloss_insights(competitor: str) -> dict[str, Any]:
    deals = list_deals(competitor)
    won = [d for d in deals if d["outcome"] == "won"]
    lost = [d for d in deals if d["outcome"] == "lost"]
    review_share, topics = _review_shares(competitor)

    def share(items: list[dict], cat: str) -> float:
        return sum(1 for d in items if d["reason_category"] == cat) / len(items) if items else 0.0

    rows = []
    for cat, label in CATEGORIES.items():
        ls, ws, rs = share(lost, cat), share(won, cat), review_share[cat]
        # "Other" is whatever matched no keyword — too mixed to draw a conclusion from.
        kind, text = _reading(ls, ws, rs) if cat != "other" else (None, None)
        rows.append({
            "category": cat, "label": label,
            "lost": sum(1 for d in lost if d["reason_category"] == cat),
            "won": sum(1 for d in won if d["reason_category"] == cat),
            "lost_share": round(ls, 3), "won_share": round(ws, 3), "review_share": round(rs, 3),
            "review_topics": topics[cat][:3],
            "reading": kind, "reading_text": text,
        })
    rows.sort(key=lambda r: -(r["lost_share"] + r["won_share"] + r["review_share"]))
    rows = [r for r in rows if r["lost"] or r["won"] or r["review_share"] > 0]

    amount_lost = sum(d["amount"] or 0 for d in lost)
    return {
        "competitor": competitor,
        "deals": len(deals),
        "won": len(won),
        "lost": len(lost),
        "win_rate": round(len(won) / len(deals), 3) if deals else None,
        "amount_lost": amount_lost or None,
        "categories": rows,
        "is_synthetic": any(d["is_synthetic"] for d in deals),
    }
