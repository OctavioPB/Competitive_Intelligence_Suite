"""Wishes router — feature wish miner."""

from fastapi import APIRouter, Query

from config import OWN_FEATURES
from modules.feature_wish_miner import extract_wishes, flag_own_features

router = APIRouter(tags=["wishes"])


@router.get("/wishes")
def get_wishes(
    competitor: str = Query("Salesforce", description="Competitor name"),
    gaps_only: bool = Query(False, description="Return only rows where your product lacks the feature"),
):
    wish_df = extract_wishes(competitor)
    if wish_df.empty:
        return {"competitor": competitor, "clusters": []}

    flagged_df = flag_own_features(wish_df, OWN_FEATURES)

    if gaps_only:
        flagged_df = flagged_df[flagged_df["your_product_has_it"] == False]  # noqa: E712

    clusters = []
    for _, row in flagged_df.iterrows():
        sample = row.get("sample_quotes", [])
        if not isinstance(sample, list):
            sample = []
        clusters.append(
            {
                "wish_phrase_cluster": str(row["wish_phrase_cluster"]),
                "count": int(row["count"]),
                "sample_quotes": [str(q) for q in sample],
                "your_product_has_it": bool(row["your_product_has_it"]),
                "matched_feature": row.get("matched_feature") if row.get("matched_feature") else None,
            }
        )

    return {"competitor": competitor, "clusters": clusters}
