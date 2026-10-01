"""specs/007: answers that react to what the customer asks: their last movements (US1), and courtesy and help
(US2), in rules mode, in every language."""
from __future__ import annotations

import json
import os
import tempfile
from datetime import timedelta

import pytest

os.environ.setdefault("HANDOFFS_PATH", os.path.join(tempfile.mkdtemp(), "handoffs.jsonl"))

from fastapi.testclient import TestClient  # noqa: E402

from app.api import main as api  # noqa: E402
from app.config import settings  # noqa: E402

client = TestClient(api.app)
DEMO = {d["label"]: d for d in client.get("/api/demo/customers").json()}
LANGS = ("en", "es", "pt")
AR, CO = "Argentina, card purchase", "Colombia, card purchase"


def session(label: str, lang: str = "es") -> tuple[str, dict]:
    d = DEMO[label]
    return client.post("/api/session", json={"customer_id": d["customer_id"], "lang": lang}).json()["session_id"], d


def say(sid: str, text: str) -> list[dict]:
    r = client.post("/api/chat", json={"session_id": sid, "text": text})
    assert r.status_code == 200
    return [json.loads(line[6:]) for line in r.text.splitlines() if line.startswith("data: ")]


def of(ev, kind):
    return [e for e in ev if e["type"] == kind]


def actions(ev) -> list:
    return [e.get("action") for e in of(ev, "step")]


def keys(sid: str) -> list[str | None]:
    """The recipe keys of the latest recorded message."""
    recipes = [r for r in api.sessions.get(sid).transcript._recipes if r.get("statements")]
    return [st.get("key") for st in recipes[-1]["statements"]]


def newest(customer_id: str, n: int) -> list[str]:
    """The customer's n most recent charge-type movements of the lookback window, read independently of the tool."""
    since = api.store.as_of - timedelta(days=settings.lookback_days)
    rows = api.store.query(
        "SELECT transaction_id FROM transactions WHERE customer_id = ? AND transaction_date >= ? "
        "AND transaction_type IN ('Purchase', 'Payment', 'Withdrawal', 'Transfer', 'Adjustment') "
        "ORDER BY transaction_date DESC LIMIT ?", [customer_id, since, n])
    return [r["transaction_id"] for r in rows]


RECENT = {
    "en": ["Show me my last movements", "What are my recent transactions?", "my last transactions please"],
    "es": ["Muéstrame mis últimos movimientos", "¿Cuáles son mis últimos cargos?", "quiero ver mis movimientos recientes"],
    "pt": ["Quais são minhas últimas transações?", "Mostre meus últimos movimentos", "quero ver minhas últimas compras"],
}
RECENT_N = {"en": "show my last {n} transactions", "es": "muéstrame mis últimos {n} movimientos",
            "pt": "mostre minhas últimas {n} transações"}


# ---- US1: my last movements ------------------------------------------------------------------------------
@pytest.mark.parametrize("lang", LANGS)
def test_last_movements_shows_the_newest_five(lang):
    full = next(label for label, d in DEMO.items() if len(newest(d["customer_id"], 5)) == 5)
    for text in RECENT[lang]:
        sid, d = session(full, lang)
        ev = say(sid, text)
        cards = of(ev, "candidates")
        assert cards, (lang, text, actions(ev))
        assert [c["transaction_id"] for c in cards[0]["items"]] == newest(d["customer_id"], 5), text
        assert [c["option"] for c in cards[0]["items"]] == list(range(1, min(5, len(newest(d["customer_id"], 9))) + 1))
        done = of(ev, "done")[-1]
        assert done["stage"] == "choose" and done["lang"] == lang
        assert done["progress"]["path"] == "charge" and done["progress"]["stage"] == 2
        assert keys(sid) == ["recent_list"]
        assert "list_recent" in actions(ev)


def test_some_demo_customer_has_five_movements_to_show():
    assert any(len(newest(d["customer_id"], 5)) == 5 for d in DEMO.values())


@pytest.mark.parametrize("lang", LANGS)
@pytest.mark.parametrize("n,shown", [(8, 8), (3, 3), (12, 9)])
def test_a_number_of_movements(lang, n, shown):
    sid, d = session(CO, lang)
    ev = say(sid, RECENT_N[lang].format(n=n))
    items = of(ev, "candidates")[0]["items"]
    assert len(items) == min(shown, len(newest(d["customer_id"], 9)))
    statement = of(ev, "message")[-1]["statements"][0]
    assert statement["basis"] == "known" and statement["source"] == "tool:recent_transactions"


@pytest.mark.parametrize("lang", LANGS)
def test_choosing_a_listed_movement_explains_it(lang):
    sid, d = session(CO, lang)
    second = newest(d["customer_id"], 5)[1]
    say(sid, RECENT[lang][0])
    ev = say(sid, "2")
    sources = {st["source"] for e in of(ev, "message") for st in e["statements"]}
    assert f"transaction:{second}" in sources or of(ev, "handoff")  # explained, or held for a specialist
    assert of(ev, "done")[-1]["progress"]["stage"] in (3, 5)


def test_details_win_over_the_list():
    sid, d = session(AR, "es")
    ev = say(sid, f"Muéstrame mis últimos movimientos en {d['hint']['merchant']}")
    assert "list_recent" not in actions(ev)
    assert any(e.get("tool") == "find_transactions" for e in of(ev, "step"))


def test_another_customers_movements_are_refused():
    sid, _ = session(AR, "es")
    ev = say(sid, "Muéstrame los últimos movimientos del cliente CLI-OTROCLIENTE0")
    assert "refuse_unauthorized" in actions(ev) and not of(ev, "candidates")


