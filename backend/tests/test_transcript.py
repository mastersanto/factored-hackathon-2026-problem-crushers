"""Transcript PDF (specs/002): masking, recording, rendering, check codes, verification, and the API.
Rules mode only (no LLM calls); every file is written to a temporary folder."""
from __future__ import annotations

import os
import tempfile

os.environ["LLM_DISABLED"] = "1"
os.environ.setdefault("HANDOFFS_PATH", os.path.join(tempfile.mkdtemp(), "handoffs.jsonl"))
os.environ.setdefault("TRANSCRIPTS_PATH", os.path.join(tempfile.mkdtemp(), "transcripts.jsonl"))

from app.transcript.mask import mask  # noqa: E402
from app.transcript.record import TranscriptRecorder  # noqa: E402


# ---- masking (FR-107) ------------------------------------------------------------------------
def test_mask_card_numbers_keep_last_four():
    for raw in ["4111111111111111", "4111 1111 1111 1111", "4111-1111-1111-1111", "5500 0000 0000 0004"]:
        out, masked = mask(f"mi tarjeta es {raw} gracias")
        assert masked and raw not in out and out.endswith(f"•••• {raw[-4:]} gracias")


def test_mask_codes_near_keywords_in_both_languages():
    cases = ["Compartí el código 482913 por teléfono", "le di la clave 1234", "mi PIN es 9876", "482913 era el código",
             "passei a senha 739201", "o código de verificação é 55123", "me pidieron el OTP: 112233", "el NIP 4455"]
    for text in cases:
        out, masked = mask(text)
        assert masked, text
        assert not any(ch.isdigit() for ch in out), (text, out)
        assert "••••" in out


def test_mask_leaves_amounts_dates_and_plain_text():
    for text in ["No reconozco un cargo de 1.250 en Uber", "un cobro de $ 1,250.00 el 14 de septiembre",
                 "Não reconheço uma compra de 89,90 em 2026-09-14", "fue el 12/09 en Rappi", "Sí, fui yo"]:
        out, masked = mask(text)
        assert out == text and not masked, text


# ---- recorder (FR-102, FR-106) ------------------------------------------------------------------
def _turn(rec: TranscriptRecorder, text: str, events: list[dict], *, commit: bool = True):
    rec.begin(text)
    for e in events:
        rec.record(e)
    if commit:
        rec.commit()


MSG = {"type": "message", "text": "Es un cargo de 1.250,00 ARS en Uber.",
       "statements": [{"text": "Cargo de 1.250,00 ARS en Uber", "basis": "known", "source": "transaction:TX-1"},
                      {"text": "Plazo de respuesta: 10 días", "basis": "rule", "source": "rule:AR-1"}]}


def test_recorder_keeps_only_customer_visible_kinds():
    rec = TranscriptRecorder()
    _turn(rec, "No reconozco un cargo", [
        {"type": "step", "step": "understand", "intent": "dispute_charge"},
        {"type": "step", "step": "escalate", "internal": True, "case_type": "compliance_review", "priority": "high"},
        MSG,
        {"type": "candidates", "items": [{"option": 1, "transaction_id": "TX-9", "when": "ayer", "amount": "10,00 ARS",
                                          "merchant": "Uber", "status": "Pending"}]},
        {"type": "verdict", "verdict": "no_record", "channel": "SMS"},
        {"type": "handoff", "handoff": {"case_id": "CASO-ABC123"}},
        {"type": "error", "code": "turn_limit", "text": "Se alcanzó el límite"},
        {"type": "done", "stage": "closed", "suggestions": None, "lang": "pt"},
    ])
    kinds = [e["kind"] for e in rec.entries]
    assert kinds == ["customer", "message", "candidates", "verdict", "handoff", "notice"]
    flat = repr(rec.entries)
    assert "compliance_review" not in flat and "priority" not in flat and "intent" not in flat
    assert "TX-9" not in flat  # the candidate's record id is not shown in the chat
    assert rec.entries[4] == {"kind": "handoff", "ts": rec.entries[4]["ts"], "case_id": "CASO-ABC123"}
    assert rec.case_ids == ["CASO-ABC123"] and rec.lang == "pt"


