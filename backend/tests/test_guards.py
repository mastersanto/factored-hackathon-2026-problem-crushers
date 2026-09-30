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
