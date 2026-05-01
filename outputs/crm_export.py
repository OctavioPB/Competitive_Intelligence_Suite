"""Export lead and alert data to CRM-compatible CSV and JSON formats."""

import logging
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)

_EXPORT_DIR = Path("outputs")

# Canonical column names for Salesforce/HubSpot import compatibility
CRM_COLUMNS = [
    "source",
    "username",
    "complaint_summary",
    "company_signals",
    "urgency_score",
    "suggested_angle",
    "post_url",
    "created_at",
    "competitor_name",
]


def _normalise_to_crm(df: pd.DataFrame) -> pd.DataFrame:
    """Reindex df to CRM_COLUMNS, filling missing columns with None."""
    export_df = pd.DataFrame(columns=CRM_COLUMNS)
    for col in CRM_COLUMNS:
        if col in df.columns:
            export_df[col] = df[col].values
    return export_df


def export_leads_csv(df: pd.DataFrame, filename: str = "leads.csv") -> str:
    """Write a leads DataFrame to a CRM-compatible CSV file.

    Args:
        df: DataFrame from hot_prospect_finder (enriched with urgency_score).
        filename: Output filename (written into outputs/).

    Returns:
        Absolute path string of the written CSV file.
    """
    _EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    path = _EXPORT_DIR / filename
    _normalise_to_crm(df).to_csv(path, index=False, encoding="utf-8")
    logger.info("CRM CSV written: %s (%d rows)", path, len(df))
    return str(path.resolve())


def export_leads_json(df: pd.DataFrame, filename: str = "leads.json") -> str:
    """Write a leads DataFrame to a CRM-compatible JSON file.

    Args:
        df: DataFrame from hot_prospect_finder (enriched with urgency_score).
        filename: Output filename (written into outputs/).

    Returns:
        Absolute path string of the written JSON file.
    """
    _EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    path = _EXPORT_DIR / filename
    _normalise_to_crm(df).to_json(path, orient="records", indent=2, force_ascii=False)
    logger.info("CRM JSON written: %s (%d rows)", path, len(df))
    return str(path.resolve())
