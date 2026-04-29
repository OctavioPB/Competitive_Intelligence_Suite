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


def export_leads_csv(df: pd.DataFrame, filename: str = "leads.csv") -> str:
    """Write leads DataFrame to a CSV file with CRM-compatible column names.

    Args:
        df: DataFrame from hot_prospect_finder.scan_reddit() (enriched).
        filename: Output filename (written to outputs/).

    Returns:
        Absolute path to the written CSV file.
    """
    raise NotImplementedError("Implement in Sprint 5 — Day 14")


def export_leads_json(df: pd.DataFrame, filename: str = "leads.json") -> str:
    """Write leads DataFrame to a JSON file with CRM-compatible field names.

    Args:
        df: DataFrame from hot_prospect_finder.scan_reddit() (enriched).
        filename: Output filename (written to outputs/).

    Returns:
        Absolute path to the written JSON file.
    """
    raise NotImplementedError("Implement in Sprint 5 — Day 14")
