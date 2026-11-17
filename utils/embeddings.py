"""Process-wide sentence-transformer singleton.

The pipeline (sentiment, BERTopic) and the Feature Wish Miner all use the same
~90 MB model; loading it once here avoids holding several copies in memory.
"""

from functools import lru_cache
from typing import Any

EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"


@lru_cache(maxsize=1)
def get_embedding_model() -> Any:
    """Load the shared SentenceTransformer on first use and reuse it afterwards.

    Raises:
        ImportError: If sentence_transformers is not installed.
    """
    from sentence_transformers import SentenceTransformer  # heavy — import lazily

    return SentenceTransformer(EMBEDDING_MODEL_NAME)