def test_recorder_commits_only_finished_turns_and_masks_customer_text():
    rec = TranscriptRecorder()
    assert not rec.has_turns
    _turn(rec, "Compartí el código 482913", [MSG], commit=False)
    assert not rec.has_turns and rec.entries == []  # a reply still streaming is not exported
    rec.commit()
    assert rec.has_turns and rec.masked
    assert "482913" not in rec.entries[0]["text"]


def test_snapshot_shape_and_time_zone():
    from datetime import datetime, timezone
    rec = TranscriptRecorder()
    _turn(rec, "hola", [MSG, {"type": "done", "stage": "confirm", "suggestions": None, "lang": "es"}])
    snap = rec.snapshot(conversation_ref="CONV-TEST0001", first_name="Ana", country="Colombia",
                        generated_at=datetime(2026, 9, 30, 19, 15, tzinfo=timezone.utc))
    assert set(snap) == {"schema", "renderer", "conversation_ref", "customer", "time_zone", "lang", "case_ids",
                         "masked", "entries", "generated_at"}
    assert snap["customer"] == {"first_name": "Ana", "country": "Colombia"}
    assert snap["time_zone"] == "America/Bogota" and snap["generated_at"] == "2026-09-30T14:15:00-05:00"
    assert all("ts" not in e and e["at"].endswith("-05:00") for e in snap["entries"])


# ---- through the API ------------------------------------------------------------------------
import json  # noqa: E402

from fastapi.testclient import TestClient  # noqa: E402

from app.api import main as api  # noqa: E402

client = TestClient(api.app)
DEMO = {d["label"]: d for d in client.get("/api/demo/customers").json()}


def _session(label: str) -> tuple[str, dict, dict]:
    d = DEMO[label]
    body = client.post("/api/session", json={"customer_id": d["customer_id"]}).json()
    return body["session_id"], d, body


def _say(sid: str, text: str) -> list[dict]:
    r = client.post("/api/chat", json={"session_id": sid, "text": text})
    assert r.status_code == 200
    return [json.loads(line[6:]) for line in r.text.splitlines() if line.startswith("data: ")]


def _ask_about(sid: str, d: dict) -> list[dict]:
    return _say(sid, f"No reconozco un cargo de {d['hint']['amount']:.2f} en {d['hint']['merchant']}")


def test_compliance_hold_never_reaches_the_transcript():
    sid, d, _ = _session("charge under compliance review (synthetic)")
    _ask_about(sid, d)
    entries = api.sessions.get(sid).transcript.entries
    flat = json.dumps(entries, ensure_ascii=False).lower()
    assert any(e["kind"] == "handoff" for e in entries)  # the customer sees the case number
    for word in ("compliance", "review", "aml", "lavado", "priority", "risk", "case_type"):
        assert word not in flat, word


def test_done_event_carries_language():
    sid, d, _ = _session("Colombia, card purchase")
    ev = _say(sid, f"Não reconheço uma compra de {d['hint']['amount']:.2f} em {d['hint']['merchant']}")
    assert ev[-1]["type"] == "done" and ev[-1]["lang"] == "pt"
    assert api.sessions.get(sid).transcript.lang == "pt"


# ---- rendering and download (US1: FR-101..104, FR-110, FR-112, SC-101) --------------------------
import copy  # noqa: E402
import io  # noqa: E402
import subprocess  # noqa: E402
import sys  # noqa: E402
import time  # noqa: E402
from datetime import datetime, timezone  # noqa: E402
from pathlib import Path  # noqa: E402

import pypdf  # noqa: E402
import pytest  # noqa: E402

from app.llm.claude import PROMISES  # noqa: E402
from app.transcript import fingerprint as fpmod  # noqa: E402
from app.transcript.fingerprint import FingerprintRegister, canonical, check_code, embedded_json, fingerprint, sign  # noqa: E402
from app.transcript.labels import LABELS  # noqa: E402
from app.transcript.render import _Doc, render  # noqa: E402
from app.transcript.verify import verify  # noqa: E402


@pytest.fixture(autouse=True)
def _fresh_rate_limits():
    api._transcript_log.clear()
    yield
    api._transcript_log.clear()


def _download(sid: str, ref: str | None = None):
    return client.post("/api/transcript", json={"session_id": sid, **({"conversation_ref": ref} if ref else {})})


