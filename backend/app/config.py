"""Settings, read from environment variables. Nothing secret has a default."""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
REPO_DIR = BACKEND_DIR.parent


def load_env_files(*paths: Path) -> None:
    """Load KEY=VALUE lines from local env files (git-ignored). Variables already set in the
    environment win, so a deployment's real environment is never overridden by a stray file."""
    for path in paths:
        if not path.is_file():
            continue
        for line in path.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key, value = key.removeprefix("export ").strip(), value.strip().strip('"').strip("'")
            if key and value and key not in os.environ:
                os.environ[key] = value


load_env_files(REPO_DIR / ".env.local", REPO_DIR / ".env")


def normalize_credentials(names=("ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN")) -> None:
    """Strip whitespace and surrounding quotes from credentials. `docker --env-file` and some hosts pass
    KEY="value" through literally, which the API then rejects as an invalid key."""
    for name in names:
        value = os.environ.get(name)
        if value is not None:
            os.environ[name] = value.strip().strip('"').strip("'").strip()


normalize_credentials()


@dataclass(frozen=True)
class Settings:
    # Local read-only mirror of the organizers' dataset (never inside this repository).
    mirror_dir: Path = Path(os.environ.get("DATA_MIRROR", Path.home() / "factored-hackathon-2026-scratch" / "data")).expanduser()
    # Parquet warehouse built from the mirror; git-ignored.
    warehouse_dir: Path = Path(os.environ.get("WAREHOUSE_DIR", BACKEND_DIR / "data" / "warehouse")).expanduser()
    # Models (the owner's choice, docs/build-plan.md): Haiku understands, Sonnet phrases.
    understand_model: str = os.environ.get("UNDERSTAND_MODEL", "claude-haiku-4-5")
    phrase_model: str = os.environ.get("PHRASE_MODEL", "claude-sonnet-5-5")
    # The LLM is used only when credentials exist; otherwise rules and templates run.
    llm_enabled: bool = bool(os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_AUTH_TOKEN")) and os.environ.get("LLM_DISABLED") != "1"
    session_ttl_seconds: int = int(os.environ.get("SESSION_TTL_SECONDS", "1800"))
    # How far back a customer's questioned charge may be (days before their latest transaction).
    lookback_days: int = int(os.environ.get("LOOKBACK_DAYS", "90"))


settings = Settings()
