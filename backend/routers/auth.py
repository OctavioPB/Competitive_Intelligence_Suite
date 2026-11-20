"""Auth router — sign in / out, first-admin setup and user management."""

import os
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, Field

from backend.auth_deps import auth_enabled, current_user, is_local_request, require_admin
from modules.auth import (
    COOKIE_NAME,
    MIN_PASSWORD,
    SESSION_DAYS,
    AuthError,
    UserError,
    create_user,
    delete_user,
    list_users,
    login,
    logout,
    update_user,
    user_count,
)

router = APIRouter(tags=["auth"])


class LoginRequest(BaseModel):
    email: str = Field(max_length=254)
    password: str = Field(max_length=256)


class NewUser(BaseModel):
    email: str = Field(max_length=254)
    name: str = Field(max_length=80)
    password: str = Field(max_length=256)
    role: Literal["admin", "member"] = "member"


class SetupRequest(BaseModel):
    email: str = Field(max_length=254)
    name: str = Field(max_length=80)
    password: str = Field(max_length=256)
    setup_token: str | None = Field(None, max_length=256)


class UserUpdate(BaseModel):
    role: Literal["admin", "member"] | None = None
    password: str | None = Field(None, max_length=256)


def _set_cookie(response: Response, request: Request, token: str) -> None:
    secure = request.url.scheme == "https" or os.getenv("COOKIE_SECURE", "false").lower() == "true"
    response.set_cookie(
        COOKIE_NAME, token,
        max_age=SESSION_DAYS * 24 * 3600, httponly=True, samesite="strict", secure=secure, path="/",
    )


def _setup_allowed(request: Request) -> bool:
    """The first admin can be created from this machine, or anywhere with
    RIVALSENSE_SETUP_TOKEN — never by whoever reaches a fresh server first."""
    return bool(os.getenv("RIVALSENSE_SETUP_TOKEN")) or is_local_request(request)


@router.get("/auth/status")
def status(request: Request):
    """What the UI needs before showing anything: is a login (or setup) required?"""
    if not auth_enabled():
        return {"auth_enabled": False, "setup_required": False, "setup_allowed": False,
                "user": current_user(request), "min_password": MIN_PASSWORD}
    needs_setup = user_count() == 0
    return {
        "auth_enabled": True,
        "setup_required": needs_setup,
        "setup_allowed": needs_setup and _setup_allowed(request),
        "setup_token_required": needs_setup and bool(os.getenv("RIVALSENSE_SETUP_TOKEN")),
        "user": current_user(request),
        "min_password": MIN_PASSWORD,
    }


@router.post("/auth/setup")
def setup(body: SetupRequest, request: Request, response: Response):
    """Create the first admin account (only while there are no users)."""
    if not auth_enabled() or user_count() > 0:
        raise HTTPException(status_code=409, detail="Setup is already done — sign in instead.")
    expected = os.getenv("RIVALSENSE_SETUP_TOKEN")
    if expected:
        import hmac

        if not hmac.compare_digest(body.setup_token or "", expected):
            raise HTTPException(status_code=403, detail="Wrong setup token.")
    elif not is_local_request(request):
        raise HTTPException(status_code=403, detail="Create the first admin from the server itself "
                                                    "(or set RIVALSENSE_SETUP_TOKEN).")
    try:
        create_user(body.email, body.name, body.password, role="admin")
    except UserError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    token, user = login(body.email, body.password, client=request.client.host if request.client else "")
    _set_cookie(response, request, token)
    return user


@router.post("/auth/login")
def do_login(body: LoginRequest, request: Request, response: Response):
    try:
        token, user = login(body.email, body.password, client=request.client.host if request.client else "")
    except AuthError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    _set_cookie(response, request, token)
    return user


@router.post("/auth/logout")
def do_logout(request: Request, response: Response):
    logout(request.cookies.get(COOKIE_NAME))
    response.delete_cookie(COOKIE_NAME, path="/")
    return {"ok": True}


@router.get("/auth/me")
def me(request: Request):
    user = current_user(request)
    if user is None:
        raise HTTPException(status_code=401, detail="Sign in required")
    return user


# ── User management (admins) ──────────────────────────────────────────────────


@router.get("/auth/users")
def users(_: dict = Depends(require_admin)):
    return list_users()


@router.post("/auth/users")
def add_user(body: NewUser, _: dict = Depends(require_admin)):
    try:
        return create_user(body.email, body.name, body.password, body.role)
    except UserError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.patch("/auth/users/{user_id}")
def change_user(user_id: int, body: UserUpdate, admin: dict = Depends(require_admin)):
    if user_id == admin["id"] and body.role == "member":
        raise HTTPException(status_code=422, detail="You cannot remove your own admin role.")
    try:
        return update_user(user_id, role=body.role, password=body.password)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="No such user") from exc
    except UserError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.delete("/auth/users/{user_id}")
def remove_user(user_id: int, admin: dict = Depends(require_admin)):
    if user_id == admin["id"]:
        raise HTTPException(status_code=422, detail="You cannot delete your own account.")
    try:
        delete_user(user_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="No such user") from exc
    except UserError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {"ok": True}
