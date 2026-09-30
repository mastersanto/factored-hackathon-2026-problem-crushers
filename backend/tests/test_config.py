import os

from app.config import normalize_credentials


def test_quoted_credentials_are_normalized(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", ' "sk-test-123" ')
    normalize_credentials()
    assert os.environ["ANTHROPIC_API_KEY"] == "sk-test-123"
