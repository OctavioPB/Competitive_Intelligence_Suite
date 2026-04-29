"""spaCy NER entity extraction from review text."""

import logging

logger = logging.getLogger(__name__)

_SPACY_MODEL = "en_core_web_sm"
_ENTITY_TYPES = {"ORG", "PRODUCT", "GPE", "PERSON"}


def extract_entities(text: str) -> list[dict[str, str]]:
    """Extract named entities from review text using spaCy.

    Filters to entity types relevant to competitive intelligence:
    ORG (companies), PRODUCT (product names), GPE (geopolitical), PERSON.

    Args:
        text: Raw review or post text.

    Returns:
        List of dicts with keys: text (str), label (str).
        Example: [{"text": "Salesforce", "label": "ORG"}]
    """
    raise NotImplementedError("Implement in Sprint 1 — Day 2")
