"""Convert markdown battlecards to PDF using weasyprint."""

import logging
from pathlib import Path

logger = logging.getLogger(__name__)

_BATTLECARD_DIR = Path("outputs/battlecards")


def generate_pdf(markdown_content: str, output_path: str) -> None:
    """Render a markdown battlecard to a PDF file.

    Converts markdown → HTML (with brand CSS injected) → PDF via weasyprint.
    Target file size: < 500 KB per battlecard.

    Args:
        markdown_content: Battlecard markdown string.
        output_path: Destination path for the PDF file.
    """
    raise NotImplementedError("Implement in Sprint 4 — Day 10")
