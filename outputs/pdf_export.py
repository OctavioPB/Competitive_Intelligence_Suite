"""Convert battlecard dicts to PDF (weasyprint) or HTML (fallback)."""

import logging
from pathlib import Path

logger = logging.getLogger(__name__)

_BATTLECARD_DIR = Path("outputs/battlecards")

# Attempt to import weasyprint once at module load — determines which export path is used.
try:
    from weasyprint import HTML as _WeasyHTML  # type: ignore[import]
    _WEASYPRINT_AVAILABLE = True
except (ImportError, OSError):
    _WEASYPRINT_AVAILABLE = False
    logger.warning(
        "weasyprint is not installed. PDF export will fall back to HTML. "
        "Install weasyprint (+ GTK+ on Windows) for true PDF output."
    )

_BRAND_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600&family=Fraunces:ital,opsz,wght@0,9..144,300;1,9..144,300&display=swap');

* { box-sizing: border-box; margin: 0; padding: 0; }

body {
  font-family: 'Plus Jakarta Sans', Arial, sans-serif;
  font-size: 13px;
  color: #1C1C2E;
  background: #F4F6F9;
  padding: 32px;
  max-width: 900px;
  margin: 0 auto;
}

.header {
  background: #003366;
  color: #fff;
  padding: 28px 32px;
  border-radius: 10px;
  margin-bottom: 24px;
}
.header h1 {
  font-family: 'Fraunces', Georgia, serif;
  font-weight: 300;
  font-size: 26px;
  margin-bottom: 6px;
}
.header .meta {
  font-size: 12px;
  color: rgba(255,255,255,0.6);
  letter-spacing: 1px;
}

.pitch-box {
  background: #FEF8EC;
  border-left: 4px solid #C8982A;
  padding: 18px 22px;
  border-radius: 6px;
  margin-bottom: 28px;
  font-size: 14px;
  line-height: 1.6;
  color: #3D2A00;
}

h2 {
  font-family: 'Fraunces', Georgia, serif;
  font-weight: 300;
  font-size: 18px;
  color: #003366;
  margin-bottom: 16px;
  padding-bottom: 6px;
  border-bottom: 1px solid #E0EAF4;
}

.objection {
  background: #fff;
  border-radius: 8px;
  padding: 18px 20px;
  margin-bottom: 14px;
  box-shadow: 0 1px 3px rgba(0,51,102,.07);
  border-top: 3px solid #003366;
}
.objection h3 {
  font-size: 13px;
  font-weight: 600;
  color: #003366;
  margin-bottom: 10px;
}
.objection .label {
  font-size: 10px;
  letter-spacing: 2px;
  text-transform: uppercase;
  color: #6B7280;
  margin-bottom: 3px;
}
.objection .text { color: #374151; line-height: 1.5; margin-bottom: 10px; }
.objection .quote {
  font-style: italic;
  color: #6B7280;
  border-left: 3px solid #E0EAF4;
  padding-left: 12px;
  font-size: 12px;
  line-height: 1.5;
}

.gaps-table {
  width: 100%;
  border-collapse: collapse;
  background: #fff;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 1px 3px rgba(0,51,102,.07);
}
.gaps-table th {
  background: #003366;
  color: rgba(255,255,255,0.85);
  font-size: 10px;
  letter-spacing: 2px;
  text-transform: uppercase;
  padding: 10px 14px;
  text-align: left;
  font-weight: 500;
}
.gaps-table td {
  padding: 12px 14px;
  border-bottom: 1px solid #F0F4F8;
  vertical-align: top;
  line-height: 1.5;
}
.gaps-table tr:last-child td { border-bottom: none; }
.badge-covered {
  display: inline-block;
  background: #E0F7EF;
  color: #0D5C3A;
  font-size: 10px;
  letter-spacing: 2px;
  text-transform: uppercase;
  padding: 2px 8px;
  border-radius: 20px;
  font-weight: 600;
}
"""


def battlecard_to_html(card: dict) -> str:
    """Render a battlecard dict to a self-contained branded HTML string.

    Args:
        card: Dict matching battlecard_generator.BATTLECARD_SCHEMA.

    Returns:
        Full HTML document string.
    """
    competitor = card.get("competitor", "Unknown")
    generated_at = card.get("generated_at", "")[:19].replace("T", " ")
    pitch = card.get("recommended_pitch", "")

    objections_html = ""
    for i, obj in enumerate(card.get("objections", []), 1):
        objections_html += f"""
        <div class="objection">
            <h3>{i}. {obj.get('objection', '')}</h3>
            <div class="label">Evidence</div>
            <div class="text">{obj.get('evidence', '')}</div>
            <div class="label">Counter</div>
            <div class="text">{obj.get('counter', '')}</div>
            <div class="quote">"{obj.get('proof_quote', '')}"</div>
        </div>
        """

    gap_rows = ""
    for gap in card.get("feature_gaps", []):
        gap_rows += f"""
        <tr>
            <td>{gap.get('gap', '')}</td>
            <td style="text-align:center;font-weight:600;color:#003366;">
                {gap.get('frequency', 0)}
            </td>
            <td>{gap.get('your_advantage', '')}</td>
            <td><span class="badge-covered">✓ We have it</span></td>
        </tr>
        """

    gaps_table = f"""
    <table class="gaps-table">
        <thead>
            <tr>
                <th>Feature Gap</th>
                <th style="text-align:center;">Mentions</th>
                <th>Our Advantage</th>
                <th>Status</th>
            </tr>
        </thead>
        <tbody>{gap_rows}</tbody>
    </table>
    """ if gap_rows else "<p style='color:#6B7280;font-style:italic;'>No feature gaps identified.</p>"

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Battlecard: {competitor}</title>
<style>{_BRAND_CSS}</style>
</head>
<body>
<div class="header">
    <h1>Sales Battlecard: vs. {competitor}</h1>
    <div class="meta">Generated: {generated_at} UTC</div>
</div>

<h2>Recommended Pitch</h2>
<div class="pitch-box">{pitch}</div>

<h2>Objection Handlers</h2>
{objections_html}

<h2 style="margin-top:28px;">Feature Gaps (We Win Here)</h2>
{gaps_table}
</body>
</html>"""


def generate_pdf_bytes(card: dict) -> tuple[bytes, str]:
    """Render a battlecard to bytes.

    Returns PDF bytes when weasyprint is available, HTML bytes otherwise.

    Args:
        card: Battlecard dict matching BATTLECARD_SCHEMA.

    Returns:
        Tuple of (file_bytes, mime_type). mime_type is "application/pdf"
        or "text/html" depending on availability of weasyprint.
    """
    html_str = battlecard_to_html(card)
    if _WEASYPRINT_AVAILABLE:
        pdf_bytes = _WeasyHTML(string=html_str).write_pdf()
        return pdf_bytes, "application/pdf"
    else:
        return html_str.encode("utf-8"), "text/html"


def generate_pdf(card: dict, output_path: str) -> str:
    """Write a battlecard to a PDF or HTML file.

    Args:
        card: Battlecard dict matching BATTLECARD_SCHEMA.
        output_path: Destination path (extension will be corrected automatically).

    Returns:
        Actual path written (may differ if PDF falls back to HTML).
    """
    content_bytes, mime_type = generate_pdf_bytes(card)
    path = Path(output_path)

    if mime_type == "text/html":
        path = path.with_suffix(".html")
        logger.info(
            "weasyprint unavailable — writing HTML instead of PDF: %s", path
        )

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content_bytes)
    logger.info("Export written: %s (%d bytes)", path, len(content_bytes))
    return str(path)
