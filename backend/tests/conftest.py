"""Loaded by pytest before any test module, so it runs before `app.config` is first imported.

- Rules mode, always: `app.config` reads `.env.local`, which can hold a real Anthropic key, and fixes
  `settings.llm_enabled` when first imported. Without this, whichever test module imported it first decided,
  and the suite could call the paid API. The tests must be free and deterministic.
- One process runs every API test from the same test-client address, so the per-visitor session limit is raised
  above what the whole suite opens. The limit itself is tested against this value.
"""
import os

os.environ["LLM_DISABLED"] = "1"
os.environ.setdefault("SESSIONS_PER_IP_HOUR", "300")
