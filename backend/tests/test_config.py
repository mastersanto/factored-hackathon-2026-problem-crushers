import os

from app.config import normalize_credentials


def test_quoted_credentials_are_normalized(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", ' "sk-test-123" ')
    normalize_credentials()
    assert os.environ["ANTHROPIC_API_KEY"] == "sk-test-123"


def test_llm_budget_cap_falls_back_to_rules(monkeypatch):
    from app.config import settings
    from app.llm.claude import Claude
    c = Claude.__new__(Claude)        # no client needed: the guard runs before any call
    c.usage_log = [{"usd": settings.max_llm_usd + 0.01}]
    assert c.over_budget() and c.understand("hola", "start", [], None) is None and c.phrase("es", []) is None
