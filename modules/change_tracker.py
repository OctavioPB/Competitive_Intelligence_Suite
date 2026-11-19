"""What changed for a competitor since the previous period.

Combines everything the app already stores but never compared:

* reviews: volume, sentiment and rating this window vs the one before, and
  which pain-point topics appeared, rose or faded (anchored on the latest
  review date, like every other windowed query);
* battlecards: the newest dated version vs the one before it — pitch,
  objections and feature gaps added or removed;
* digests: the latest stored digest vs the previous one for this competitor;
* alerts first detected, pricing changes and job postings in the window.

``highlights`` turns the lot into a few sentences for the top of the page.
"""

from __future__ import annotations

import json
import re
from datetime import date, timedelta
from typing import Any

import pandas as pd

from database.db import query_df

_TOPIC_LIMIT = 5
_SENTIMENT_MOVE = 0.05        # smaller moves in average sentiment are reported as "stable"

_REVIEW_WINDOWS_SQL = """
    WITH anchor AS (SELECT MAX(date) AS d FROM processed_reviews WHERE competitor_name = :competitor)
    SELECT
        (SELECT d FROM anchor) AS anchor,
        SUM(CASE WHEN date >  date((SELECT d FROM anchor), :cur) THEN 1 ELSE 0 END) AS cur_n,
        SUM(CASE WHEN date <= date((SELECT d FROM anchor), :cur)
                  AND date >  date((SELECT d FROM anchor), :prev) THEN 1 ELSE 0 END) AS prev_n,
        AVG(CASE WHEN date >  date((SELECT d FROM anchor), :cur) THEN sentiment_score END) AS cur_s,
        AVG(CASE WHEN date <= date((SELECT d FROM anchor), :cur)
                  AND date >  date((SELECT d FROM anchor), :prev) THEN sentiment_score END) AS prev_s,
        AVG(CASE WHEN date >  date((SELECT d FROM anchor), :cur) THEN rating END) AS cur_r,
        AVG(CASE WHEN date <= date((SELECT d FROM anchor), :cur)
                  AND date >  date((SELECT d FROM anchor), :prev) THEN rating END) AS prev_r
    FROM processed_reviews
    WHERE competitor_name = :competitor
"""

_TOPIC_WINDOWS_SQL = """
    WITH anchor AS (SELECT MAX(date) AS d FROM processed_reviews WHERE competitor_name = :competitor)
    SELECT topic_label,
        SUM(CASE WHEN date >  date((SELECT d FROM anchor), :cur) THEN 1 ELSE 0 END) AS cur_n,
        SUM(CASE WHEN date <= date((SELECT d FROM anchor), :cur)
                  AND date >  date((SELECT d FROM anchor), :prev) THEN 1 ELSE 0 END) AS prev_n
    FROM processed_reviews
    WHERE competitor_name = :competitor
      AND topic_label IS NOT NULL AND COALESCE(topic_cluster, 0) != -1
      AND date > date((SELECT d FROM anchor), :prev)
    GROUP BY topic_label
"""


def _num(value: Any, digits: int = 3) -> float | None:
    return None if value is None or pd.isna(value) else round(float(value), digits)


# ── Reviews ───────────────────────────────────────────────────────────────────


def review_changes(competitor: str, days: int = 7) -> dict[str, Any]:
    params = {"competitor": competitor, "cur": f"-{days} days", "prev": f"-{2 * days} days"}
    row = query_df(_REVIEW_WINDOWS_SQL, params).to_dict("records")[0]
    topics = query_df(_TOPIC_WINDOWS_SQL, params)

    new, rising, fading = [], [], []
    for t in topics.to_dict("records"):
        cur, prev = int(t["cur_n"] or 0), int(t["prev_n"] or 0)
        item = {"topic": t["topic_label"], "current": cur, "previous": prev}
        if cur and not prev:
            new.append(item)
        elif cur > prev:
            rising.append(item)
        elif prev > cur:
            fading.append(item)
    new.sort(key=lambda x: -x["current"])
    rising.sort(key=lambda x: -(x["current"] - x["previous"]))
    fading.sort(key=lambda x: -(x["previous"] - x["current"]))

    return {
        "anchor_date": row["anchor"],
        "current": {"reviews": int(row["cur_n"] or 0), "sentiment": _num(row["cur_s"]), "rating": _num(row["cur_r"], 2)},
        "previous": {"reviews": int(row["prev_n"] or 0), "sentiment": _num(row["prev_s"]), "rating": _num(row["prev_r"], 2)},
        "topics": {"new": new[:_TOPIC_LIMIT], "rising": rising[:_TOPIC_LIMIT], "fading": fading[:_TOPIC_LIMIT]},
    }


