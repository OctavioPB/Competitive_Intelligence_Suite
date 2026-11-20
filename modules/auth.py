"""Accounts, password hashing and sessions.

* Passwords: scrypt (stdlib) with a random 16-byte salt per user.
* Sessions: a random 32-byte token in an HttpOnly, SameSite=Strict cookie. Only
  its SHA-256 is stored, so a leaked database does not leak live sessions.
* Roles: ``admin`` (manages users and settings) and ``member``.
* Brute force: after ``MAX_FAILURES`` failed logins for an email or a client
  address within ``FAILURE_WINDOW``, further attempts are refused for that window.
"""

from __future__ import annotations

import hashlib
import hmac
import re
import secrets
import threading
import time
from collections import defaultdict, deque
from contextlib import closing
from datetime import datetime, timedelta, timezone
from typing import Any

from database.db import get_conn, init_schema

ROLES = ("admin", "member")
SESSION_DAYS = 14
MIN_PASSWORD = 10
MAX_FAILURES = 5
FAILURE_WINDOW = 15 * 60          # seconds
COOKIE_NAME = "rs_session"

_SCRYPT = {"n": 2**14, "r": 8, "p": 1, "dklen": 32}
_EMAIL = re.compile(r"^[^@\s]{1,64}@[^@\s]{1,190}\.[^@\s]{2,}$")


class AuthError(Exception):
    """Login refused; the message is safe to show (never says which part was wrong)."""


class UserError(ValueError):
    """Invalid account data; the message says which field."""


# ── Passwords ─────────────────────────────────────────────────────────────────


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.scrypt(password.encode("utf-8"), salt=salt, **_SCRYPT)
    return f"scrypt${salt.hex()}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        scheme, salt_hex, digest_hex = stored.split("$")
    except ValueError:
        return False
    if scheme != "scrypt":
        return False
    digest = hashlib.scrypt(password.encode("utf-8"), salt=bytes.fromhex(salt_hex), **_SCRYPT)
    return hmac.compare_digest(digest.hex(), digest_hex)


# A real hash to verify against when the email is unknown, so a login attempt
# takes the same time whether or not the account exists.
_DUMMY_HASH = hash_password(secrets.token_urlsafe(16))


# ── Users ─────────────────────────────────────────────────────────────────────


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(dt: datetime) -> str:
    return dt.isoformat(timespec="seconds")


def _public(row: Any) -> dict[str, Any]:
    return {
        "id": int(row["id"]),
        "email": row["email"],
        "name": row["name"],
        "role": row["role"],
        "created_at": row["created_at"],
        "last_login": row["last_login"],
    }


def _validate(email: str, name: str, password: str | None, role: str) -> tuple[str, str]:
    email, name = email.strip().lower(), name.strip()
    if not _EMAIL.match(email):
        raise UserError("Enter a valid email address")
    if not 1 <= len(name) <= 80:
        raise UserError("Name: 1–80 characters")
    if password is not None and len(password) < MIN_PASSWORD:
        raise UserError(f"Password: at least {MIN_PASSWORD} characters")
    if password is not None and len(password) > 256:
        raise UserError("Password: at most 256 characters")
    if role not in ROLES:
        raise UserError(f"Role must be one of {ROLES}")
    return email, name


def user_count() -> int:
    init_schema()
    with closing(get_conn()) as conn:
        return conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]


def create_user(email: str, name: str, password: str, role: str = "member") -> dict[str, Any]:
    email, name = _validate(email, name, password, role)
    init_schema()
    with closing(get_conn()) as conn, conn:
        if conn.execute("SELECT 1 FROM users WHERE email = ?", (email,)).fetchone():
            raise UserError("An account with that email already exists")
        cur = conn.execute(
            "INSERT INTO users (email, name, password_hash, role, created_at) VALUES (?, ?, ?, ?, ?)",
            (email, name, hash_password(password), role, _iso(_now())),
        )
        row = conn.execute("SELECT * FROM users WHERE id = ?", (cur.lastrowid,)).fetchone()
    return _public(row)


def list_users() -> list[dict[str, Any]]:
    with closing(get_conn()) as conn:
        return [_public(r) for r in conn.execute("SELECT * FROM users ORDER BY created_at, id")]


