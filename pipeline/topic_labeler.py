"""Human-readable names for topic clusters.

BERTopic names clusters after its top raw tokens ("connectors_the_getting_than"),
which then appear in every module and in the UI. This module replaces them with:

1. Claude-written names ("ERP Integration Costs") when ANTHROPIC_API_KEY is set —
   one call per competitor, built from each cluster's keywords and sample reviews.
2. Otherwise, the cluster's most distinctive keywords with stop words and the
   competitor's own name removed ("Connectors / ERP / Integration").
"""

import logging
import re

import pandas as pd

from database.db import executemany, query_df

logger = logging.getLogger(__name__)

OUTLIER_LABEL = "misc"
INSUFFICIENT_LABEL = "insufficient_data"

_KEYWORDS_PER_CLUSTER = 8
_KEYWORDS_IN_FALLBACK_LABEL = 3
_SAMPLES_PER_CLUSTER = 4
_SAMPLE_CHARS = 220
_MAX_LABEL_CHARS = 48
_MAX_FALLBACK_CHARS = 36

_SYSTEM_PROMPT = """\
You name customer-review topic clusters for a competitive-intelligence dashboard \
used by B2B sales teams.

For each cluster you get its most distinctive keywords and a few sample reviews \
about one competitor's product. Return a short name for what the cluster is about.

Rules:
- 2 to 4 words, Title Case, at most 40 characters
- Name the theme or complaint ("Per-Seat Pricing", "Mobile App Crashes", \
"Slow Support Response"), not the sentiment and not the competitor's name
- Every name must be distinct
- Return ONLY a JSON object mapping each cluster id (as a string) to its name — \
no markdown fences, no explanation
"""

_USER_PROMPT_TEMPLATE = """\
Competitor: {competitor}

{clusters}

Return the JSON object now.
"""

_SELECT_CLUSTERED_SQL = """
    SELECT topic_cluster, review_text
    FROM processed_reviews
    WHERE competitor_name = ?
"""

_UPDATE_LABEL_SQL = """
    UPDATE processed_reviews
    SET topic_label = ?
    WHERE competitor_name = ? AND topic_cluster = ?
"""


# Words common in any review that say nothing about what a cluster is about.
_GENERIC_WORDS = frozenset({
    "able", "actually", "basically", "best", "better", "completely", "constantly",
    "crm", "customer", "customers", "day", "days", "didn", "doesn", "don", "every",
    "experience", "feature", "features", "fully", "genuinely", "get", "getting", "good",
    "got", "great", "isn", "just", "like", "little", "ll", "lot", "lots", "lose", "make",
    "makes", "month", "months", "need", "needs", "new", "people", "platform", "product",
    "really", "reason", "reasons", "require", "requires", "simply", "software", "take",
    "takes", "team", "teams", "thing", "things", "time", "times", "took", "tool", "tools",
    "use", "used", "useful", "user", "users", "using", "ve", "want", "way", "ways",
    "week", "weeks", "won", "work", "working", "works", "year", "years",
})

_TOKEN_RE = re.compile(r"[a-z][a-z\-]{2,}")
_MIN_COVERAGE = 0.2  # a keyword must appear in at least 20% of the cluster's reviews
_BIGRAM_PREFERENCE = 1.3


def _name_tokens(competitor: str) -> set[str]:
    return {t for t in re.split(r"[^a-z0-9]+", competitor.lower()) if t}


def _make_analyzer(stop: frozenset[str]):
    """Unigrams plus bigrams of *adjacent* content words.

    sklearn's ngram_range builds bigrams after dropping stop words, which glues
    words that were never next to each other ("engineers, not salespeople" →
    "engineers salespeople").
    """

    def analyze(text: str) -> list[str]:
        tokens = _TOKEN_RE.findall(text.lower())
        terms = [t for t in tokens if t not in stop]
        terms += [
            f"{a} {b}" for a, b in zip(tokens, tokens[1:]) if a not in stop and b not in stop
        ]
        return terms

    return analyze


def cluster_keywords(
    texts: list[str],
    clusters: list[int],
    competitor: str,
    top_k: int = _KEYWORDS_PER_CLUSTER,
) -> dict[int, list[str]]:
    """Return the most distinctive keywords of every non-outlier cluster, best first.

    A term scores high when it appears in many of the cluster's reviews and
    rarely in the competitor's other reviews. Terms seen in under 20% of the
    cluster are ignored, so one-off words from a single review never become a
    topic name. Stop words, generic review vocabulary and the competitor's own
    name are excluded — they otherwise dominate every cluster.
    """
    import numpy as np
    from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS, CountVectorizer

    labels = np.asarray([int(c) for c in clusters])
    ids = sorted({int(c) for c in labels if c >= 0})
    if not ids:
        return {}

    stop = frozenset(ENGLISH_STOP_WORDS | _GENERIC_WORDS | _name_tokens(competitor))
    vectorizer = CountVectorizer(analyzer=_make_analyzer(stop), binary=True)
    try:
        presence = vectorizer.fit_transform(str(t) for t in texts)   # reviews × terms
    except ValueError:  # every token was a stop word
        return {i: [] for i in ids}
    vocab = vectorizer.get_feature_names_out()
    is_bigram = np.char.find(vocab.astype(str), " ") >= 0

    keywords: dict[int, list[str]] = {}
    for cluster_id in ids:
        inside = labels == cluster_id
        coverage = np.asarray(presence[inside].mean(axis=0)).ravel()
        elsewhere = (
            np.asarray(presence[~inside].mean(axis=0)).ravel() if (~inside).any()
            else np.zeros_like(coverage)
        )
        score = coverage * np.log1p(coverage / (elsewhere + 0.02))
        score[coverage < _MIN_COVERAGE] = 0.0
        # A phrase that is nearly as distinctive as its words reads better as a label.
        score[is_bigram] *= _BIGRAM_PREFERENCE

        chosen: list[str] = []
        for j in score.argsort()[::-1]:
            if score[j] <= 0 or len(chosen) == top_k:
                break
            term = str(vocab[j])
            # "mobile" adds nothing once "mobile app" is in, and vice versa
            if any(set(term.split()) & set(t.split()) for t in chosen):
                continue
            chosen.append(term)
        keywords[cluster_id] = chosen
    return keywords


