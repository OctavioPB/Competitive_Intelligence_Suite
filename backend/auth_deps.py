"""Authentication plumbing shared by the app and the routers.

Auth is ON by default. ``AUTH_DISABLED=true`` turns it off for a single-user
setup on your own machine; then every request acts as a local admin.
"""

import os

from fastapi import HTTPException, Request

from modules.auth import COOKIE_NAME, user_for_token

LOCAL_ADMIN = {"id": 0, "email": "local@localhost", "name": "Local user", "role": "admin",
               "created_at": None, "last_login": None}

# Reachable without a session: everything needed to sign in.
PUBLIC_PATHS = frozenset({"/api/auth/status", "/api/auth/login", "/api/auth/logout", "/api/auth/setup"})


def auth_enabled() -> bool:
    return os.getenv("AUTH_DISABLED", "false").lower() != "true"


def current_user(request: Request) -> dict | None:
    if not auth_enabled():
        return LOCAL_ADMIN
    return getattr(request.state, "user", None) or user_for_token(request.cookies.get(COOKIE_NAME))


def require_admin(request: Request) -> dict:
    user = current_user(request)
    if user is None:
        raise HTTPException(status_code=401, detail="Sign in required")
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Only admins can do this")
    return user


def is_local_request(request: Request) -> bool:
    """A direct request from this machine (not relayed by a reverse proxy)."""
    host = request.client.host if request.client else ""
    proxied = any(h in request.headers for h in ("x-forwarded-for", "forwarded", "x-real-ip"))
    return host in ("127.0.0.1", "::1", "localhost") and not proxied