# ── Battlecards ───────────────────────────────────────────────────────────────


def battlecard_versions(competitor: str) -> list[str]:
    """Dates (YYYY-MM-DD, newest first) of the stored battlecard versions."""
    from modules.battlecard_generator import _BATTLECARD_DIR, _slug

    slug = _slug(competitor)
    dates = []
    for path in _BATTLECARD_DIR.glob(f"{slug}_*.json"):
        m = re.fullmatch(rf"{re.escape(slug)}_(\d{{4}})(\d{{2}})(\d{{2}})\.json", path.name)
        if m:
            dates.append("-".join(m.groups()))
    return sorted(dates, reverse=True)


def _load_version(competitor: str, day: str) -> dict | None:
    from modules.battlecard_generator import _BATTLECARD_DIR, _slug

    path = _BATTLECARD_DIR / f"{_slug(competitor)}_{day.replace('-', '')}.json"
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", str(text)).strip().lower()


def _added_removed(before: list[str], after: list[str]) -> tuple[list[str], list[str]]:
    b, a = {_norm(x): x for x in before}, {_norm(x): x for x in after}
    return [a[k] for k in a if k not in b], [b[k] for k in b if k not in a]


def battlecard_changes(competitor: str) -> dict[str, Any] | None:
    """Newest battlecard version vs the one before it (None when there is no version)."""
    versions = battlecard_versions(competitor)
    if not versions:
        return None
    current = _load_version(competitor, versions[0])
    if current is None:
        return None
    previous = _load_version(competitor, versions[1]) if len(versions) > 1 else None
    out: dict[str, Any] = {
        "versions": len(versions),
        "current_date": versions[0],
        "previous_date": versions[1] if previous else None,
        "pitch_changed": False,
        "pitch_before": None,
        "pitch_after": current.get("recommended_pitch"),
        "objections_added": [], "objections_removed": [],
        "gaps_added": [], "gaps_removed": [],
    }
    if previous is None:
        return out

    def objections(card):
        return [o.get("objection", "") for o in card.get("objections", []) if o.get("objection")]

    def gaps(card):
        return [g.get("gap", "") for g in card.get("feature_gaps", []) if g.get("gap")]

    out["pitch_before"] = previous.get("recommended_pitch")
    out["pitch_changed"] = _norm(out["pitch_before"] or "") != _norm(out["pitch_after"] or "")
    out["objections_added"], out["objections_removed"] = _added_removed(objections(previous), objections(current))
    out["gaps_added"], out["gaps_removed"] = _added_removed(gaps(previous), gaps(current))
    return out


# ── Digests ───────────────────────────────────────────────────────────────────


def digest_changes(competitor: str) -> dict[str, Any] | None:
    """This competitor's entry in the latest digest vs the previous digest."""
    df = query_df("SELECT generated_at, report_json FROM digests ORDER BY id DESC LIMIT 2")
    if df.empty:
        return None

    def entry(report_json: str) -> tuple[dict, dict | None]:
        try:
            report = json.loads(report_json)
        except json.JSONDecodeError:
            return {}, None
        match = next((c for c in report.get("per_competitor", []) if c.get("name") == competitor), None)
        return report, match

    rows = df.to_dict("records")
    cur_report, cur = entry(rows[0]["report_json"])
    prev_report, prev = entry(rows[1]["report_json"]) if len(rows) > 1 else ({}, None)

    def view(c: dict | None) -> dict | None:
        if not c:
            return None
        return {
            "sentiment_delta": _num(c.get("sentiment_delta")),
            "sentiment_signal": c.get("sentiment_signal"),
            "top_pain": c.get("top_pain"),
            "summary": c.get("summary"),
        }

    return {
        "current_at": rows[0]["generated_at"],
        "previous_at": rows[1]["generated_at"] if len(rows) > 1 else None,
        "theme_before": prev_report.get("overall_theme") if prev_report else None,
        "theme_after": cur_report.get("overall_theme"),
        "before": view(prev),
        "after": view(cur),
    }


# ── Alerts, pricing, hiring in the window ─────────────────────────────────────


def _new_alerts(competitor: str, days: int) -> list[dict[str, Any]]:
    from modules.alert_history import list_alerts

    since = (date.today() - timedelta(days=days)).isoformat()
    return [a for a in list_alerts(competitor=competitor, limit=50) if a["first_seen"] >= since]


