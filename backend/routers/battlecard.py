"""Battlecard router — AI-generated sales battlecards."""

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel

from backend.deps import known_competitor
from modules.battlecard_generator import generate_battlecard, load_cached_battlecard
from outputs.pdf_export import export_filename, generate_pdf_bytes

router = APIRouter(tags=["battlecard"])


class BattlecardRequest(BaseModel):
    competitor: str


@router.get("/battlecard")
def get_cached_battlecard(competitor: str = "Salesforce"):
    """Return the cached battlecard, or null if none exists."""
    return load_cached_battlecard(known_competitor(competitor))


@router.get("/battlecard/export")
def export_battlecard(competitor: str = "Salesforce"):
    """Download the cached battlecard as PDF.

    Without weasyprint on the server the response is print-ready HTML
    (Content-Type text/html); the UI opens it and triggers the browser's
    print dialog so the user can still save a PDF.
    """
    card = load_cached_battlecard(known_competitor(competitor))
    if card is None:
        raise HTTPException(
            status_code=404,
            detail=f"No battlecard for {competitor} yet — generate one first.",
        )

    content, mime_type = generate_pdf_bytes(card)
    filename = export_filename(competitor, mime_type)
    return Response(
        content=content,
        media_type=mime_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/battlecard")
def create_battlecard(body: BattlecardRequest):
    """Generate a fresh battlecard via the Claude API."""
    return generate_battlecard(known_competitor(body.competitor))
