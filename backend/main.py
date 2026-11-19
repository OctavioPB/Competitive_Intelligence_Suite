"""RivalSense FastAPI backend — wraps existing Python module functions."""

import logging
import os
import sys
from contextlib import asynccontextmanager
from pathlib import Path

# Make repo root importable so all existing modules work without modification
sys.path.insert(0, str(Path(__file__).parent.parent))

import anthropic
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.routers import (
    alerts,
    battlecard,
    churn,
    crm,
    digest,
    meta,
    outreach,
    pain_points,
    prospects,
    reviews,
    sentiment,
    wishes,
)
from database.db import init_schema
from utils.llm import LLMConfigError

logger = logging.getLogger(__name__)

# The Vite dev server proxies /api, so CORS only matters when the UI is served
# from another origin. Keep the list explicit — "*" plus credentials is unsafe.
_DEFAULT_ORIGINS = "http://localhost:5173,http://127.0.0.1:5173"
_CORS_ORIGINS = [
    o.strip() for o in os.getenv("CORS_ORIGINS", _DEFAULT_ORIGINS).split(",") if o.strip()
]


@asynccontextmanager
async def lifespan(_: FastAPI):
    # Idempotent (IF NOT EXISTS): guarantees tables added after a DB was first
    # created — e.g. `digests` — exist, so writes are not silently dropped.
    init_schema()

    # Background scraping / alerting is opt-in; it also stays off in DEMO_MODE.
    if os.getenv("ENABLE_SCHEDULER", "false").lower() == "true":
        from scheduler.jobs import start_scheduler

        start_scheduler()
    yield


app = FastAPI(title="RivalSense API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_CORS_ORIGINS,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


@app.exception_handler(LLMConfigError)
async def _llm_not_configured(_: Request, exc: LLMConfigError):
    return JSONResponse(status_code=503, content={"detail": str(exc)})


@app.exception_handler(anthropic.APIError)
async def _llm_api_error(_: Request, exc: anthropic.APIError):
    logger.error("Claude API error: %s", exc)
    message = getattr(exc, "message", None) or str(exc)
    return JSONResponse(status_code=502, content={"detail": f"Claude API error: {message}"})


for _router in (
    meta, pain_points, sentiment, wishes, battlecard,
    alerts, prospects, churn, digest, outreach, reviews, crm,
):
    app.include_router(_router.router, prefix="/api")


@app.get("/")
def root():
    return {"service": "RivalSense API", "status": "ok"}


if __name__ == "__main__":
    import uvicorn

    # Loopback only: the API has no authentication (see README, Known Limitations).
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=True)