def _text(pdf: bytes) -> str:
    """Diagnostic only (never the check): the PDF's text, whitespace collapsed."""
    return " ".join(" ".join(p.extract_text() for p in pypdf.PdfReader(io.BytesIO(pdf)).pages).split())


def _claim(label: str = "Colombia, card purchase"):
    sid, d, body = _session(label)
    streamed = _ask_about(sid, d) + _say(sid, "No fui yo") + _say(sid, "Tengo la tarjeta conmigo y no compartí ningún código.")
    return sid, d, body, streamed


def test_download_contains_the_conversation_as_shown():
    sid, d, body, streamed = _claim()
    r = _download(sid, body["conversation_ref"])
    assert r.status_code == 200 and r.headers["content-type"] == "application/pdf"
    assert r.headers["content-disposition"].startswith(f'attachment; filename="conversacion-{body["conversation_ref"]}-')
    code = r.headers["x-check-code"]
    text = _text(r.content)
    squash = lambda s: " ".join(s.split())  # noqa: E731
    messages = [e for e in streamed if e["type"] == "message"]
    positions = [text.find(squash(m["text"])[:60]) for m in messages]
    assert all(p >= 0 for p in positions) and positions == sorted(positions)  # every reply, in order
    for m in messages:
        for st in m["statements"]:
            assert f'[{LABELS["es"]["basis"][st["basis"]]}] {squash(st["text"])[:40]}' in text
            if st.get("source"):
                assert st["source"] in text
    case = next(e["handoff"]["case_id"] for e in streamed if e["type"] == "handoff")
    assert case in text and f"{LABELS['es']['check_code']}: {code}" in text
    assert d["first_name"] in text and body["conversation_ref"] in text and "Página 1 de" in text
    assert text.find("No fui yo") < text.find(LABELS["es"]["handoff"].format(case=case))


def test_render_is_byte_identical_and_fast_at_the_turn_limit():
    rec = TranscriptRecorder()
    for i in range(40):
        _turn(rec, f"mensaje {i}", [MSG, {"type": "handoff", "handoff": {"case_id": "CASO-000001"}}], commit=True)
    signed, _ = sign(rec.snapshot(conversation_ref="CONV-TEST0001", first_name="Ana", country="Argentina",
                                  generated_at=datetime(2026, 9, 30, tzinfo=timezone.utc)))
    t = time.perf_counter()
    a = render(signed)
    assert time.perf_counter() - t < 5  # SC-101
    assert a == render(signed)
    assert pypdf.PdfReader(io.BytesIO(a)).attachments["transcript.json"][0] == embedded_json(signed)


def test_download_makes_no_model_call(monkeypatch):
    sid, d, body, _ = _claim()

    class Exploding:
        def __getattr__(self, name):
            raise AssertionError("the transcript must not call a model")
    monkeypatch.setattr(api, "llm", Exploding())
    monkeypatch.setattr(api.engine, "llm", Exploding())
    assert _download(sid).status_code == 200


def test_download_refusals():
    assert _download("not-a-session").status_code == 401
    sid, d, body = _session("Argentina, card purchase")
    assert _download(sid).status_code == 409  # nothing to export yet
    _ask_about(sid, d)
    r = _download(sid, "CONV-SOMEONE1")
    assert r.status_code == 403 and "transcript_other_conversation" in api.sessions.get(sid).security_flags
    api._transcript_log["testclient"].extend([time.time()] * api.settings.transcript_requests_per_ip_hour)
    assert _download(sid).status_code == 429
    api._transcript_log.clear()
    api.sessions.get(sid).last_seen = 0  # expired
    assert _download(sid).status_code == 401


# ---- check codes and verification (US2: FR-104, FR-105, FR-111, SC-107) --------------------------
def _signed(**over) -> dict:
    rec = TranscriptRecorder()
    _turn(rec, "No reconozco un cargo", [MSG, {"type": "handoff", "handoff": {"case_id": "CASO-AAAAAA"}},
                                         {"type": "done", "lang": over.pop("lang", "es")}])
    snap = rec.snapshot(conversation_ref="CONV-TEST0001", first_name="Ana", country="México",
                        generated_at=datetime(2026, 9, 30, 12, tzinfo=timezone.utc))
    return sign({**snap, **over})[0]