def _admin_count(conn) -> int:
    return conn.execute("SELECT COUNT(*) FROM users WHERE role = 'admin'").fetchone()[0]


def update_user(user_id: int, *, role: str | None = None, password: str | None = None) -> dict[str, Any]:
    with closing(get_conn()) as conn, conn:
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        if row is None:
            raise KeyError(user_id)
        if role is not None:
            _validate(row["email"], row["name"], None, role)
            if row["role"] == "admin" and role != "admin" and _admin_count(conn) == 1:
                raise UserError("Keep at least one admin")
            conn.execute("UPDATE users SET role = ? WHERE id = ?", (role, user_id))
        if password is not None:
            _validate(row["email"], row["name"], password, row["role"])
            conn.execute("UPDATE users SET password_hash = ? WHERE id = ?", (hash_password(password), user_id))
            # A new password signs the account out everywhere.
            conn.execute("DELETE FROM sessions WHERE user_id = ?", (user_id,))
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    return _public(row)


def delete_user(user_id: int) -> None:
    with closing(get_conn()) as conn, conn:
        row = conn.execute("SELECT role FROM users WHERE id = ?", (user_id,)).fetchone()
        if row is None:
            raise KeyError(user_id)
        if row["role"] == "admin" and _admin_count(conn) == 1:
            raise UserError("Keep at least one admin")
        conn.execute("DELETE FROM sessions WHERE user_id = ?", (user_id,))
        conn.execute("DELETE FROM users WHERE id = ?", (user_id,))


# ── Brute-force limiter ───────────────────────────────────────────────────────

_failures: dict[str, deque[float]] = defaultdict(deque)
_lock = threading.Lock()


def _recent(key: str, now: float) -> deque[float]:
    q = _failures[key]
    while q and now - q[0] > FAILURE_WINDOW:
        q.popleft()
    return q


def _throttled(keys: list[str]) -> bool:
    now = time.monotonic()
    with _lock:
        return any(len(_recent(k, now)) >= MAX_FAILURES for k in keys)


def _record_failure(keys: list[str]) -> None:
    now = time.monotonic()
    with _lock:
        for k in keys:
            _recent(k, now).append(now)


def reset_limiter() -> None:
    with _lock:
        _failures.clear()


# ── Sessions ──────────────────────────────────────────────────────────────────


def _token_hash(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def login(email: str, password: str, client: str = "") -> tuple[str, dict[str, Any]]:
    """Check credentials and open a session. Returns (token, user)."""
    email = email.strip().lower()
    keys = [f"email:{email}", f"client:{client}"]
    if _throttled(keys):
        raise AuthError("Too many failed attempts. Try again in 15 minutes.")
    init_schema()
    with closing(get_conn()) as conn, conn:
        row = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        ok = verify_password(password, row["password_hash"] if row else _DUMMY_HASH)
        if not row or not ok:
            _record_failure(keys)
            raise AuthError("Wrong email or password.")
        token = secrets.token_urlsafe(32)
        now = _now()
        conn.execute(
            "INSERT INTO sessions (token_hash, user_id, created_at, expires_at) VALUES (?, ?, ?, ?)",
            (_token_hash(token), row["id"], _iso(now), _iso(now + timedelta(days=SESSION_DAYS))),
        )
        conn.execute("UPDATE users SET last_login = ? WHERE id = ?", (_iso(now), row["id"]))
        conn.execute("DELETE FROM sessions WHERE expires_at < ?", (_iso(now),))
        row = conn.execute("SELECT * FROM users WHERE id = ?", (row["id"],)).fetchone()
    return token, _public(row)


def user_for_token(token: str | None) -> dict[str, Any] | None:
    if not token:
        return None
    try:
        with closing(get_conn()) as conn:
            row = conn.execute(
                """
                SELECT u.* FROM sessions s JOIN users u ON u.id = s.user_id
                WHERE s.token_hash = ? AND s.expires_at > ?
                """,
                (_token_hash(token), _iso(_now())),
            ).fetchone()
    except Exception:  # noqa: BLE001 — no sessions table yet means no valid session
        return None
    return _public(row) if row else None


def logout(token: str | None) -> None:
    if not token:
        return
    with closing(get_conn()) as conn, conn:
        conn.execute("DELETE FROM sessions WHERE token_hash = ?", (_token_hash(token),))
