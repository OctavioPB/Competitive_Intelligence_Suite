"""Meta router — competitor names and own-feature list."""

from fastapi import APIRouter

from config import COMPETITOR_NAMES, OWN_FEATURES

router = APIRouter(tags=["meta"])


@router.get("/meta/competitors")
def get_competitors():
    return {"competitors": COMPETITOR_NAMES}


@router.get("/meta/own-features")
def get_own_features():
    return {"features": OWN_FEATURES}
