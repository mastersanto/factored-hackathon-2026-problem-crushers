"""Transcript PDF checks on every evaluation case (specs/002, SC-101..104, SC-107).

For each case, the conversation's events go through the same recorder the API uses (which keeps only
what the customer is sent), then the PDF is signed and rendered. Measured:

- complete: every assistant message, statement label and source, candidate, verdict, and case number
  appears in the PDF, in order (SC-102). Text extraction is used here as a measurement only;
  verification itself never relies on it.
- internal: no internal marker (case types, priority, risk, compliance terms) and no other
  customer's ID in anything the assistant said or in the header (SC-103).
- masked: a seeded card number or code never appears, in the pages or the embedded data (SC-104).
- verifies: the original verifies as a match, and four tampered copies fail (SC-107): an edited
  visible message, edited embedded data, a swapped reference, and a copy re-saved by another tool.
- ms: time to sign and render (SC-101).
"""
from __future__ import annotations

import copy
import io
import re
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

import pypdf

from app.transcript.fingerprint import FingerprintRegister, embedded_json, fingerprint, sign
from app.transcript.labels import labels
from app.transcript.record import TranscriptRecorder
from app.transcript.render import _Doc, render
from app.transcript.verify import verify

CASE_TYPES = ("unrecognized_charge", "fraud_suspected", "compliance_review", "fake_contact_secret_shared",
              "technical_fallback", "recurring_charge", "bank_fee")
INTERNAL = re.compile(r"\b(" + "|".join(CASE_TYPES) + r"|priority|probability|risk_estimate|under_review|flagged|compliance|aml|"
                      r"lavado|cumplimiento|lavagem)\b", re.I)
CUSTOMER_ID = re.compile(r"CLI-[A-Z0-9]{6,}")
_REGISTER = FingerprintRegister(Path(tempfile.mkdtemp()) / "transcripts.jsonl")


def _squash(s: str) -> str:
    return " ".join(s.split())


def _pages_text(pdf: bytes) -> str:
    return _squash(" ".join(p.extract_text() for p in pypdf.PdfReader(io.BytesIO(pdf)).pages))


def _forged(visible: dict, embedded: dict) -> bytes:
    doc = _Doc(visible)
    doc.add_page()
    doc.body()
    doc.embed_file(bytes=embedded_json(embedded), basename="transcript.json", mime_type="application/json",
                   modification_date=datetime.fromisoformat(visible["generated_at"]))
    return bytes(doc.output())


def _in_order(text: str, needles: list[str]) -> bool:
    pos = 0
    for n in needles:
        i = text.find(n, pos)
        if i < 0:
            return False
        pos = i
    return True


def check_case(case: dict, turns: list[dict], customer) -> dict:
    rec = TranscriptRecorder()
    for t in turns:
        rec.begin(t["text"])
        for e in t["events"]:
            rec.record(e)
        rec.commit()
    t0 = time.perf_counter()
    signed, fp = sign(rec.snapshot(conversation_ref="CONV-EVAL0001", first_name=customer.first_name,
                                   country=customer.country, generated_at=datetime.now(timezone.utc)))
    pdf = render(signed)
    ms = (time.perf_counter() - t0) * 1000
    _REGISTER.add(signed, fp)
    L = labels(signed["lang"])
    text = _pages_text(pdf)

    needles: list[str] = []
    for e in signed["entries"]:
        if e["kind"] == "message":
            needles.append(_squash(e["text"])[:60])
            for st in e["statements"]:  # each label, then its own source
                needles.append(_squash(f'[{L["basis"][st["basis"]]}] {st["text"]}')[:50])
                if st.get("source"):
                    needles.append(st["source"])
        elif e["kind"] == "candidates":
            needles += [_squash(f'{c["option"]}. {c["amount"]} · {c["merchant"]}') for c in e["items"]]
        elif e["kind"] == "verdict":
            needles.append(L["verdict"].get(e["verdict"], e["verdict"]))
        elif e["kind"] == "handoff":
            needles.append(L["handoff"].format(case=e["case_id"]))
        elif e["kind"] == "notice":
            needles.append(_squash(e["text"])[:60])
    complete = _in_order(text, needles) and all(c in text for c in signed["case_ids"])

    # What the assistant said and the header, not the customer's own words (a customer may type another ID).
    customer_words = {_squash(e["text"]) for e in signed["entries"] if e["kind"] == "customer"}
    said = text
    for w in sorted(customer_words, key=len, reverse=True):
        said = said.replace(w, " ")
    assistant_data = [e for e in signed["entries"] if e["kind"] != "customer"]
    internal = bool(INTERNAL.search(said) or INTERNAL.search(str(assistant_data)) or CUSTOMER_ID.search(said))

    secret = case["expected"].get("seeded_secret")
    raw = embedded_json(signed).decode()
    masked = None if not secret else (secret not in text.replace(" ", "") and secret not in raw.replace(" ", "") and signed["masked"])

    original = verify(pdf, _REGISTER)["result"] == "match"
    edited = copy.deepcopy(signed)
    first = next(e for e in edited["entries"] if e["kind"] in ("message", "customer"))
    first["text"] = first["text"] + "."
    swapped = copy.deepcopy(signed)
    swapped["conversation_ref"] = "CONV-EVAL0002"
    writer = pypdf.PdfWriter(clone_from=pypdf.PdfReader(io.BytesIO(pdf)))
    resaved = io.BytesIO()
    writer.write(resaved)
    tampers = [_forged(edited, signed), render(edited), render(swapped), resaved.getvalue()]
    caught = sum(verify(t, _REGISTER)["result"] == "altered" for t in tampers)

    return {"complete": complete, "internal_leak": internal, "masked": masked, "verifies": original,
            "tampers": len(tampers), "tampers_caught": caught, "ms": round(ms, 1),
            "compliance": case["category"] == "compliance_review", "fingerprint_ok": bool(fp)}