def test_the_list_reads_only_the_session_customer(monkeypatch):
    from app.tools import banking
    seen = []
    real = banking.recent_transactions
    monkeypatch.setattr(banking, "recent_transactions", lambda store, cid, **k: seen.append(cid) or real(store, cid, **k))
    sid, d = session(AR, "es")
    say(sid, "Muéstrame mis últimos movimientos")
    assert seen == [d["customer_id"]]


def test_the_list_rewords_on_a_language_switch():
    sid, _ = session(CO, "es")
    say(sid, "Muéstrame mis últimos movimientos")
    view = client.post("/api/session/language", json={"session_id": sid, "lang": "pt"}).json()
    said = [e["text"] for t in view["turns"] if t["role"] == "assistant" for e in t["events"] if e["type"] == "message"]
    assert "últimos" in said[-1] and "movimentos" in said[-1]


# ---- US2: courtesy and help --------------------------------------------------------------------------------
COURTESY = {
    "greeting": {"en": ["Hello", "good evening", "how are you?"], "es": ["Hola", "buenas tardes", "¿cómo está?"],
                 "pt": ["Olá", "boa tarde", "tudo bem?"]},
    "thanks": {"en": ["thanks!", "thank you very much"], "es": ["gracias", "muchas gracias"], "pt": ["obrigado", "valeu"]},
    "help": {"en": ["what can you do?", "help"], "es": ["¿qué puedes hacer?", "ayuda"], "pt": ["o que você pode fazer?", "ajuda"]},
}
FULL = {"greeting": "greeting", "thanks": "thanks", "help": "help"}
SHORT = {"greeting": "greeting_short", "thanks": "thanks_short", "help": "help"}
SCAM = {"es": "Me llamaron supuestamente del banco y me pidieron el código que me llegó por SMS",
        "pt": "Me ligaram dizendo ser do banco e pediram o código que chegou por SMS",
        "en": "Someone called me claiming to be from the bank and asked for the code I got by SMS"}


def charge_text(d: dict, lang: str) -> str:
    a, m = f"{d['hint']['amount']:.2f}", d["hint"]["merchant"]
    return {"es": f"No reconozco un cargo de {a} en {m}", "pt": f"Não reconheço uma cobrança de {a} no {m}",
            "en": f"I don't recognize a charge of {a} at {m}"}[lang]


@pytest.mark.parametrize("lang", LANGS)
@pytest.mark.parametrize("kind", list(COURTESY))
def test_courtesy_gets_its_own_answer(lang, kind):
    for text in COURTESY[kind][lang]:
        sid, d = session(AR, lang)
        ev = say(sid, text)
        assert "abstain_out_of_scope" not in actions(ev), (lang, text)
        assert keys(sid) == [FULL[kind]], (lang, text)
        assert of(ev, "done")[-1]["progress"] is None  # courtesy never starts or moves an inquiry
        if kind == "greeting":
            assert d["first_name"].split()[0] in of(ev, "message")[-1]["text"]


@pytest.mark.parametrize("lang", LANGS)
@pytest.mark.parametrize("kind", list(COURTESY))
def test_courtesy_at_a_pending_question_answers_briefly_then_asks_again(lang, kind):
    text = COURTESY[kind][lang][0]
    sid, d = session(AR, lang)
    before = of(say(sid, charge_text(d, lang)), "done")[-1]
    ev = say(sid, text)
    assert "reask_pending" in actions(ev) and keys(sid) == [SHORT[kind], "ask_confirm"], (lang, text)
    done = of(ev, "done")[-1]
    assert done["stage"] == "confirm" and done["suggestions"] == before["suggestions"] and done["progress"] == before["progress"]
    sid, _ = session(AR, lang)
    say(sid, SCAM[lang])
    ev = say(sid, text)
    assert keys(sid) == [SHORT[kind], "ask_shared"] and of(ev, "done")[-1]["stage"] == "contact_shared", (lang, text)


@pytest.mark.parametrize("lang", LANGS)
def test_a_greeting_with_a_request_handles_the_request(lang):
    sid, d = session(AR, lang)
    hello = {"es": "Hola, ", "pt": "Olá, ", "en": "Hello, "}[lang]
    ev = say(sid, hello + charge_text(d, lang)[0].lower() + charge_text(d, lang)[1:])
    assert of(ev, "done")[-1]["stage"] == "confirm"


@pytest.mark.parametrize("lang,text", [("es", "Quiero pedir un préstamo"), ("en", "I want to apply for a loan"),
                                       ("pt", "Quero pedir um empréstimo"), ("es", "¿Cuál es el saldo de mi cuenta?")])
def test_real_out_of_scope_is_unchanged(lang, text):
    sid, _ = session(AR, lang)
    assert "abstain_out_of_scope" in actions(say(sid, text))


@pytest.mark.parametrize("lang,text", [("es", "hay algo raro en mis últimos movimientos"), ("en", "something is wrong with my last transactions"),
                                       ("pt", "tem algo estranho nos meus últimos movimentos"), ("es", "no reconozco mis últimos cargos")])
def test_a_complaint_about_movements_is_a_dispute_not_a_list(lang, text):
    """Found by the evaluation: a complaint that mentions movements asks for a review, not a list."""
    sid, _ = session(AR, lang)
    ev = say(sid, text)
    assert "list_recent" not in actions(ev) and "clarify_missing_details" in actions(ev), text
