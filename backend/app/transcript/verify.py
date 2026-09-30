"""Is this PDF an unaltered transcript issued by this service? (FR-111, research §5)

1. Read the embedded transcript. If the file is not a PDF, is encrypted, or has none: unreadable.
2. If it was issued by a different renderer or schema, it cannot be re-rendered: unknown_version.
3. Recompute the keyed fingerprint. If it doesn't give the embedded check code: altered.
4. Re-render and compare the whole file byte for byte. Comparing only page content misses edits,
   since pages refer to glyphs by index. Any difference: altered, including a copy re-saved by
   another tool (only the original download verifies).

The result never contains message text.
"""
from __future__ import annotations

import hmac
import io
import json

import pypdf

from app.transcript.fingerprint import FingerprintRegister, check_code, fingerprint
from app.transcript.record import RENDERER, SCHEMA
from app.transcript.render import render


def verify(data: bytes, register: FingerprintRegister) -> dict:
    try:
        reader = pypdf.PdfReader(io.BytesIO(data))
        if reader.is_encrypted:
            return {"result": "unreadable"}
        attached = reader.attachments.get("transcript.json")
        if not attached:
            return {"result": "unreadable"}
        signed = json.loads(attached[0])
        if not isinstance(signed, dict):
            return {"result": "unreadable"}
    except Exception:
        return {"result": "unreadable"}

    code = signed.get("check_code") if isinstance(signed.get("check_code"), str) else None
    if signed.get("renderer") != RENDERER or signed.get("schema") != SCHEMA:
        return {"result": "unknown_version", "check_code": code}
    fp = fingerprint(signed)
    if code is None or not hmac.compare_digest(check_code(fp), code):
        return {"result": "altered", "check_code": code}
    try:
        fresh = render(signed)
    except Exception:
        return {"result": "altered", "check_code": code}
    if not hmac.compare_digest(fresh, data):
        return {"result": "altered", "check_code": code}
    return {"result": "match", "check_code": code, "registered": fp in register,
            "generated_at": signed.get("generated_at"), "case_ids": signed.get("case_ids", [])}