def test_fingerprint_is_keyed_canonical_and_stable():
    signed = _signed()
    body = {k: v for k, v in signed.items() if k != "check_code"}
    assert canonical(signed) == canonical(body) and b" " not in canonical({"a": 1, "b": [1, 2]})
    assert canonical({"b": 1, "a": 2}) == b'{"a":2,"b":1}'
    fp = fingerprint(signed)
    assert fp == fingerprint(copy.deepcopy(signed)) and fp != fingerprint(signed, key=b"another key")
    code = check_code(fp)
    assert len(code) == 19 and code.count("-") == 3 and code == signed["check_code"]
    assert set(code.replace("-", "")) <= set("0123456789ABCDEFGHJKMNPQRSTVWXYZ")


def test_same_conversation_same_code_new_message_new_code():
    sid, d, body = _session("Argentina, card purchase")
    _ask_about(sid, d)
    first = _download(sid).headers["x-check-code"]
    time.sleep(1.1)  # a later download of the same content differs only in generation time...
    again = _download(sid).headers["x-check-code"]
    _say(sid, "Sí, fui yo")
    later = _download(sid).headers["x-check-code"]
    assert later not in (first, again)


def test_register_holds_no_conversation_text(tmp_path):
    reg = FingerprintRegister(tmp_path / "t.jsonl")
    signed = _signed()
    fp = fingerprint(signed)
    reg.add(signed, fp)
    reg.add(signed, fp)  # not duplicated
    lines = (tmp_path / "t.jsonl").read_text().splitlines()
    assert len(lines) == 1 and fp in reg
    assert set(json.loads(lines[0])) == {"fingerprint", "check_code", "conversation_ref", "case_ids", "generated_at", "schema", "renderer"}
    for secret in ("Ana", "Uber", "1.250", "No reconozco"):
        assert secret not in lines[0]


def test_missing_key_is_ephemeral_and_reported():
    env = {**os.environ, "TRANSCRIPT_HMAC_KEY": ""}
    out = subprocess.run([sys.executable, "-c", "from app.transcript.fingerprint import KEY_MODE; print(KEY_MODE)"],
                         env=env, capture_output=True, text=True, cwd=Path(__file__).parents[1])
    assert out.stdout.strip() == "ephemeral"
    assert client.get("/api/health").json()["transcript_verification"] == fpmod.KEY_MODE


def _forged(visible: dict, embedded: dict) -> bytes:
    """Visible pages from one transcript, the attachment from another."""
    doc = _Doc(visible)
    doc.add_page()
    doc.body()
    doc.embed_file(bytes=embedded_json(embedded), basename="transcript.json", mime_type="application/json",
                   modification_date=datetime.fromisoformat(visible["generated_at"]))
    return bytes(doc.output())


def test_verify_original_and_every_tamper(tmp_path):
    reg = FingerprintRegister(tmp_path / "t.jsonl")
    signed = _signed()
    original = render(signed)
    reg.add(signed, fingerprint(signed))
    ok = verify(original, reg)
    assert ok["result"] == "match" and ok["registered"] is True and ok["case_ids"] == ["CASO-AAAAAA"]
    (tmp_path / "t.jsonl").unlink()
    assert verify(original, reg) == {**ok, "registered": False}  # still verifies after the register is lost

    edited = copy.deepcopy(signed)
    edited["entries"][1]["text"] = edited["entries"][1]["text"].replace("1.250", "1.259")
    assert verify(_forged(edited, signed), reg)["result"] == "altered"     # (a) visible text changed
    assert verify(render(edited), reg)["result"] == "altered"              # (b) embedded data changed
    swapped = copy.deepcopy(signed)
    swapped["case_ids"] = ["CASO-BBBBBB"]
    swapped["entries"][2]["case_id"] = "CASO-BBBBBB"
    assert verify(render(swapped), reg)["result"] == "altered"             # (c) case number swapped

    writer = pypdf.PdfWriter(clone_from=pypdf.PdfReader(io.BytesIO(original)))
    buf = io.BytesIO()
    writer.write(buf)
    assert verify(buf.getvalue(), reg)["result"] == "altered"              # re-saved by another tool

    assert verify(render({**signed, "renderer": "fpdf2-0.0.0/r0"}), reg)["result"] == "unknown_version"
    assert verify(b"not a pdf", reg) == {"result": "unreadable"}
    plain = _Doc(signed)
    plain.add_page()
    assert verify(bytes(plain.output()), reg) == {"result": "unreadable"}


