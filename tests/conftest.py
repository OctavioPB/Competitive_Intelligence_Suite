"""Suite-wide safety net: tests must never reach the real Claude API."""

import pytest


@pytest.fixture(autouse=True)
def _no_real_llm_calls(monkeypatch):
    # Empty, not deleted: python-dotenv never overrides a variable that is
    # already set, so a real key in .env cannot leak back in.
    monkeypatch.setenv("ANTHROPIC_API_KEY", "")
    monkeypatch.setenv("ANTHROPIC_AUTH_TOKEN", "")

    from utils.llm import get_client

    get_client.cache_clear()
    yield
    get_client.cache_clear()
