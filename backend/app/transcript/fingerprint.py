"""Check codes for transcript PDFs (FR-111, option B): the bank keeps only a keyed fingerprint of
the conversation, never its text.

- canonical(): the transcript as sorted, compact UTF-8 JSON, without the check code itself.
- fingerprint(): HMAC-SHA256 with TRANSCRIPT_HMAC_KEY. Keyed, so a leaked register cannot confirm a
  guessed conversation, and a code cannot be forged without the bank's secret.
- check_code(): the first 80 bits in Crockford base32, as XXXX-XXXX-XXXX-XXXX.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import logging
import secrets
import threading
from pathlib import Path

from app.config import settings

log = logging.getLogger("transcript")

_CROCKFORD = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"

if settings.transcript_hmac_key:
    _KEY, KEY_MODE = settings.transcript_hmac_key.encode(), "configured"
else:
    _KEY, KEY_MODE = secrets.token_bytes(32), "ephemeral"
    log.warning("TRANSCRIPT_HMAC_KEY is not set: using an ephemeral key; check codes stop verifying after a restart")


def canonical(transcript: dict) -> bytes:
    body = {k: v for k, v in transcript.items() if k != "check_code"}
    return json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def fingerprint(transcript: dict, key: bytes | None = None) -> str:
    return hmac.new(key or _KEY, canonical(transcript), hashlib.sha256).hexdigest()


def check_code(fp_hex: str) -> str:
    n = int(fp_hex[:20], 16)  # the first 80 bits
    chars = "".join(_CROCKFORD[(n >> shift) & 31] for shift in range(75, -1, -5))
    return "-".join(chars[i:i + 4] for i in range(0, 16, 4))


def sign(transcript: dict) -> tuple[dict, str]:
    """Return the transcript with its check code, and the full fingerprint."""
    fp = fingerprint(transcript)
    return {**transcript, "check_code": check_code(fp)}, fp


def embedded_json(signed: dict) -> bytes:
    return json.dumps(signed, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


class FingerprintRegister:
    """Append-only JSON lines: fingerprint, code, references, and time. No message text, name, or amount.
    Always read from disk: after a restart the file is what the bank still holds."""

    def __init__(self, path: Path | None = None):
        self.path = Path(path or settings.transcripts_path)
        self._lock = threading.Lock()

    def _has(self, fp: str) -> bool:
        if not self.path.exists():
            return False
        return any(json.loads(line)["fingerprint"] == fp for line in self.path.read_text().splitlines() if line.strip())

    def add(self, signed: dict, fp: str) -> None:
        with self._lock:
            if self._has(fp):
                return
            record = {"fingerprint": fp, "check_code": signed["check_code"], "conversation_ref": signed["conversation_ref"],
                      "case_ids": signed["case_ids"], "generated_at": signed["generated_at"],
                      "schema": signed["schema"], "renderer": signed["renderer"]}
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with self.path.open("a") as f:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")

    def __contains__(self, fp: str) -> bool:
        with self._lock:
            return self._has(fp)
