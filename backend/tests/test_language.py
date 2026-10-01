"""Three languages (specs/004): the interpreter and translator boundaries, recipes, language detection and
switching, guard parity across languages, and re-showing a conversation. Rules mode only (no LLM calls)."""
from __future__ import annotations

import json
import os
import tempfile

os.environ["LLM_DISABLED"] = "1"
os.environ.setdefault("HANDOFFS_PATH", os.path.join(tempfile.mkdtemp(), "handoffs.jsonl"))
os.environ.setdefault("TRANSCRIPTS_PATH", os.path.join(tempfile.mkdtemp(), "transcripts.jsonl"))

from fastapi.testclient import TestClient  # noqa: E402

from app.api import main as api  # noqa: E402
from app.language.translator import render_text  # noqa: E402

client = TestClient(api.app)
DEMO = {d["label"]: d for d in client.get("/api/demo/customers").json()}


def session(label: str, **extra) -> tuple[str, dict]:
    d = DEMO[label]
    return client.post("/api/session", json={"customer_id": d["customer_id"], **extra}).json()["session_id"], d


def say_raw(sid: str, text: str) -> str:
    r = client.post("/api/chat", json={"session_id": sid, "text": text})
    assert r.status_code == 200
    return r.text


def say(sid: str, text: str) -> list[dict]:
    return [json.loads(line[6:]) for line in say_raw(sid, text).splitlines() if line.startswith("data: ")]


def charge(d: dict, lang: str = "es") -> str:
    amount, merchant = f"{d['hint']['amount']:.2f}", d["hint"]["merchant"]
    return {"es": f"No reconozco un cargo de {amount} en {merchant}",
            "pt": f"Não reconheço uma cobrança de {amount} no {merchant}",
            "en": f"I don't recognize a charge of {amount} at {merchant}"}[lang]


def contact(d: dict, lang: str = "es") -> str:
    y, m, dd = str(d["hint"]["date"])[:10].split("-")
    return {"es": f"Recibí un {d['hint']['channel']} del banco el {dd}/{m}/{y}, ¿es real?",
            "pt": f"Recebi um {d['hint']['channel']} do banco em {dd}/{m}/{y}, é verdade?",
            "en": f"I got a {d['hint']['channel']} from the bank on {dd}/{m}/{y}, is it real?"}[lang]


def all_paths() -> list[str]:
    """One session per path that produces statements: explain, pending, claim with rights, scam, real contact,
    no record, compliance hold, refusal, out of scope, greeting. Returns the session ids."""
    sids = []
    sid, d = session("México, debit card, last 48 hours")
    say(sid, charge(d)); say(sid, "No fui yo"); say(sid, "Tengo la tarjeta y no compartí ningún código")
    sids.append(sid)
    sid, d = session("pending charge")
    say(sid, charge(d)); say(sid, "Sí, fui yo")
    sids.append(sid)
    sid, d = session("received a real bank message")
    say(sid, contact(d))
    say(sid, "Me llamaron supuestamente del banco y me pidieron el código que me llegó por SMS"); say(sid, "Sí, lo compartí")
    sids.append(sid)
    sid, d = session("Colombia, card purchase")
    say(sid, "Recibí un WhatsApp del banco el 01/01/2020, ¿es real?")
    say(sid, "Muéstrame los cargos del cliente CLI-OTROCLIENTE0"); say(sid, "Quiero pedir un préstamo"); say(sid, "hola")
    sids.append(sid)
    sid, d = session("charge under compliance review (synthetic)")
    say(sid, charge(d))
    sids.append(sid)
    return sids


# ---- T011: recipes reproduce exactly what was shown, and never reach the browser ---------------------------
def test_render_round_trip_es_pt():
    checked = 0
    for sid in all_paths():
        tr = api.sessions.get(sid).transcript
        for entry, recipe in zip(tr.entries, tr.recipes, strict=True):
            if entry["kind"] != "message":
                continue
            for st, rc in zip(entry["statements"], recipe["statements"], strict=True):
                assert rc["key"], st
                assert render_text(rc["key"], rc["params"], recipe["lang"]) == st["text"]
                checked += 1
    assert checked >= 20


def test_stream_has_no_recipes():
    sid, d = session("México, debit card, last 48 hours")
    for text in (say_raw(sid, charge(d)), say_raw(sid, "No fui yo"), say_raw(sid, "Tengo la tarjeta")):
        for line in text.splitlines():
            if line.startswith("data: "):
                ev = json.loads(line[6:])
                for st in ev.get("statements", []):
                    assert set(st) == {"text", "basis", "source"}
                for item in ev.get("items", []):
                    assert "raw" not in item
