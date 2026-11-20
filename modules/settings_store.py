"""Competitors and own features, stored in the database and editable from the UI.

``config.py`` only holds the *defaults*: the first time a database is used the
tables are empty and get seeded from ``config.COMPETITORS`` / ``config.OWN_FEATURES``.
From then on the database is the source of truth, so each deployment (each
client) keeps its own list. Every reader in the app goes through this module:

    competitors()       -> list[CompetitorConfig]
    competitor_names()  -> list[str]
    get_competitor(n)   -> CompetitorConfig | None
    own_features()      -> list[str]
"""

from __future__ import annotations

import json
import re
from contextlib import closing
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlparse

from config import COMPETITORS as DEFAULT_COMPETITORS
from config import OWN_FEATURES as DEFAULT_OWN_FEATURES
from config import CompetitorConfig
from database.db import get_conn, init_schema

_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9 .&+'()-]{0,59}$")
_SLUG = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,99}$")
_PROVIDERS = {"greenhouse", "lever", "ashby", "workday"}
MAX_COMPETITORS = 25
MAX_FEATURES = 50


class SettingsError(ValueError):
    """Invalid competitor or feature settings; the message says which field."""


def _ensure(conn) -> None:
    """Create the tables if needed and seed them from config.py when empty."""
    tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    if not {"competitors", "own_features"} <= tables:
        init_schema()
    if conn.execute("SELECT COUNT(*) FROM competitors").fetchone()[0] == 0:
        _write_all(conn, list(DEFAULT_COMPETITORS))
    if conn.execute("SELECT COUNT(*) FROM own_features").fetchone()[0] == 0:
        conn.executemany(
            "INSERT INTO own_features (feature, position) VALUES (?, ?)",
            [(f, i) for i, f in enumerate(DEFAULT_OWN_FEATURES)],
        )


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _write_all(conn, items: list[CompetitorConfig]) -> None:
    conn.execute("DELETE FROM competitors")
    conn.executemany(
        "INSERT INTO competitors (name, config_json, position, updated_at) VALUES (?, ?, ?, ?)",
        [
            (c["name"], json.dumps({k: v for k, v in c.items() if k != "name"}), i, _now())
            for i, c in enumerate(items)
        ],
    )


# ── Read ──────────────────────────────────────────────────────────────────────


def competitors() -> list[CompetitorConfig]:
    with closing(get_conn()) as conn, conn:
        _ensure(conn)
        rows = conn.execute("SELECT name, config_json FROM competitors ORDER BY position, name").fetchall()
    return [{"name": r["name"], **json.loads(r["config_json"])} for r in rows]


def competitor_names() -> list[str]:
    return [c["name"] for c in competitors()]


def get_competitor(name: str) -> CompetitorConfig | None:
    return next((c for c in competitors() if c["name"] == name), None)


def own_features() -> list[str]:
    with closing(get_conn()) as conn, conn:
        _ensure(conn)
        rows = conn.execute("SELECT feature FROM own_features ORDER BY position, feature").fetchall()
    return [r["feature"] for r in rows]


# ── Validate ──────────────────────────────────────────────────────────────────


def _https_url(value: Any, field: str) -> str:
    url = str(value or "").strip()
    parsed = urlparse(url)
    if parsed.scheme != "https" or not parsed.netloc:
        raise SettingsError(f"{field} must be an https:// URL")
    return url


def _keywords(value: Any) -> list[str]:
    items = value if isinstance(value, list) else str(value or "").split(",")
    words = [str(w).strip().lower() for w in items if str(w).strip()]
    if not words:
        raise SettingsError("reddit_keywords needs at least one keyword")
    if len(words) > 20 or any(len(w) > 60 for w in words):
        raise SettingsError("reddit_keywords: at most 20 keywords of up to 60 characters")
    return words


