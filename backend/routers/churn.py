"""Churn router — churn reason intelligence (M07)."""

from fastapi import APIRouter

from modules.churn_reason_intelligence import analyse_competitor, load_cached_analysis

router = APIRouter(tags=["churn"])


@router.get("/churn")
def get_cached_churn(competitor: str = "Salesforce"):
    """Return cached churn analysis for a competitor, or null if none exists."""
    return load_cached_analysis(competitor)


@router.post("/churn")
def create_churn_analysis(competitor: str = "Salesforce"):
    """Run a fresh churn reason analysis via Claude."""
    return analyse_competitor(competitor)
