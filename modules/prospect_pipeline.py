"""Prospect pipeline: Hot Prospect leads kept across scans, each with a stage.

Every scan upserts its leads (keyed by post URL) into ``prospect_leads``:
the latest urgency and summary are refreshed, but the stage and note a rep set
are never overwritten. Stages: new → contacted → replied → opportunity, plus
``dismissed`` for leads that are not a fit.
"""

from __future__ import annotations

import json
from contextlib import closing
from datetime import date, datetime, timezone
from typing import Any

from database.db import get_conn, query_rows

STAGES = ("new", "contacted", "replied", "opportunity", "dismissed")
STAGE_LABELS = {
    "new": "New",
    "contacted": "Contacted",
    "replied": "Replied",
    "opportunity": "Opportunity",
    "dismissed": "Not a fit",
}

_COLUMNS = (
    "post_url, username, competitor_name, created_at, urgency_score, complaint_summary, "
    "company_signals, suggested_angle, status, note, first_seen, last_seen, status_changed_at, is_synthetic"
)


class UnknownLeadError(LookupError):
    """No stored lead with that post URL."""


def _lead(record: dict[str, Any]) -> dict[str, Any]:
    try:
        signals = json.loads(record["company_signals"] or "[]")
    except (TypeError, json.JSONDecodeError):
        signals = []
    return {
        "username": record["username"],
        "post_url": record["post_url"],
        "created_at": record["created_at"] or "",
        "competitor_name": record["competitor_name"] or "",
        "urgency_score": float(record["urgency_score"] or 0.0),
        "complaint_summary": record["complaint_summary"] or "",
        "company_signals": signals if isinstance(signals, list) else [],
        "suggested_angle": record["suggested_angle"] or "",
        "is_synthetic": bool(record["is_synthetic"]),
        "status": record["status"],
        "note": record["note"],
        "first_seen": record["first_seen"],
        "last_seen": record["last_seen"],
        "status_changed_at": record["status_changed_at"],
    }


def upsert_leads(leads: list[dict[str, Any]], seen_on: date | None = None) -> list[dict[str, Any]]:
    """Store one scan's leads; return them (same order) with their pipeline stage."""
    day = (seen_on or date.today()).isoformat()
    out: list[dict[str, Any]] = []
    with closing(get_conn()) as conn, conn:
        for lead in leads:
            values = (
                lead["username"], lead.get("competitor_name"), lead.get("created_at"),
                float(lead.get("urgency_score") or 0.0), lead.get("complaint_summary"),
                json.dumps(lead.get("company_signals") or []), lead.get("suggested_angle"),
            )
            cur = conn.execute(
                """
                UPDATE prospect_leads
                SET username = ?, competitor_name = ?, created_at = ?, urgency_score = ?,
                    complaint_summary = ?, company_signals = ?, suggested_angle = ?, last_seen = ?
                WHERE post_url = ?
                """,
                (*values, day, lead["post_url"]),
            )
            if cur.rowcount == 0:
                conn.execute(
                    f"""
                    INSERT INTO prospect_leads ({_COLUMNS})
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'new', NULL, ?, ?, NULL, ?)
                    """,
                    (lead["post_url"], *values, day, day, int(bool(lead.get("is_synthetic")))),
                )
            record = conn.execute(
                f"SELECT {_COLUMNS} FROM prospect_leads WHERE post_url = ?", (lead["post_url"],),
            ).fetchone()
            out.append(_lead(dict(record)))
    return out


def set_stage(post_url: str, status: str, note: str | None = None) -> dict[str, Any]:
    """Move a lead to another stage (and optionally replace its note)."""
    if status not in STAGES:
        raise ValueError(f"status must be one of {STAGES}")
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    with closing(get_conn()) as conn, conn:
        if note is None:
            cur = conn.execute(
                "UPDATE prospect_leads SET status = ?, status_changed_at = ? WHERE post_url = ?",
                (status, now, post_url),
            )
        else:
            cur = conn.execute(
                "UPDATE prospect_leads SET status = ?, note = ?, status_changed_at = ? WHERE post_url = ?",
                (status, note.strip() or None, now, post_url),
            )
        if cur.rowcount == 0:
            raise UnknownLeadError(post_url)
        record = conn.execute(f"SELECT {_COLUMNS} FROM prospect_leads WHERE post_url = ?", (post_url,)).fetchone()
    return _lead(dict(record))


def get_pipeline(include_dismissed: bool = False) -> dict[str, Any]:
    """All stored leads by stage (most urgent first) with a count per stage."""
    rows = query_rows(f"SELECT {_COLUMNS} FROM prospect_leads ORDER BY urgency_score DESC, last_seen DESC")
    leads = [_lead(r) for r in rows]
    counts = {s: 0 for s in STAGES}
    for lead in leads:
        counts[lead["status"]] = counts.get(lead["status"], 0) + 1
    if not include_dismissed:
        leads = [lead for lead in leads if lead["status"] != "dismissed"]
    return {
        "stages": [{"id": s, "label": STAGE_LABELS[s], "count": counts[s]} for s in STAGES],
        "leads": leads,
    }
