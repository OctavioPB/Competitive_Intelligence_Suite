"""Weekly HTML email digest of top alerts and prospect leads.

Sends a formatted HTML email via SendGrid when SENDGRID_API_KEY is set.
Falls back to a no-op with a logged warning when the key is absent.

Usage (from APScheduler or CLI):
    from outputs.email_digest import send_weekly_digest
    send_weekly_digest(alerts=alerts, leads_df=prospects_df, to_email="team@company.com")
"""

import logging
import os
from datetime import datetime

import pandas as pd

logger = logging.getLogger(__name__)

_SENDGRID_AVAILABLE = False
try:
    import sendgrid  # noqa: F401
    from sendgrid import SendGridAPIClient
    from sendgrid.helpers.mail import Mail

    _SENDGRID_AVAILABLE = True
except ImportError:
    logger.debug("sendgrid package not installed — email digest will be skipped.")

_FROM_EMAIL = "noreply@rivalsense.io"
_DIGEST_SUBJECT = "RivalSense Weekly Intel — {date}"

_HTML_TEMPLATE = """\
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  body {{ font-family: 'Helvetica Neue', Arial, sans-serif; background: #F4F6F9;
          margin: 0; padding: 0; color: #1C1C2E; }}
  .wrapper {{ max-width: 600px; margin: 32px auto; }}
  .header {{ background: #003366; border-radius: 10px 10px 0 0;
             padding: 28px 32px; }}
  .header h1 {{ font-family: Georgia, serif; font-weight: 300; color: #fff;
                font-size: 24px; margin: 0 0 6px; }}
  .header p {{ color: rgba(255,255,255,.6); font-size: 13px; margin: 0; }}
  .body {{ background: #fff; padding: 28px 32px; border-radius: 0 0 10px 10px;
           box-shadow: 0 2px 8px rgba(0,51,102,.08); }}
  .section-title {{ font-size: 10px; letter-spacing: 3px; text-transform: uppercase;
                    color: #C8982A; font-weight: 600; margin: 24px 0 12px; }}
  .alert-card {{ border-left: 4px solid #E03448; background: #F9FAFB;
                 border-radius: 6px; padding: 14px 16px; margin-bottom: 10px; }}
  .alert-card.news {{ border-left-color: #F07020; }}
  .alert-card.spike {{ border-left-color: #C8982A; }}
  .alert-competitor {{ font-weight: 600; font-size: 14px; color: #003366; }}
  .alert-evidence {{ font-size: 13px; color: #6B7280; margin-top: 4px; }}
  .lead-table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
  .lead-table th {{ background: #003366; color: rgba(255,255,255,.85);
                    padding: 8px 12px; text-align: left; font-size: 10px;
                    letter-spacing: 2px; text-transform: uppercase; font-weight: 500; }}
  .lead-table td {{ padding: 10px 12px; border-bottom: 1px solid #E0EAF4; }}
  .lead-table tr:last-child td {{ border-bottom: none; }}
  .footer {{ text-align: center; font-size: 11px; color: #9CA3AF;
             margin: 20px 0 0; padding: 16px; }}
</style>
</head>
<body>
<div class="wrapper">
  <div class="header">
    <h1>Rival<em style="color:#C8982A;font-style:italic;">Sense</em> Weekly Intel</h1>
    <p>Competitive intelligence digest — {date}</p>
  </div>
  <div class="body">
    <div class="section-title">Trigger Alerts This Week</div>
    {alerts_html}
    <div class="section-title">Top Prospect Leads</div>
    {leads_html}
  </div>
  <div class="footer">
    RivalSense · Unsubscribe · Generated automatically
  </div>
</div>
</body>
</html>
"""