def validate_competitor(data: dict[str, Any]) -> CompetitorConfig:
    """Normalise and check one competitor; raises SettingsError on bad input."""
    name = str(data.get("name") or "").strip()
    if not _NAME.match(name):
        raise SettingsError("name: 1–60 letters, digits, spaces or . & + ' ( ) -")
    out: dict[str, Any] = {"name": name}
    for field in ("g2_slug", "trustpilot_slug"):
        value = str(data.get(field) or "").strip()
        if value and not _SLUG.match(value):
            raise SettingsError(f"{field}: letters, digits, dots, dashes or underscores only")
        out[field] = value
    out["reddit_keywords"] = _keywords(data.get("reddit_keywords"))

    urls = data.get("pricing_urls") or []
    if isinstance(urls, str):
        urls = [u for u in urls.splitlines() if u.strip()]
    if len(urls) > 5:
        raise SettingsError("pricing_urls: at most 5")
    if urls:
        out["pricing_urls"] = [_https_url(u, "pricing_urls") for u in urls]

    careers = data.get("careers")
    if careers and (careers.get("provider") or careers.get("board")):
        provider = str(careers.get("provider") or "").strip().lower()
        board = str(careers.get("board") or "").strip()
        if provider not in _PROVIDERS:
            raise SettingsError(f"careers.provider must be one of {sorted(_PROVIDERS)}")
        if provider == "workday":
            board = _https_url(board, "careers.board")
        elif not _SLUG.match(board):
            raise SettingsError("careers.board: the board token from the job board URL")
        out["careers"] = {"provider": provider, "board": board}

    app_id = data.get("app_store_id")
    if app_id not in (None, "", 0):
        try:
            out["app_store_id"] = int(app_id)
        except (TypeError, ValueError) as exc:
            raise SettingsError("app_store_id must be a number") from exc
    if data.get("capterra_url"):
        out["capterra_url"] = _https_url(data["capterra_url"], "capterra_url")
    return out  # type: ignore[return-value]


# ── Write ─────────────────────────────────────────────────────────────────────


def save_competitor(data: dict[str, Any], original_name: str | None = None) -> CompetitorConfig:
    """Create a competitor, or update one (``original_name`` allows renaming).

    Renaming only changes the configuration: data already stored under the old
    name (reviews, alerts, deals) stays under the old name.
    """
    cfg = validate_competitor(data)
    current = competitors()
    names = [c["name"] for c in current]
    target = original_name or cfg["name"]
    if original_name and original_name not in names:
        raise KeyError(original_name)
    if cfg["name"] != target and cfg["name"] in names:
        raise SettingsError(f"A competitor named '{cfg['name']}' already exists")
    if not original_name and cfg["name"] in names:
        raise SettingsError(f"A competitor named '{cfg['name']}' already exists")
    if not original_name and len(current) >= MAX_COMPETITORS:
        raise SettingsError(f"At most {MAX_COMPETITORS} competitors")

    updated = [cfg if c["name"] == target else c for c in current] if original_name else [*current, cfg]
    with closing(get_conn()) as conn, conn:
        _write_all(conn, updated)
    return cfg


def delete_competitor(name: str) -> None:
    current = competitors()
    if name not in [c["name"] for c in current]:
        raise KeyError(name)
    if len(current) == 1:
        raise SettingsError("Keep at least one competitor")
    with closing(get_conn()) as conn, conn:
        _write_all(conn, [c for c in current if c["name"] != name])


def set_own_features(features: list[str]) -> list[str]:
    cleaned: list[str] = []
    for f in features:
        f = re.sub(r"\s+", " ", str(f)).strip().lower()
        if not f:
            continue
        if len(f) > 80:
            raise SettingsError("Each feature: up to 80 characters")
        if f not in cleaned:
            cleaned.append(f)
    if not cleaned:
        # An empty table means "never configured" and would be re-seeded from config.py.
        raise SettingsError("Keep at least one feature")
    if len(cleaned) > MAX_FEATURES:
        raise SettingsError(f"At most {MAX_FEATURES} features")
    with closing(get_conn()) as conn, conn:
        _ensure(conn)
        conn.execute("DELETE FROM own_features")
        conn.executemany(
            "INSERT INTO own_features (feature, position) VALUES (?, ?)",
            [(f, i) for i, f in enumerate(cleaned)],
        )
    return cleaned
