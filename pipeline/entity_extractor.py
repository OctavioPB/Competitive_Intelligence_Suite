"""spaCy NER entity extraction from review text."""

import logging
from functools import lru_cache

logger = logging.getLogger(__name__)

_SPACY_MODEL = "en_core_web_sm"
_ENTITY_TYPES = frozenset({"ORG", "PRODUCT", "GPE", "PERSON"})
_MAX_CHARS = 10_000  # keep single documents well under spaCy's max_length

# Only tok2vec + ner are needed for entities; skipping the rest roughly halves
# per-document time.
_UNUSED_COMPONENTS = ["tagger", "parser", "attribute_ruler", "lemmatizer"]


@lru_cache(maxsize=1)
def _load_nlp():
    """Lazy-load spaCy model once per process."""
    import spacy

    return spacy.load(_SPACY_MODEL, exclude=_UNUSED_COMPONENTS)


def _doc_entities(doc) -> list[dict[str, str]]:
    """Return relevant entities of a parsed doc, deduplicated by (text.lower(), label)."""
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
    return _doc_entities(_load_nlp()(text[:_MAX_CHARS]))


def extract_entities_batch(texts: list[str]) -> list[list[dict[str, str]]]:
    """Run extract_entities on a list of texts using spaCy's pipe() for efficiency.

    Args:
        texts: List of review text strings.

    Returns:
        List of entity lists, one per input text.
    """
    docs = _load_nlp().pipe((t[:_MAX_CHARS] for t in texts), batch_size=64)
    return [_doc_entities(doc) for doc in docs]
