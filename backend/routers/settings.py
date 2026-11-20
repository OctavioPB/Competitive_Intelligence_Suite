"""Settings router — competitors and own features (admins only to change)."""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from backend.auth_deps import require_admin
from modules.settings_store import (
    SettingsError,
    competitors,
    delete_competitor,
    own_features,
    save_competitor,
    set_own_features,
)

router = APIRouter(tags=["settings"])


class FeaturesRequest(BaseModel):
    features: list[str] = Field(max_length=200)


@router.get("/settings")
def get_settings():
    """Everyone signed in can read the configuration."""
    return {"competitors": competitors(), "own_features": own_features()}


@router.post("/settings/competitors")
def add_competitor(body: dict[str, Any], _: dict = Depends(require_admin)):
    try:
        return save_competitor(body)
    except SettingsError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.put("/settings/competitors/{name}")
def edit_competitor(name: str, body: dict[str, Any], _: dict = Depends(require_admin)):
    try:
        return save_competitor(body, original_name=name)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"No competitor named '{name}'") from exc
    except SettingsError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.delete("/settings/competitors/{name}")
def remove_competitor(name: str, _: dict = Depends(require_admin)):
    try:
        delete_competitor(name)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"No competitor named '{name}'") from exc
    except SettingsError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {"ok": True}


@router.put("/settings/own-features")
def update_features(body: FeaturesRequest, _: dict = Depends(require_admin)):
    try:
        return {"own_features": set_own_features(body.features)}
    except SettingsError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