def test_verify_endpoint_answers_without_message_text():
    sid, d, body, streamed = _claim()
    pdf = _download(sid).content
    r = client.post("/api/transcripts/verify", files={"file": ("c.pdf", pdf, "application/pdf")})
    assert r.status_code == 200 and r.json()["result"] == "match" and r.json()["registered"] is True
    assert set(r.json()) == {"result", "check_code", "registered", "generated_at", "case_ids"}
    flat = r.text
    for e in streamed:
        if e["type"] == "message":
            assert e["text"][:30] not in flat
    assert d["hint"]["merchant"] not in flat and d["first_name"] not in flat
    big = b"%PDF-" + b"0" * (2 * 1024 * 1024)
    assert client.post("/api/transcripts/verify", files={"file": ("b.pdf", big, "application/pdf")}).status_code == 413


def test_first_page_notice_and_masking_note():
    signed = _signed(masked=True)
    text = _text(render(signed))
    for key in ("notice", "keep_original", "masked"):
        assert " ".join(LABELS["es"][key].split())[:50] in text, key


@pytest.mark.parametrize("lang", ["es", "pt"])
def test_notice_never_promises(lang):
    notice = LABELS[lang]["notice"].lower()
    assert not any(p in notice for p in PROMISES)
    must = {"es": ["no decide el reclamo", "no promete ningún resultado"],
            "pt": ["não decide a reclamação", "não promete nenhum resultado"]}[lang]
    assert all(m in notice for m in must)


# ---- language (US3: FR-109) ----------------------------------------------------------------------
def test_portuguese_conversation_gets_portuguese_fixed_texts():
    sid, d, body = _session("Colombia, card purchase")
    _say(sid, f"Não reconheço uma compra de {d['hint']['amount']:.2f} em {d['hint']['merchant']}")
    r = _download(sid)
    assert r.headers["content-disposition"].startswith('attachment; filename="conversa-')
    text = _text(r.content)
    for key in ("title", "assistant_author", "check_code"):
        assert LABELS["pt"][key] in text, key
    assert "[verificado]" in text and LABELS["pt"]["notice"][:40] in text


def test_language_switch_follows_latest_assistant_turn():
    rec = TranscriptRecorder()
    _turn(rec, "No reconozco un cargo", [MSG, {"type": "done", "lang": "es"}])
    _turn(rec, "Não reconheço uma compra", [MSG, {"type": "done", "lang": "pt"}])
    signed = sign(rec.snapshot(conversation_ref="CONV-TEST0001", first_name="Ana", country="Colombia",
                               generated_at=datetime(2026, 9, 30, tzinfo=timezone.utc)))[0]
    text = _text(render(signed))
    assert "No reconozco un cargo" in text and "Não reconheço uma compra" in text  # messages verbatim
    assert LABELS["pt"]["title"] in text and LABELS["es"]["title"] not in text


# ---- the evaluation's transcript check detects what it claims to (Principle V) -----------------
def test_eval_transcript_check_flags_leaks_and_unmasked_secrets():
    from types import SimpleNamespace

    from app.eval import transcript_check as tc

    who = SimpleNamespace(first_name="Ana", country="Colombia")
    turn = {"text": "No reconozco un cargo", "events": [MSG, {"type": "done", "lang": "es"}]}
    clean = tc.check_case({"category": "claim_unrecognized", "expected": {}}, [turn], who)
    assert clean["complete"] and not clean["internal_leak"] and clean["verifies"] and clean["tampers_caught"] == clean["tampers"]
    leaky = {**MSG, "text": "Caso tipo compliance_review, priority urgent"}
    bad = tc.check_case({"category": "compliance_review", "expected": {}}, [{**turn, "events": [leaky]}], who)
    assert bad["internal_leak"]
    seeded = tc.check_case({"category": "contact_scam_secret", "expected": {"seeded_secret": "482913"}},
                           [{"text": "sí, le di el código 482913", "events": [MSG]}], who)
    assert seeded["masked"] is True