def _fallback_label(words: list[str], cluster_id: int) -> str:
    """Join the top keywords, stopping before the name gets too long for a table cell."""
    if not words:
        return f"Topic {cluster_id}"
    parts = [words[0].capitalize()]
    for word in words[1:_KEYWORDS_IN_FALLBACK_LABEL]:
        candidate = " / ".join([*parts, word.capitalize()])
        if len(candidate) > _MAX_FALLBACK_CHARS:
            break
        parts.append(word.capitalize())
    return " / ".join(parts)


def _llm_labels(
    competitor: str,
    keywords: dict[int, list[str]],
    samples: dict[int, list[str]],
) -> dict[int, str]:
    """Ask Claude for cluster names. Raises on any API or parsing failure."""
    from utils.llm import REPAIR_SYSTEM_PROMPT, call_claude, parse_json_object

    blocks = []
    for cluster_id in sorted(keywords):
        quotes = "\n".join(
            f'    - "{s[:_SAMPLE_CHARS].strip()}"' for s in samples.get(cluster_id, [])
        )
        blocks.append(
            f"Cluster {cluster_id}\n"
            f"  keywords: {', '.join(keywords[cluster_id]) or '(none)'}\n"
            f"  sample reviews:\n{quotes}"
        )

    prompt = _USER_PROMPT_TEMPLATE.format(competitor=competitor, clusters="\n\n".join(blocks))
    raw = call_claude(_SYSTEM_PROMPT, prompt, max_tokens=600, label="Topic labels")
    data = parse_json_object(
        raw,
        context="topic labels",
        repair=lambda text: call_claude(REPAIR_SYSTEM_PROMPT, text, max_tokens=600),
    )

    labels: dict[int, str] = {}
    for key, value in data.items():
        try:
            cluster_id = int(key)
        except (TypeError, ValueError):
            continue
        name = " ".join(str(value).split())[:_MAX_LABEL_CHARS]
        if cluster_id in keywords and name:
            labels[cluster_id] = name
    return labels


def _dedupe(labels: dict[int, str]) -> dict[int, str]:
    """Make names unique — modules group by topic_label, so duplicates would merge."""
    seen: dict[str, int] = {}
    result: dict[int, str] = {}
    for cluster_id in sorted(labels):
        name = labels[cluster_id]
        key = name.lower()
        if key in seen or key in (OUTLIER_LABEL, INSUFFICIENT_LABEL):
            seen[key] = seen.get(key, 1) + 1
            name = f"{name} ({seen[key]})"
        else:
            seen[key] = 1
        result[cluster_id] = name
    return result


def label_topics(
    competitor: str,
    texts: list[str],
    clusters: list[int],
    use_llm: bool = True,
) -> dict[int, str]:
    """Return {cluster_id: name} for every cluster id >= 0 in ``clusters``.

    Never raises for LLM problems: a missing API key, an API error or an
    unparseable answer falls back to keyword names (logged), so the pipeline
    keeps working offline and in tests.
    """
    keywords = cluster_keywords(texts, clusters, competitor)
    if not keywords:
        return {}

    labels = {cid: _fallback_label(words, cid) for cid, words in keywords.items()}

    if use_llm:
        samples: dict[int, list[str]] = {}
        for text, cluster in zip(texts, clusters):
            bucket = samples.setdefault(int(cluster), [])
            if cluster >= 0 and len(bucket) < _SAMPLES_PER_CLUSTER:
                bucket.append(str(text))
        try:
            labels.update(_llm_labels(competitor, keywords, samples))
        except Exception as exc:  # noqa: BLE001 — naming must never break the pipeline
            logger.info("[%s] Using keyword topic names (Claude naming unavailable: %s)", competitor, exc)

    return _dedupe(labels)


def relabel_competitor(competitor: str, use_llm: bool = True) -> int:
    """Rename the topics already stored in processed_reviews for one competitor.

    Cheap compared with a full pipeline run: no re-embedding or retraining,
    cluster assignments are left untouched.

    Returns:
        Number of clusters renamed.
    """
    df = query_df(_SELECT_CLUSTERED_SQL, (competitor,))
    if df.empty:
        logger.warning("[%s] No processed reviews to relabel.", competitor)
        return 0

    clusters = pd.to_numeric(df["topic_cluster"], errors="coerce").fillna(-1).astype(int).tolist()
    labels = label_topics(competitor, df["review_text"].tolist(), clusters, use_llm=use_llm)

    params = [(name, competitor, cid) for cid, name in labels.items()]
    # BERTopic outliers keep the reserved label every module filters out —
    # older runs stored keyword strings for cluster -1.
    if any(c == -1 for c in clusters) and labels:
        params.append((OUTLIER_LABEL, competitor, -1))
    executemany(_UPDATE_LABEL_SQL, params)

    for cid, name in sorted(labels.items()):
        logger.info("[%s] cluster %d -> %s", competitor, cid, name)
    return len(labels)