def _render_alerts_html(alerts: list) -> str:
    """Render alert objects as HTML cards."""
    if not alerts:
        return '<p style="color:#6B7280;font-size:13px;">No alerts detected this week.</p>'

    border_class = {
        "sentiment_drop": "",
        "negative_news": "news",
        "review_spike": "spike",
    }
    type_label = {
        "sentiment_drop": "📉 Sentiment Drop",
        "negative_news": "📰 Negative News",
        "review_spike": "🔔 Review Spike",
    }

    html = ""
    for alert in alerts[:5]:
        css = border_class.get(alert.trigger_type, "")
        label = type_label.get(alert.trigger_type, alert.trigger_type)
        html += (
            f'<div class="alert-card {css}">'
            f'<div class="alert-competitor">{alert.competitor} — {label}</div>'
            f'<div class="alert-evidence">{alert.evidence_summary}</div>'
            f"</div>"
        )
    return html


def _render_leads_html(leads_df: pd.DataFrame | None) -> str:
    """Render top 5 prospect leads as an HTML table."""
    if leads_df is None or leads_df.empty:
        return '<p style="color:#6B7280;font-size:13px;">No prospect leads available this week.</p>'

    rows_html = ""
    for _, row in leads_df.head(5).iterrows():
        score = float(row.get("urgency_score", 0))
        badge_color = "#E03448" if score >= 0.7 else ("#F07020" if score >= 0.4 else "#27B97C")
        badge = (
            f'<span style="background:{badge_color}1A;color:{badge_color};'
            f"font-size:10px;padding:2px 8px;border-radius:10px;"
            f'font-weight:600;">{score:.2f}</span>'
        )
        rows_html += (
            f"<tr>"
            f"<td>{row.get('username', '—')}</td>"
            f"<td>{row.get('competitor_name', '—')}</td>"
            f"<td>{str(row.get('complaint_summary', ''))[:80]}</td>"
            f"<td style='text-align:center;'>{badge}</td>"
            f"</tr>"
        )

    return (
        '<table class="lead-table">'
        "<thead><tr>"
        "<th>User</th><th>Competitor</th><th>Complaint</th><th>Urgency</th>"
        "</tr></thead>"
        f"<tbody>{rows_html}</tbody>"
        "</table>"
    )


def build_digest_html(alerts: list, leads_df: pd.DataFrame | None) -> str:
    """Render the full weekly digest as an HTML string.

    Args:
        alerts: List of Alert objects from check_triggers().
        leads_df: Enriched prospects DataFrame from hot_prospect_finder.

    Returns:
        Complete HTML document string.
    """
    return _HTML_TEMPLATE.format(
        date=datetime.utcnow().strftime("%B %d, %Y"),
        alerts_html=_render_alerts_html(alerts),
        leads_html=_render_leads_html(leads_df),
    )


def send_weekly_digest(
    alerts: list,
    leads_df: pd.DataFrame | None,
    to_email: str,
) -> bool:
    """Send the weekly HTML digest via SendGrid.

    Silently skips when SENDGRID_API_KEY is not set or the package is absent.

    Args:
        alerts: List of Alert objects from check_triggers().
        leads_df: Enriched prospects DataFrame (may be None if no leads).
        to_email: Recipient email address.

    Returns:
        True if the email was sent successfully, False otherwise.
    """
    api_key = os.getenv("SENDGRID_API_KEY", "")
    if not api_key:
        logger.warning("SENDGRID_API_KEY not set — email digest skipped.")
        return False

    if not _SENDGRID_AVAILABLE:
        logger.warning("sendgrid package not installed — email digest skipped.")
        return False

    html_body = build_digest_html(alerts, leads_df)
    subject = _DIGEST_SUBJECT.format(date=datetime.utcnow().strftime("%Y-%m-%d"))

    message = Mail(
        from_email=_FROM_EMAIL,
        to_emails=to_email,
        subject=subject,
        html_content=html_body,
    )

    try:
        sg = SendGridAPIClient(api_key)
        response = sg.send(message)
        logger.info(
            "Weekly digest sent to %s (status %d)", to_email, response.status_code
        )
        return True
    except Exception as exc:  # noqa: BLE001
        logger.error("Failed to send weekly digest: %s", exc)
        return False