def _pricing_in_window(competitor: str, days: int) -> list[dict[str, Any]]:
    from modules.market_signals import get_pricing_overview

    found = []
    for page in get_pricing_overview(competitor)["pages"]:
        change = page["last_change"]
        if not change:
            continue
        since = (date.fromisoformat(page["last_checked"]) - timedelta(days=days)).isoformat()
        if change["date"] >= since:
            found.append({"url": page["url"], "date": change["date"], "changes": change["changes"]})
    return found


def _hiring_in_window(competitor: str, days: int) -> dict[str, int] | None:
    df = query_df(
        """
        WITH anchor AS (SELECT MAX(last_seen) AS d FROM job_postings WHERE competitor_name = :c)
        SELECT COUNT(*) AS n,
               SUM(category = 'support') AS support,
               SUM(integration) AS integration
        FROM job_postings
        WHERE competitor_name = :c AND last_seen = (SELECT d FROM anchor)
          AND COALESCE(posted_date, first_seen) > date((SELECT d FROM anchor), :w)
        """,
        {"c": competitor, "w": f"-{days} days"},
    )
    row = df.to_dict("records")[0]
    if not row["n"]:
        return None
    return {"new_roles": int(row["n"]), "support": int(row["support"] or 0), "integration": int(row["integration"] or 0)}


def _safe(fn, *args):
    """A missing table (e.g. a database that never ran market signals) is "no data"."""
    try:
        return fn(*args)
    except Exception:  # noqa: BLE001
        return None


# ── Summary ───────────────────────────────────────────────────────────────────


def _highlights(competitor: str, r: dict, card: dict | None, digest: dict | None,
                alerts: list, pricing: list, hiring: dict | None, days: int) -> list[str]:
    lines: list[str] = []
    cur, prev = r["current"], r["previous"]
    if cur["sentiment"] is not None and prev["sentiment"] is not None:
        move = cur["sentiment"] - prev["sentiment"]
        if abs(move) >= _SENTIMENT_MOVE:
            word = "improved" if move > 0 else "fell"
            lines.append(f"Sentiment {word} from {prev['sentiment']:+.2f} to {cur['sentiment']:+.2f}.")
    if prev["reviews"] and cur["reviews"] >= 2 * prev["reviews"]:
        lines.append(f"Review volume jumped: {cur['reviews']} vs {prev['reviews']} the {days} days before.")
    # A topic mentioned once is noise, not news.
    for t in [t for t in r["topics"]["new"] if t["current"] >= 2][:2]:
        lines.append(f"New complaint topic: {t['topic']} ({t['current']} mentions).")
    for p in pricing[:1]:
        lines.append(f"Pricing page changed on {p['date']}: {p['changes'][0]}" if p["changes"] else
                     f"Pricing page changed on {p['date']}.")
    if hiring and hiring["support"] >= 3:
        lines.append(f"{hiring['support']} new support roles posted.")
    if alerts:
        lines.append(f"{len(alerts)} new alert{'s' if len(alerts) != 1 else ''} detected.")
    if card and card["previous_date"]:
        n = len(card["objections_added"]) + len(card["gaps_added"])
        if card["pitch_changed"] or n:
            entries = f"{n} new objection{'' if n == 1 else 's'} / gaps" if n else "new pitch"
            lines.append(f"Battlecard updated on {card['current_date']} ({entries}).")
    if digest and digest["before"] and digest["after"] and digest["before"]["top_pain"] != digest["after"]["top_pain"]:
        lines.append(f"Digest top pain moved from “{digest['before']['top_pain']}” to “{digest['after']['top_pain']}”.")
    return lines


def get_changes(competitor: str, days: int = 7) -> dict[str, Any]:
    reviews = review_changes(competitor, days)
    card = _safe(battlecard_changes, competitor)
    digest = _safe(digest_changes, competitor)
    alerts = _safe(_new_alerts, competitor, days) or []
    pricing = _safe(_pricing_in_window, competitor, days) or []
    hiring = _safe(_hiring_in_window, competitor, days)
    return {
        "competitor": competitor,
        "window_days": days,
        "reviews": reviews,
        "battlecard": card,
        "digest": digest,
        "alerts": alerts,
        "pricing": pricing,
        "hiring": hiring,
        "highlights": _highlights(competitor, reviews, card, digest, alerts, pricing, hiring, days),
    }
