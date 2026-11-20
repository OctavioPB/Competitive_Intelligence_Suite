"""Suite-wide safety nets: tests never reach the real Claude API, and never read
or write the developer's real database."""

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


@pytest.fixture(autouse=True)
def _isolated_database(tmp_path, monkeypatch):
    # A fresh, empty SQLite file per test. Tests that need tables call
    # init_schema(); tests that need DEMO_MODE=true set it themselves.
    monkeypatch.setenv("DEMO_MODE", "false")
    monkeypatch.setenv("DATABASE_URL", str(tmp_path / "isolated.db"))


@pytest.fixture(autouse=True)
def _auth_off_by_default(monkeypatch):
    # Most tests exercise features, not sign-in; tests/test_platform.py turns auth on.
    monkeypatch.setenv("AUTH_DISABLED", "true")
    from modules.auth import reset_limiter

    reset_limiter()
