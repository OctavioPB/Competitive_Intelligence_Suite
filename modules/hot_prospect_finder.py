"""M06 — Hot Prospect Finder: surface Reddit users actively switching competitors."""

import logging
import time
from datetime import datetime

import pandas as pd

from pipeline.sentiment import score_sentiment

logger = logging.getLogger(__name__)

_SWITCHING_PHRASES = [
    "looking for alternative",
    "switching from",
    "leaving",
    "is terrible",
    "alternative to",
    "fed up with",
    "moving away from",
    "replacing",
    "ditching",
    "frustrated with",
]

_REDDIT_COLUMNS = [
    "source", "post_id", "username", "post_text",
    "post_url", "created_at", "competitor_name",
    "upvotes", "num_comments",
]


def scan_reddit(competitor_list: list[str], subreddits: list[str]) -> pd.DataFrame:
    """Search subreddits for posts expressing intent to switch from a competitor.

    Requires REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET in the environment.
    Raises RuntimeError if credentials are missing (caller should fall back to fixtures).

    Args:
        competitor_list: Competitor names to search for.
        subreddits: Subreddit names to search (without r/ prefix).

    Returns:
        DataFrame with columns: source, post_id, username, post_text, post_url,
        created_at, competitor_name, upvotes, num_comments.
    """
    import os

    import praw

    client_id = os.getenv("REDDIT_CLIENT_ID", "")
    client_secret = os.getenv("REDDIT_CLIENT_SECRET", "")
    user_agent = os.getenv("REDDIT_USER_AGENT", "RivalSense/1.0 (competitive intelligence)")

    if not (client_id and client_secret):
        raise RuntimeError(
            "REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET must be set to use scan_reddit()."
        )

    reddit = praw.Reddit(
        client_id=client_id,
        client_secret=client_secret,
        user_agent=user_agent,
        read_only=True,
    )

    rows: list[dict] = []
    for subreddit_name in subreddits:
        subreddit = reddit.subreddit(subreddit_name)
        for competitor in competitor_list:
            query = f"{competitor} alternative OR switching OR leaving OR frustrated"
            try:
                for submission in subreddit.search(
                    query, limit=25, time_filter="month", sort="new"
                ):
                    rows.append(
                        {
                            "source": "reddit",
                            "post_id": submission.id,
                            "username": str(submission.author)
                            if submission.author
                            else "[deleted]",
                            "post_text": f"{submission.title} {submission.selftext}"[
                                :1000
                            ],
                            "post_url": f"https://reddit.com{submission.permalink}",
                            "created_at": datetime.utcfromtimestamp(
                                submission.created_utc
                            ).strftime("%Y-%m-%d"),
                            "competitor_name": competitor,
                            "upvotes": submission.score,
                            "num_comments": submission.num_comments,
                        }
                    )
                time.sleep(1)  # respect Reddit rate limits
            except Exception as exc:  # noqa: BLE001
                logger.warning(
                    "Reddit search failed for r/%s + %s: %s",
                    subreddit_name, competitor, exc,
                )

    if not rows:
        return pd.DataFrame(columns=_REDDIT_COLUMNS)

    return pd.DataFrame(rows)


def score_urgency(post: dict) -> float:
    """Score a Reddit post for switching-intent urgency.

    Scoring rubric (all additive, clamped to [0.0, 1.0]):
      +0.40  explicit switching-intent keyword present
      +0.30  negative sentiment (sentiment_score < -0.2); +0.15 if mildly negative
      +0.20  post created within last 7 days; +0.10 if within 30 days
      +0.10  engagement above threshold (upvotes + comments > 10)

    Args:
        post: Dict with keys: post_text (str), created_at (str, YYYY-MM-DD),
              upvotes (int), num_comments (int), sentiment_score (float, optional).

    Returns:
        Urgency score in [0.0, 1.0].
    """
    score = 0.0

    text_lower = str(post.get("post_text", "")).lower()

    # +0.4: explicit switching-intent phrase
    if any(phrase in text_lower for phrase in _SWITCHING_PHRASES):
        score += 0.4

    # +0.3 / +0.15: negative sentiment
    sentiment = float(post.get("sentiment_score", 0.0))
    if sentiment < -0.2:
        score += 0.30
    elif sentiment < 0.0:
        score += 0.15

    # +0.2 / +0.1: recency
    created_str = str(post.get("created_at", ""))[:10]
    try:
        created = datetime.strptime(created_str, "%Y-%m-%d")
        days_ago = (datetime.utcnow() - created).days
        if days_ago <= 7:
            score += 0.20
        elif days_ago <= 30:
            score += 0.10
    except ValueError:
        pass

    # +0.1: engagement
    engagement = int(post.get("upvotes", 0)) + int(post.get("num_comments", 0))
    if engagement > 10:
        score += 0.10

    return min(1.0, round(score, 3))


def enrich_lead(lead: dict) -> dict:
    """Add complaint_summary, company_signals, and suggested_angle to a lead.

    Also computes sentiment_score via the pipeline's VADER scorer if absent.

    Args:
        lead: Dict from a scan_reddit() result row (or equivalent).

    Returns:
        lead dict extended with:
        complaint_summary (str), company_signals (list[str]),
        suggested_angle (str), sentiment_score (float).
    """
    from modules.pain_point_radar import get_pain_points

    text = str(lead.get("post_text", ""))
    competitor = str(lead.get("competitor_name", ""))

    # Compute sentiment if not already present
    if "sentiment_score" not in lead or lead["sentiment_score"] is None:
        lead = {**lead, "sentiment_score": score_sentiment(text)["sentiment_score"]}

    # complaint_summary: first meaningful sentence, capped at 120 chars
    sentences = [
        s.strip()
        for s in text.replace("!", ".").replace("?", ".").split(".")
        if s.strip() and len(s.strip()) > 10
    ]
    complaint_summary = (sentences[0][:120] + "…") if sentences else text[:120]

    # company_signals: capitalised tokens that look like company/product names
    _STOP = {
        "I", "The", "A", "An", "My", "Our", "We", "They", "This", "That",
        "It", "If", "But", "And", "Or", "So", "Just", "Not", "Also",
    }
    company_signals: list[str] = []
    seen: set[str] = set()
    for token in text.split():
        clean = token.rstrip(".,!?;:'\"")
        if (
            clean
            and clean[0].isupper()
            and clean not in _STOP
            and len(clean) > 2
            and clean.lower() != competitor.lower()
            and clean not in seen
        ):
            company_signals.append(clean)
            seen.add(clean)
        if len(company_signals) >= 5:
            break

    # suggested_angle: tied to competitor's top pain point
    pain_df = get_pain_points(competitor, top_n=1)
    if not pain_df.empty:
        top_pain = pain_df.iloc[0]["topic_label"].replace("_", " ")
        suggested_angle = (
            f"Reference {competitor}'s known friction with {top_pain} — "
            f"position your product as the direct fix."
        )
    else:
        suggested_angle = (
            f"Emphasise how users switching from {competitor} report a notably "
            f"smoother experience with your product."
        )

    return {
        **lead,
        "complaint_summary": complaint_summary,
        "company_signals": company_signals,
        "suggested_angle": suggested_angle,
    }
