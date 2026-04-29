"""spaCy NER entity extraction from review text."""

import logging
from functools import lru_cache
from typing import Any

logger = logging.getLogger(__name__)

_SPACY_MODEL = "en_core_web_sm"
_ENTITY_TYPES = frozenset({"ORG", "PRODUCT", "GPE", "PERSON"})


@lru_cache(maxsize=1)
def _load_nlp():
    """Lazy-load spaCy model once per process."""
    import spacy

    return spacy.load(_SPACY_MODEL)


def extract_entities(text: str) -> list[dict[str, str]]:
    """Extract named entities from review text using spaCy.

    Filters to entity types relevant to competitive intelligence:
    ORG (companies), PRODUCT (product names), GPE (locations), PERSON.

    Args:
        text: Raw review or post text.

    Returns:
        List of dicts with keys: text (str), label (str).
        Deduplicated by (text.lower(), label) pair.
        Example: [{"text": "Salesforce", "label": "ORG"}]
    """
    nlp = _load_nlp()
    doc = nlp(text[:10_000])  # spaCy default limit protection

    seen: set[tuple[str, str]] = set()
    entities: list[dict[str, str]] = []

    for ent in doc.ents:
        if ent.label_ not in _ENTITY_TYPES:
            continue
        key = (ent.text.lower(), ent.label_)
        if key in seen:
            continue
        seen.add(key)
        entities.append({"text": ent.text, "label": ent.label_})

    return entities


def extract_entities_batch(texts: list[str]) -> list[list[dict[str, str]]]:
    """Run extract_entities on a list of texts using spaCy's pipe() for efficiency.

    Args:
        texts: List of review text strings.

    Returns:
        List of entity lists, one per input text.
    """
    nlp = _load_nlp()
    results: list[list[dict[str, str]]] = []

    for doc in nlp.pipe(texts, batch_size=64):
        seen: set[tuple[str, str]] = set()
        entities: list[dict[str, str]] = []
        for ent in doc.ents:
            if ent.label_ not in _ENTITY_TYPES:
                continue
            key = (ent.text.lower(), ent.label_)
            if key in seen:
                continue
            seen.add(key)
            entities.append({"text": ent.text, "label": ent.label_})
        results.append(entities)

    return results
