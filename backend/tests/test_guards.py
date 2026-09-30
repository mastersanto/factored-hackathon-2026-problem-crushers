"""Guards that hold whatever the language model says. A fake model returns the wrong reading on
purpose; the deterministic checks in the engine must still keep the outcome safe."""
from __future__ import annotations

import os
import tempfile
from pathlib import Path

os.environ["LLM_DISABLED"] = "1"

from app.data.store import get_store  # noqa: E402
from app.tools import banking  # noqa: E402
from app.workflow.engine import Engine, HandoffQueue, SessionStore  # noqa: E402
from app.workflow.understanding import understand as rules_understand  # noqa: E402


class MisreadingModel:
    """Understands like the rules, except it reads every reply at the confirmation step as 'it was mine'."""

    usage_log: list = []

    def __init__(self, engine):
        self.engine = engine

    def understand(self, text, stage, merchants, today):
        u = rules_understand(text, merchants, today, "confirm" if stage == "confirm" else None)
        if stage == "confirm":
            u.intent = "confirm_mine"
        u.source = "llm"
        return u

    def phrase(self, lang, statements):
        return None

    @staticmethod
    def faithful(candidate, statements):
        return False


def _engine():
    engine = Engine(get_store(), HandoffQueue(Path(tempfile.mkdtemp()) / "h.jsonl"), None)
    engine.llm = MisreadingModel(engine)
    return engine


def _explained_charge(engine, sessions):
    store = engine.store
    row = store.query("SELECT t.customer_id, t.amount, t.merchant_name FROM transactions t JOIN customers c USING (customer_id) "
                      "WHERE t.transaction_type = 'Purchase' AND t.merchant_name IS NOT NULL AND c.customer_status = 'Active' "
                      "AND t.transaction_date >= ? ORDER BY t.transaction_id LIMIT 1", [store.as_of.replace(day=1)])[0]
    s = sessions.create(banking.get_customer(store, row["customer_id"]))
    events = list(engine.handle(s, f"No reconozco un cargo de {row['amount']:.2f} en {row['merchant_name']}"))
    assert s.stage == "confirm", events
    return s


def test_negation_files_the_claim_even_if_the_model_says_mine():
    engine, sessions = _engine(), SessionStore()
    s = _explained_charge(engine, sessions)
    list(engine.handle(s, "no, no lo reconozco"))
    assert s.stage == "statement"  # the claim proceeds to a person


def test_model_alone_cannot_close_a_case():
    engine, sessions = _engine(), SessionStore()
    s = _explained_charge(engine, sessions)
    events = list(engine.handle(s, "mmm puede ser"))  # the model says "mine"; the rules do not
    assert s.stage == "confirm"
    assert any(e.get("action") == "reconfirm_before_closing" for e in events if e["type"] == "step")


def _reviewed_charge(store):
    """A recent, explainable charge on the synthetic compliance-review list (FR-018)."""
    rows = store.query(
        "SELECT t.customer_id, t.transaction_id, t.amount, t.merchant_name FROM compliance_reviews r "
        "JOIN transactions t USING (transaction_id) JOIN customers c ON c.customer_id = t.customer_id "
        "WHERE t.merchant_name IS NOT NULL AND c.customer_status = 'Active' AND t.transaction_date >= ? "
        "AND t.transaction_type IN ('Purchase', 'Payment') ORDER BY t.transaction_id LIMIT 1",
        [store.as_of.replace(day=1)])
    assert rows, "the warehouse needs the synthetic compliance-review list (make data)"
    return rows[0]


def test_charge_under_compliance_review_is_never_explained():
    engine, sessions = Engine(get_store(), HandoffQueue(Path(tempfile.mkdtemp()) / "h.jsonl"), None), SessionStore()
    row = _reviewed_charge(engine.store)
    s = sessions.create(banking.get_customer(engine.store, row["customer_id"]))
    events = list(engine.handle(s, f"No reconozco un cargo de {row['amount']:.2f} en {row['merchant_name']}"))
    messages = [e for e in events if e["type"] == "message"]
    sources = [st.get("source") or "" for m in messages for st in m["statements"]]
    text = " ".join(m["text"] for m in messages)
    assert not any(row["transaction_id"] in src for src in sources)          # no fact about it is stated
    assert row["merchant_name"] not in text and f"{row['amount']:,.2f}".split(".")[0].replace(",", ".") not in text
    streamed = [e["handoff"] for e in events if e["type"] == "handoff"]
    assert streamed == [{"case_id": streamed[0]["case_id"]}]                  # the customer gets only a case number
    handoffs = [h for h in engine.handoffs.items if h["case_id"] == streamed[0]["case_id"]]
    assert len(handoffs) == 1 and handoffs[0]["case_type"] == "compliance_review"
    assert "review" not in text.lower() and "lavado" not in text.lower()  # no reason is given to the customer
    assert s.stage == "closed"
