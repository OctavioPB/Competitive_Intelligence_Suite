"""Alert history: every detected alert, with a workflow status.

``check_triggers`` recomputes alerts from scratch on every scan. Without a
memory, a sentiment drop that lasts a week would be "new" — and sent to
Slack — seven days in a row. This module stores detections:

* A detection matching an alert of the same competitor, type and
  ``dedupe_key`` last seen within ``EPISODE_GAP_DAYS`` updates that row
  (latest evidence, ``last_seen``, ``times_seen``) and keeps its status.
* Anything else starts a new alert with status ``new``.

Statuses: ``new`` → ``seen`` → (optionally) ``dismissed``. A dismissed alert
stays dismissed while its episode continues; once the signal has been gone for
more than ``EPISODE_GAP_DAYS`` a fresh detection is a new alert again.
"""

from __future__ import annotations

import os
from contextlib import closing
from datetime import date, datetime, timezone
from typing import TYPE_CHECKING, Any

from database.db import get_conn, query_rows

if TYPE_CHECKING:
    from modules.trigger_alerts import Alert

STATUSES = ("new", "seen", "dismissed")
EPISODE_GAP_DAYS = 7

_COLUMNS = (
    "id, competitor_name, trigger_type, dedupe_key, evidence_summary, first_seen, last_seen, "
    "times_seen, status, status_changed_at, outreach_draft, notified_at, is_synthetic"
)


class UnknownAlertError(LookupError):
    """No alert with that id."""


def _synthetic_competitors() -> set[str]:
    """Competitors whose stored reviews are mostly sample data (alerts on them are too)."""
    if os.getenv("DEMO_MODE", "false").lower() == "true":
        from config import COMPETITOR_NAMES

        return set(COMPETITOR_NAMES)
    from modules.review_evidence import get_data_status

    try:
        status = get_data_status()
    except Exception:  # noqa: BLE001 — no reviews table yet means no sample data either
        return set()
    return {
        name for name, s in status.items()
        if s.get("reviews") and s.get("synthetic", 0) / s["reviews"] > 0.5
    }


def _row(record: dict[str, Any], is_new: bool | None = None) -> dict[str, Any]:
    out = {
        "id": int(record["id"]),
        "competitor": record["competitor_name"],
        "trigger_type": record["trigger_type"],
        "evidence_summary": record["evidence_summary"],
        "first_seen": record["first_seen"],
        "last_seen": record["last_seen"],
        "times_seen": int(record["times_seen"]),
        "status": record["status"],
        "status_changed_at": record["status_changed_at"],
        "outreach_draft": record["outreach_draft"],
        "notified": record["notified_at"] is not None,
        "is_synthetic": bool(record["is_synthetic"]),
    }
    if is_new is not None:
        out["is_new"] = is_new
    return out


def record_alerts(alerts: list[Alert], detected_on: date | None = None) -> list[dict[str, Any]]:
    """Store one scan's detections; return them as history rows.

    Each returned row carries ``is_new`` — True when this scan created it.
    """
    day = (detected_on or date.today()).isoformat()
    synthetic = _synthetic_competitors()
    rows: list[dict[str, Any]] = []
    with closing(get_conn()) as conn, conn:
        for alert in alerts:
            key = alert.dedupe_key or ""
            existing = conn.execute(
                f"""
                SELECT {_COLUMNS} FROM alert_history
                WHERE competitor_name = ? AND trigger_type = ? AND dedupe_key = ?
                  AND last_seen >= date(?, ?)
                ORDER BY id DESC LIMIT 1
                """,
                (alert.competitor, alert.trigger_type, key, day, f"-{EPISODE_GAP_DAYS} days"),
            ).fetchone()

            if existing is not None:
                same_day = existing["last_seen"] == day
                conn.execute(
                    """
                    UPDATE alert_history
                    SET evidence_summary = ?, last_seen = ?, times_seen = times_seen + ?
                    WHERE id = ?
                    """,
                    (alert.evidence_summary, day, 0 if same_day else 1, existing["id"]),
                )
                alert_id, is_new = existing["id"], False
            else:
                cur = conn.execute(
                    """
                    INSERT INTO alert_history
                        (competitor_name, trigger_type, dedupe_key, evidence_summary,
                         first_seen, last_seen, outreach_draft, is_synthetic)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (alert.competitor, alert.trigger_type, key, alert.evidence_summary, day, day,
                     alert.outreach_draft or None, int(alert.competitor in synthetic)),
                )
                alert_id, is_new = cur.lastrowid, True

            record = conn.execute(f"SELECT {_COLUMNS} FROM alert_history WHERE id = ?", (alert_id,)).fetchone()
            rows.append(_row(dict(record), is_new))
    return rows


def list_alerts(
    status: str | None = None,
    competitor: str | None = None,
    active_only: bool = False,
    limit: int = 200,
) -> list[dict[str, Any]]:
    """History rows, most recently seen first.

    Args:
        active_only: Only alerts detected within the last ``EPISODE_GAP_DAYS``
            of the most recent detection.
    """
    where, params = [], []
    if status:
        where.append("status = ?")
        params.append(status)
    if competitor:
        where.append("competitor_name = ?")
        params.append(competitor)
    if active_only:
        where.append("last_seen >= date((SELECT MAX(last_seen) FROM alert_history), ?)")
        params.append(f"-{EPISODE_GAP_DAYS} days")
    sql = f"SELECT {_COLUMNS} FROM alert_history"
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY last_seen DESC, id DESC LIMIT ?"
    params.append(limit)
    return [_row(r) for r in query_rows(sql, tuple(params))]


def status_counts() -> dict[str, int]:
    counts = {s: 0 for s in STATUSES}
    rows = query_rows("SELECT status, COUNT(*) AS n FROM alert_history GROUP BY status")
    counts.update({r["status"]: int(r["n"]) for r in rows})
    return counts


def set_status(alert_id: int, status: str) -> dict[str, Any]:
    if status not in STATUSES:
        raise ValueError(f"status must be one of {STATUSES}")
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    with closing(get_conn()) as conn, conn:
        cur = conn.execute(
            "UPDATE alert_history SET status = ?, status_changed_at = ? WHERE id = ?",
            (status, now, alert_id),
        )
        if cur.rowcount == 0:
            raise UnknownAlertError(alert_id)
        record = conn.execute(f"SELECT {_COLUMNS} FROM alert_history WHERE id = ?", (alert_id,)).fetchone()
    return _row(dict(record))


def mark_all_seen(competitor: str | None = None) -> int:
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    sql = "UPDATE alert_history SET status = 'seen', status_changed_at = ? WHERE status = 'new'"
    params: tuple = (now,)
    if competitor:
        sql += " AND competitor_name = ?"
        params = (now, competitor)
    with closing(get_conn()) as conn, conn:
        return conn.execute(sql, params).rowcount


def save_draft(alert_id: int, draft: str) -> None:
    with closing(get_conn()) as conn, conn:
        conn.execute("UPDATE alert_history SET outreach_draft = ? WHERE id = ?", (draft, alert_id))


def mark_notified(alert_ids: list[int]) -> None:
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    with closing(get_conn()) as conn, conn:
        conn.executemany(
            "UPDATE alert_history SET notified_at = ? WHERE id = ?", [(now, i) for i in alert_ids],
        )


def pending_notifications(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Rows from :func:`record_alerts` worth a Slack message: never notified, not dismissed."""
    return [r for r in rows if not r["notified"] and r["status"] != "dismissed"]
