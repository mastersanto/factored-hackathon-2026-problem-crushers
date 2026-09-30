"""Settings, read from environment variables. Nothing secret has a default."""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class Settings:
    # Local read-only mirror of the organizers' dataset (never inside this repository).
    mirror_dir: Path = Path(os.environ.get("DATA_MIRROR", Path.home() / "factored-hackathon-2026-scratch" / "data"))
    # Parquet warehouse built from the mirror; git-ignored.
    warehouse_dir: Path = Path(os.environ.get("WAREHOUSE_DIR", BACKEND_DIR / "data" / "warehouse"))
    # Models (the owner's choice, docs/build-plan.md): Haiku understands, Sonnet phrases.
    understand_model: str = os.environ.get("UNDERSTAND_MODEL", "claude-haiku-4-5")
    phrase_model: str = os.environ.get("PHRASE_MODEL", "claude-sonnet-5-5")
    # The LLM is used only when credentials exist; otherwise rules and templates run.
    llm_enabled: bool = bool(os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_AUTH_TOKEN")) and os.environ.get("LLM_DISABLED") != "1"
    session_ttl_seconds: int = int(os.environ.get("SESSION_TTL_SECONDS", "1800"))
    # How far back a customer's questioned charge may be (days before their latest transaction).
    lookback_days: int = int(os.environ.get("LOOKBACK_DAYS", "90"))


settings = Settings()
