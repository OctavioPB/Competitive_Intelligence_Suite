"""RivalSense FastAPI backend — wraps existing Python module functions."""

import sys
from pathlib import Path

# Make repo root importable so all existing modules work without modification
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.routers import meta, pain_points, sentiment, wishes, battlecard, alerts, prospects, churn, digest, outreach

app = FastAPI(title="RivalSense API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(meta.router, prefix="/api")
app.include_router(pain_points.router, prefix="/api")
app.include_router(sentiment.router, prefix="/api")
app.include_router(wishes.router, prefix="/api")
app.include_router(battlecard.router, prefix="/api")
app.include_router(alerts.router, prefix="/api")
app.include_router(prospects.router, prefix="/api")
app.include_router(churn.router,    prefix="/api")
app.include_router(digest.router,   prefix="/api")
app.include_router(outreach.router, prefix="/api")


@app.get("/")
def root():
    return {"service": "RivalSense API", "status": "ok"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
