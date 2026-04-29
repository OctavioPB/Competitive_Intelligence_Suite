"""Orchestrate the NLP pipeline: read reviews → write processed_reviews."""

import argparse
import json
import logging
import sys
from pathlib import Path

# Ensure project root is on sys.path when script is run directly
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd

from config import COMPETITORS, CompetitorConfig
from database.db import executemany, query_df
from pipeline.entity_extractor import extract_entities_batch
from pipeline.sentiment import compute_sentiment_delta, extract_wish_phrases, score_sentiment
from pipeline.topic_model import assign_topics, train_topics

logger = logging.getLogger(__name__)

_SELECT_REVIEWS = """
    SELECT id, source, competitor_name, review_text, rating, date
    FROM reviews
    WHERE competitor_name = ?
    ORDER BY date ASC
"""

# INSERT OR REPLACE relies on UNIQUE(review_id) constraint in schema.sql
_UPSERT_SQL = """
    INSERT INTO processed_reviews
        (review_id, source, competitor_name, review_text, rating, date,
         topic_cluster, topic_label, sentiment_score, sentiment_delta,
         entities, wish_phrases)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT(review_id) DO UPDATE SET
        topic_cluster  = excluded.topic_cluster,
        topic_label    = excluded.topic_label,
        sentiment_score = excluded.sentiment_score,
        sentiment_delta = excluded.sentiment_delta,
        entities       = excluded.entities,
        wish_phrases   = excluded.wish_phrases
"""


def run_for_competitor(competitor: CompetitorConfig) -> int:
    """Run the full NLP pipeline for a single competitor.

    Reads from reviews, writes to processed_reviews. Idempotent:
    re-running updates existing rows rather than inserting duplicates.

    Args:
        competitor: Competitor config dict from config.COMPETITORS.

    Returns:
        Number of processed_reviews rows written.
    """
    name = competitor["name"]
    df = query_df(_SELECT_REVIEWS, (name,))

    if df.empty:
        logger.warning("[%s] No reviews found in DB — run ingestion first.", name)
        return 0

    texts: list[str] = df["review_text"].tolist()
    logger.info("[%s] Processing %d reviews ...", name, len(df))

    # ── Batch: topic modeling ──────────────────────────────────────────────
    train_topics(name, texts)
    topic_assignments = assign_topics(texts, name)

    # ── Batch: NER entity extraction ──────────────────────────────────────
    logger.info("[%s] Extracting entities ...", name)
    all_entities = extract_entities_batch(texts)

    # ── Per-review: sentiment scoring ──────────────────────────────────────
    logger.info("[%s] Scoring sentiment ...", name)
    sentiment_results = [score_sentiment(t) for t in texts]
    sentiment_scores = [r["sentiment_score"] for r in sentiment_results]

    # ── Per-review: wish phrase extraction ────────────────────────────────
    wish_results = [extract_wish_phrases(t) for t in texts]

    # ── Compute sentiment delta across the competitor's timeline ───────────
    scores_df = pd.DataFrame(
        {"date": df["date"].tolist(), "sentiment_score": sentiment_scores},
        index=df.index,
    )
    deltas = compute_sentiment_delta(scores_df)

    # ── Write to processed_reviews (idempotent upsert) ────────────────────
    rows = []
    for i, (_, rev) in enumerate(df.iterrows()):
        rows.append(
            (
                int(rev["id"]),
                rev["source"],
                rev["competitor_name"],
                rev["review_text"],
                rev["rating"],
                rev["date"],
                topic_assignments[i]["topic_cluster"],
                topic_assignments[i]["topic_label"],
                sentiment_scores[i],
                float(deltas.iloc[i]),
                json.dumps(all_entities[i]),
                json.dumps(wish_results[i]),
            )
        )

    executemany(_UPSERT_SQL, rows)
    logger.info("[%s] Wrote %d processed_reviews rows.", name, len(rows))
    return len(rows)


def main() -> None:
    """CLI entry point.

    Usage:
        python pipeline/run_pipeline.py                        # all competitors
        python pipeline/run_pipeline.py --competitor HubSpot   # single competitor
    """
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)

    parser = argparse.ArgumentParser(description="RivalSense NLP pipeline")
    parser.add_argument(
        "--competitor",
        type=str,
        default=None,
        help="Competitor name to process (default: all)",
    )
    args = parser.parse_args()

    targets = (
        [c for c in COMPETITORS if c["name"] == args.competitor]
        if args.competitor
        else COMPETITORS
    )

    if not targets:
        logger.error("No competitor matched '%s'. Check config.COMPETITORS.", args.competitor)
        sys.exit(1)

    total = 0
    for competitor in targets:
        total += run_for_competitor(competitor)

    logger.info("Pipeline complete. Total processed rows: %d", total)


if __name__ == "__main__":
    main()
