"""The dispute-intake workflow: understand -> decide -> act -> verify -> escalate.

The flow is an explicit state machine in code. Models only interpret the customer (understand)
and reword verified facts (phrase); every decision, lookup, rule, and permission is here.
Each turn yields events that the API streams to the browser.
"""
from __future__ import annotations

import json
import os
import re
import secrets
import threading
import time
import unicodedata
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Iterator, Literal

from pydantic import BaseModel, Field

from app.config import BACKEND_DIR, settings
from app.data.store import Store
from app.language.interpreter import interpret
from app.language.translator import render_text
from app.ml.fraud import load_fraud_risk
from app.policy import rules as policy
from app.tools import banking
from app.transcript.record import TranscriptRecorder
from app.workflow import messages as M
from app.workflow.understanding import Understanding

Basis = Literal["known", "guessed", "rule"]


class Statement(BaseModel):
    text: str
    basis: Basis
    source: str | None = None
    # The recipe (specs/004, R6): the template key, or `rule:<id>`, and the raw verified values. Kept server-side
    # so the statement can be re-worded in any language with the same facts; never sent to the browser.
    key: str | None = None
    params: dict = Field(default_factory=dict)


def _st(key: str, lang: str, basis: Basis, source: str | None, **params) -> Statement:
    """A statement built from its recipe, worded in `lang` by the translator (the one path from facts to text)."""
    return Statement(text=render_text(key, params, lang), basis=basis, source=source, key=key, params=params)


Stage = Literal["start", "choose", "confirm", "statement", "contact_shared", "closed"]
InquiryPath = Literal["charge", "contact"]
Outcome = Literal["recognized", "specialist", "urgent", "genuine", "no_record", "warned"]
TOTALS = {"charge": 5, "contact": 4}


@dataclass
class Inquiry:
    """Where the customer's inquiry stands, shown in the progress panel (specs/006, data model).

    - `path` is "charge" or "contact"; `stage` is 1-5 for charge and 1-4 for contact, never above the path's total.
    - `done` is true only at the path's last stage.
    - `outcome` is set exactly when `done` is true; `case` is the case number when the outcome is "specialist"
      or "urgent", None otherwise.
    Set by the engine at the same points that move the workflow stage or file a case, never from reply text."""
    path: InquiryPath
    stage: int
    done: bool = False
    outcome: Outcome | None = None
    case: str | None = None


@dataclass
class Session:
    id: str
    customer: banking.Customer
    created: float = field(default_factory=time.time)
    last_seen: float = field(default_factory=time.time)
    stage: Stage = "start"
    lang: str = "es"
    candidates: list[dict] = field(default_factory=list)
    tx: dict | None = None
    request_text: str = ""
    pending_contact: dict | None = None
    security_flags: list[str] = field(default_factory=list)
    turns: int = 0
    # Printed on transcript PDFs; random and unrelated to the session token, which is a credential.
    conversation_ref: str = field(default_factory=lambda: "CONV-" + "".join(secrets.choice("ABCDEFGHJKLMNPQRSTUVWXYZ23456789") for _ in range(8)))
    # What the customer was shown, in memory only; it expires with the session (specs/002).
    transcript: TranscriptRecorder = field(default_factory=TranscriptRecorder)
    # Translations of the customer's messages for display, by (entry index, language); None records "no usable
    # translation", so it is not tried again (specs/004, research R7). In memory only, like the transcript.
    translations: dict = field(default_factory=dict)
    inquiry: Inquiry | None = None  # None until a message starts one (specs/006)

    def expired(self, now: float | None = None) -> bool:
        return (now or time.time()) - self.last_seen > settings.session_ttl_seconds


class SessionStore:
    def __init__(self):
        self._sessions: dict[str, Session] = {}
        self._lock = threading.Lock()

    def create(self, customer: banking.Customer) -> Session:
        s = Session(id=secrets.token_urlsafe(24), customer=customer)
        with self._lock:
            self._sessions[s.id] = s
        return s

    def get(self, sid: str) -> Session | None:
        with self._lock:
            return self._sessions.get(sid)


class HandoffQueue:
    """Structured handoffs for the human agent. Persisted as JSON lines in the git-ignored data folder."""

    def __init__(self, path: Path | None = None):
        self.path = path or Path(os.environ.get("HANDOFFS_PATH", BACKEND_DIR / "data" / "handoffs.jsonl"))
        path = self.path
        self._lock = threading.Lock()
        self.items: list[dict] = []
        if path.exists():
            self.items = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]

    def add(self, handoff: dict) -> dict:
        with self._lock:
            self.items.append(handoff)
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with self.path.open("a") as f:
                f.write(json.dumps(handoff, default=str, ensure_ascii=False) + "\n")
        return handoff


def public_event(event: dict) -> dict:
    """What the browser receives: the event without the server-side recipes (specs/004, R6). Statements lose
    `key` and `params`, and charge options lose `raw`, so the stream is exactly what it was before. The API
    streams this, and the evaluation grades it."""
    if event.get("type") == "message":
        return {**event, "statements": [{k: v for k, v in st.items() if k not in ("key", "params")} for st in event["statements"]]}
    if event.get("type") == "candidates":
        return {**event, "items": [{k: v for k, v in c.items() if k != "raw"} for c in event["items"]]}
    return event


def progress_view(s: Session) -> dict | None:
    """The inquiry as the browser receives it (specs/006, contracts/http-api.md)."""
    i = s.inquiry
    if i is None:
        return None
    return {"path": i.path, "stage": i.stage, "total": TOTALS[i.path], "done": i.done, "outcome": i.outcome, "case": i.case}


def _case_id() -> str:
    return "CASO-" + secrets.token_hex(3).upper()


def _yes_no(text: str) -> bool | None:
    t = "".join(c for c in unicodedata.normalize("NFD", text.lower()) if unicodedata.category(c) != "Mn").strip()
    if re.match(r"^(no|nao|nunca|para nada|nope|never|i didn't|i did not)\b", t):
        return False
    if re.match(r"^(si|sim|yes|yeah|yep|claro|lo di|le di|passei|compartilhei|i did|i shared|i gave)\b", t):
        return True
    return None


class Engine:
    def __init__(self, store: Store, handoffs: HandoffQueue, llm=None):
        self.store = store
        self.handoffs = handoffs
        self.llm = llm  # app.llm.claude.Claude or None
        self.fraud = load_fraud_risk()  # calibrated risk estimate; falls back to the score >= 50 rule
        self.merchants = [r["merchant_name"] for r in store.query(
            "SELECT DISTINCT merchant_name FROM transactions WHERE merchant_name IS NOT NULL")]

    # ---- helpers --------------------------------------------------------------------------
    def _step(self, name: str, **detail) -> dict:
        return {"type": "step", "step": name, **detail}

    def _internal(self, name: str, **detail) -> dict:
        """A trace step for staff and evaluation only; the API never streams it to the customer."""
        return {"type": "step", "step": name, "internal": True, **detail}

    def _say(self, s: Session, statements: list[Statement], *, verify: bool = True) -> Iterator[dict]:
        """Verify statements, optionally let the LLM reword them, verify again, and emit."""
        problems = [st.text for st in statements if st.basis in ("known", "rule") and not st.source]
        if problems:  # a claimed fact without a record never reaches the customer
            statements = [st for st in statements if st.text not in problems]
        text = " ".join(st.text for st in statements)
        phrased_by = "template"
        if self.llm and verify:
            candidate = self.llm.phrase(s.lang, statements)
            if candidate and self.llm.faithful(candidate, statements):
                text, phrased_by = candidate, "llm"
        yield self._step("verify", unsupported_removed=len(problems), phrased_by=phrased_by)
        yield {"type": "message", "text": text, "statements": [st.model_dump() for st in statements]}

    def _understand(self, s: Session, text: str) -> Understanding:
        return interpret(text, stage=s.stage, merchants=self.merchants, today=self.store.as_of,
                         session_customer_id=s.customer.customer_id, llm=self.llm)

    # ---- inquiry progress (specs/006) ---------------------------------------------------------
    @staticmethod
    def _progress(s: Session, path: InquiryPath, stage: int) -> None:
        """Move the inquiry to `stage`; a closed inquiry, or one on another path, is replaced by a new one."""
        assert 1 <= stage < TOTALS[path], "the last stage is reached only through _finish"
        i = s.inquiry
        if i is None or i.done or i.path != path:
            s.inquiry = Inquiry(path=path, stage=stage)
        else:
            i.stage = stage

    @staticmethod
    def _finish(s: Session, path: InquiryPath, outcome: Outcome, case: str | None = None) -> None:
        assert (case is not None) == (outcome in ("specialist", "urgent")), "a case exactly for specialist and urgent"
        s.inquiry = Inquiry(path=path, stage=TOTALS[path], done=True, outcome=outcome, case=case)

    # ---- main entry -------------------------------------------------------------------------
    def handle(self, s: Session, text: str) -> Iterator[dict]:
        now = time.time()
        if s.expired(now):
            yield {"type": "error", "code": "session_expired", "text": M.t("session_expired", s.lang)}
            return
        if s.turns >= settings.session_max_turns:
            yield {"type": "error", "code": "turn_limit", "text": M.t("turn_limit", s.lang)}
            return
        s.last_seen, s.turns = now, s.turns + 1
        try:
            yield from self._turn(s, text)
        except banking.Unauthorized:
            s.security_flags.append("unauthorized_tool_access")
            yield self._step("decide", action="refuse_unauthorized")
            yield from self._say(s, [_st("unauthorized", s.lang, "rule", "policy:own-data-only")], verify=False)
        except Exception as exc:  # safe fallback: never guess, hand to a person
            case = _case_id()
            handoff = self.handoffs.add(self._handoff(s, case, "technical_fallback", open_questions=[f"System error: {type(exc).__name__}"]))
            self._finish(s, s.inquiry.path if s.inquiry else "charge", "specialist", case)
            yield self._step("escalate", reason="technical_fallback", case_id=case)
            yield self._handoff_event(handoff)
            yield from self._say(s, [_st("fallback", s.lang, "rule", "policy:safe-fallback", case=case)], verify=False)
        yield {"type": "done", "stage": s.stage, "suggestions": M.QUICK_REPLIES.get(s.stage, {}).get(s.lang), "lang": s.lang,
               "progress": progress_view(s)}

    def _turn(self, s: Session, text: str) -> Iterator[dict]:
        u = self._understand(s, text)
        if u.language:  # a clear language switches the conversation at any stage; an unclear one never does (FR-407)
            s.lang = u.language
        yield self._step("understand", intent=u.intent, source=u.source,
                         slots={k: v for k, v in u.model_dump(exclude={"language", "intent", "source"}).items() if v not in (None, False)})

        if u.other_customer_reference:
            s.security_flags.append("other_customer_reference")
            yield self._step("decide", action="refuse_unauthorized")
            yield from self._say(s, [_st("unauthorized", s.lang, "rule", "policy:own-data-only")], verify=False)
            return
        if u.injection_suspected:
            s.security_flags.append("prompt_injection_attempt")  # logged; the text never becomes an instruction

        details = bool(u.amount or u.merchant or u.date)
        # At "did you share anything?", a clear yes or no is the answer, even with a number in it ("I gave them the
        # code 123456"); only an unclear message may start a new contact check or charge search (research R5).
        new_inquiry = u.intent == "check_contact" or (u.intent == "dispute_charge" and details)
        if s.stage == "contact_shared" and (_shared_answer(text) is not None or not new_inquiry):
            yield from self._contact_followup(s, text)
            return
        if s.stage == "contact_shared":
            s.stage, s.pending_contact = "start", None
        if s.stage == "statement":
            yield from self._file_claim(s, text)
            return
        if u.intent == "check_contact":
            yield from self._check_contact(s, u, text)
        elif u.intent == "choose_option" and s.stage == "choose":
            idx = (u.option or 0) - 1
            if 0 <= idx < len(s.candidates):
                yield self._step("decide", action="explain_candidate", option=u.option)
                yield from self._explain(s, s.candidates[idx])
            else:
                yield from self._say(s, [_st("choose", s.lang, "rule", "flow")], verify=False)
        elif u.intent == "confirm_mine" and s.stage == "confirm":
            s.stage = "closed"
            self._finish(s, "charge", "recognized")
            yield self._step("act", action="close_recognized", transaction_id=s.tx["transaction_id"])
            yield from self._say(s, [_st("closed_mine", s.lang, "rule", "policy:recurring-cancel-via-bank")])
        elif u.intent == "reconfirm" and s.stage == "confirm":
            yield self._step("decide", action="reconfirm_before_closing")
            yield from self._say(s, [_st("ask_confirm", s.lang, "rule", "policy:close-needs-clear-yes")], verify=False)
        elif u.intent == "file_claim" and s.stage == "confirm":
            s.stage = "statement"
            self._progress(s, "charge", 4)
            yield self._step("decide", action="collect_statement")
            yield from self._say(s, [_st("ask_statement", s.lang, "rule", "policy:handoff-checklist")], verify=False)
        elif u.intent == "dispute_charge" or u.intent in ("confirm_mine", "file_claim", "choose_option"):
            # Confirming, claiming, or choosing only make sense about a charge already on screen.
            s.request_text = text
            yield from self._find(s, u)
        elif u.intent in ("greeting", "out_of_scope") and s.stage in ("choose", "confirm"):
            yield from self._reask(s, s.stage)  # a pending question is asked again, not dropped (research R5)
        elif u.intent == "greeting":
            yield from self._say(s, [_st("greeting", s.lang, "rule", "flow", name=s.customer.first_name.split()[0])], verify=False)
        else:
            yield self._step("decide", action="abstain_out_of_scope")
            yield from self._say(s, [_st("out_of_scope", s.lang, "rule", "policy:scope")], verify=False)

    REASK = {"choose": ("choose", "flow"), "confirm": ("ask_confirm", "policy:close-needs-clear-yes"),
             "contact_shared": ("ask_shared", "policy:handoff-checklist")}

    def _reask(self, s: Session, question: str) -> Iterator[dict]:
        key, source = self.REASK[question]
        yield self._step("decide", action="reask_pending", question=question)
        yield from self._say(s, [_st("need_answer", s.lang, "rule", "flow"), _st(key, s.lang, "rule", source)], verify=False)

    # ---- dispute path ---------------------------------------------------------------------
    def _find(self, s: Session, u: Understanding) -> Iterator[dict]:
        if not (u.amount or u.merchant or u.date):
            if s.inquiry is None or s.inquiry.done:  # a vague message mid-inquiry doesn't restart it (research R3)
                self._progress(s, "charge", 1)
            yield self._step("decide", action="clarify_missing_details")
            yield from self._say(s, [_st("need_details", s.lang, "rule", "flow")], verify=False)
            return
        date_from = u.date
        date_to = u.date + timedelta(days=1) if u.date else None
        found = banking.find_transactions(self.store, s.customer.customer_id, amount=u.amount, merchant=u.merchant,
                                          date_from=date_from, date_to=date_to)
        yield self._step("act", tool="find_transactions", results=min(len(found), 6))
        self._progress(s, "charge", 2)
        # What the search used, repeated back, and what is still missing (specs/006, research R4).
        searched = {k: v for k, v in (("amount", u.amount), ("merchant", u.merchant),
                                      ("date", u.date.isoformat() if u.date else None)) if v is not None}
        missing = [k for k in ("amount", "merchant", "date") if k not in searched]
        if not found:
            yield from self._say(s, [_st("none_found_with", s.lang, "rule", "tool:find_transactions", searched=searched, missing=missing)], verify=False)
        elif len(found) == 1:
            yield from self._explain(s, found[0])
        elif len(found) <= 5:
            s.stage, s.candidates = "choose", found
            yield {"type": "candidates", "items": [self._card(tx, s.lang, i + 1) for i, tx in enumerate(found)]}
            yield from self._say(s, [_st("choose_with", s.lang, "rule", "flow", searched=searched)], verify=False)
        else:
            yield from self._say(s, [_st("too_many_with", s.lang, "rule", "tool:find_transactions", searched=searched, missing=missing)], verify=False)

    def _card(self, tx: dict, lang: str, n: int) -> dict:
        return {"option": n, "transaction_id": tx["transaction_id"], "when": M.when(tx["transaction_date"], lang),
                "amount": M.money(tx["amount"], tx["currency"], lang), "merchant": tx["merchant_name"] or M.TX_KINDS[lang].get(tx["transaction_type"], tx["transaction_type"]),
                "status": tx["transaction_status"],
                # Raw values (specs/004, R6), kept server-side to re-word the card in any language; never streamed.
                "raw": {"amount": tx["amount"], "currency": tx["currency"], "date": tx["transaction_date"].isoformat(),
                        "merchant": tx["merchant_name"], "type": tx["transaction_type"], "status": tx["transaction_status"]}}

    def _explain(self, s: Session, tx: dict) -> Iterator[dict]:
        if banking.under_compliance_review(self.store, s.customer.customer_id, tx["transaction_id"]):
            yield from self._compliance_hold(s, tx)
            return
        s.tx, s.stage = tx, "confirm"
        self._progress(s, "charge", 3)
        lang, src = s.lang, f"transaction:{tx['transaction_id']}"
        when = tx["transaction_date"].isoformat()
        if tx["merchant_name"]:
            core = _st("tx_core", lang, "known", src, amount=tx["amount"], currency=tx["currency"], merchant=tx["merchant_name"],
                       when=when, city=tx["transaction_city"] or "?", country=tx["transaction_country"], channel=tx["channel"],
                       product=tx["product_type"], last4=tx["last4"])
        else:
            core = _st("tx_core_nomerchant", lang, "known", src, kind=tx["transaction_type"], amount=tx["amount"],
                       currency=tx["currency"], when=when, channel=tx["channel"], product=tx["product_type"], last4=tx["last4"])
        statements = [core]
        if tx["transaction_status"] == "Pending":
            statements.append(_st("pending", lang, "known", src))
        if tx["merchant_name"]:
            h = banking.merchant_history(self.store, s.customer.customer_id, tx["merchant_name"], tx["transaction_date"])
            yield self._step("act", tool="merchant_history", previous=h["previous_count"])
            key = "history_yes" if h["previous_count"] else "history_no"
            statements.append(_st(key, lang, "known", f"history:{tx['merchant_name']}", merchant=tx["merchant_name"],
                                  n=h["previous_count"], last=h["last_date"].isoformat() if h["last_date"] else None))
        # Risk signal from the learned component (docs/model-card.md); an estimate, never a decision.
        p, flagged = self._risk(tx)
        tx["risk"] = {"probability": round(p, 4), "flagged": flagged, "model": self.fraud.name if self.fraud else "rule:fraud_score>=50"}
        yield self._internal("act", tool="fraud_risk", **tx["risk"])
        if flagged:
            statements.append(_st("risk", lang, "guessed", f"model:{tx['risk']['model']}"))
        statements.append(_st("ask_confirm", lang, "rule", "flow"))
        yield self._step("decide", action="explain_transaction", transaction_id=tx["transaction_id"])
        yield from self._say(s, statements)

    def _compliance_hold(self, s: Session, tx: dict) -> Iterator[dict]:
        """FR-018 / constitution III: state nothing about the charge and give no reason (no tipping-off);
        a specialist receives the case with the verified facts, which stay internal."""
        s.tx, s.stage = tx, "closed"
        case = _case_id()
        self._finish(s, "charge", "specialist", case)
        yield self._internal("act", tool="compliance_review", under_review=True)
        yield self._internal("decide", action="withhold_and_escalate")
        handoff = self.handoffs.add(self._handoff(s, case, "compliance_review",
                                                  open_questions=["Charge under compliance review: do not disclose the reason to the customer"]))
        yield self._step("escalate", case_id=case)
        yield self._internal("escalate", case_id=case, case_type="compliance_review", priority=handoff["priority"])
        yield self._handoff_event(handoff)
        yield from self._say(s, [_st("compliance_neutral", s.lang, "rule", "policy:specialist-only", case=case)], verify=False)

    def _risk(self, tx: dict) -> tuple[float, bool]:
        if self.fraud:
            return self.fraud.estimate(tx.get("fraud_score"))
        flagged = (tx.get("fraud_score") or 0) >= 50
        return (1.0 if flagged else 0.0), flagged

    def _file_claim(self, s: Session, statement_text: str) -> Iterator[dict]:
        tx, lang = s.tx, s.lang
        claim_time = self.store.as_of
        shared = _yes_no_shared(statement_text)
        card = banking.card_status(self.store, s.customer.customer_id, tx["product_id"])
        yield self._step("act", tool="card_status", status=card["product_status"])
        rights = policy.rights_for(s.customer.country, tx, claim_time)
        case_type = "fraud_suspected" if (shared or tx.get("risk", {}).get("flagged")) else "unrecognized_charge"
        case = _case_id()
        handoff = self._handoff(
            s, case, case_type, customer_statement=statement_text, shared_secret=shared, card=card,
            rights=[r.id for r in rights], answer_by=policy.answer_deadline(s.customer.country, claim_time),
            open_questions=[q for q, missing in [
                ("Did the customer share a code or click a link?", shared is None),
                ("Authentication method of the transaction (not in the data)", True),
                ("Police report number, if any", "denuncia" not in statement_text.lower() and "boletim" not in statement_text.lower()),
            ] if missing])
        self.handoffs.add(handoff)
        s.stage = "closed"
        self._finish(s, "charge", "specialist", case)
        yield self._step("escalate", case_id=case)
        yield self._internal("escalate", case_id=case, case_type=case_type, priority=handoff["priority"])
        yield self._handoff_event(handoff)
        statements = [_st("handoff_done", lang, "rule", f"handoff:{case}", case=case)]
        statements += [_st(f"rule:{r.id}", lang, "rule", f"rule:{r.id}") for r in rights]
        if case_type == "fraud_suspected":
            statements.append(_st("freeze_hint", lang, "rule", "policy:never-ask-secrets"))
        yield from self._say(s, statements, verify=False)

    # ---- "is this really my bank?" ----------------------------------------------------------
    def _check_contact(self, s: Session, u: Understanding, text: str) -> Iterator[dict]:
        channel = u.channel or "any"
        res = banking.outbound_check(self.store, s.customer.customer_id, channel, u.date, u.asked_for_secret)
        yield self._step("act", tool="outbound_check", verdict=res["verdict"], matches=len(res["matches"]))
        yield {"type": "verdict", "verdict": res["verdict"], "channel": channel}
        lang = s.lang
        if res["verdict"] == "scam_asks_secret":
            st = [_st("verdict_scam_asks_secret", lang, "rule", "policy:never-ask-secrets")]
            if u.shared_secret:
                yield from self._escalate_contact(s, text, channel, st)
                return
            if u.shared_secret is None:
                s.stage, s.pending_contact = "contact_shared", {"channel": channel, "text": text}
                self._progress(s, "contact", 3)
                st.append(_st("ask_shared", lang, "rule", "policy:handoff-checklist"))
            else:
                self._finish(s, "contact", "warned")
            yield from self._say(s, st, verify=False)
        elif res["verdict"] == "bank_contact":
            m = res["matches"][0]
            self._finish(s, "contact", "genuine")
            yield from self._say(s, [_st("verdict_bank_contact", lang, "known", f"outbound:{m['contact_id']}",
                                         channel=m["channel"], day=m["contact_ts"].isoformat())])
        else:
            self._finish(s, "contact", "no_record")
            yield from self._say(s, [_st("verdict_no_record", lang, "known", "outbound:none-in-window", channel=channel)])

    def _contact_followup(self, s: Session, text: str) -> Iterator[dict]:
        shared = _shared_answer(text)
        if shared is None:  # unclear: asked again, never read as "nothing shared" (constitution III)
            yield from self._reask(s, "contact_shared")
            return
        pc = s.pending_contact or {"channel": "any", "text": ""}
        if shared:
            yield from self._escalate_contact(s, pc["text"] + " / " + text, pc["channel"], [])
        else:
            s.stage = "start"
            self._finish(s, "contact", "warned")
            yield from self._say(s, [_st("freeze_hint", s.lang, "rule", "policy:never-ask-secrets")], verify=False)

    def _escalate_contact(self, s: Session, text: str, channel: str, st: list[Statement]) -> Iterator[dict]:
        case = _case_id()
        handoff = self._handoff(s, case, "fake_contact_secret_shared", customer_statement=text, shared_secret=True,
                                contact_channel=channel, open_questions=["Which data or code was shared, and when",
                                                                        "Transactions after the contact to review"])
        handoff["priority"] = "urgent"
        self.handoffs.add(handoff)
        s.stage = "closed"
        self._finish(s, "contact", "urgent", case)
        yield self._step("escalate", case_id=case, urgent=True)  # the customer is told it is urgent (freeze the card)
        yield self._internal("escalate", case_id=case, case_type="fake_contact_secret_shared", priority="urgent")
        yield self._handoff_event(handoff)
        st = st + [_st("verdict_escalated", s.lang, "rule", f"handoff:{case}", case=case)]
        yield from self._say(s, st, verify=False)

    # ---- handoff ----------------------------------------------------------------------------
    @staticmethod
    def _handoff_event(handoff: dict) -> dict:
        """What the customer's device receives: only the case number. The full handoff (case type, risk
        estimate, security flags, internal notes) stays server-side for the specialist: sending it to the
        browser would disclose internal assessments and, for compliance holds, tip off the customer."""
        return {"type": "handoff", "handoff": {"case_id": handoff["case_id"]}}

    def _handoff(self, s: Session, case: str, case_type: str, **extra) -> dict:
        tx = s.tx
        priority = "high" if extra.get("shared_secret") or (tx and tx.get("risk", {}).get("flagged")) else "normal"
        return {
            "case_id": case, "created_at": datetime.now().isoformat(timespec="seconds"), "case_type": case_type,
            "priority": priority, "language": s.lang,
            "customer": {"customer_id": s.customer.customer_id, "first_name": s.customer.first_name,
                         "country": s.customer.country, "segment": s.customer.segment},
            "request": s.request_text,
            "verified_facts": ({"transaction_id": tx["transaction_id"], "date": tx["transaction_date"], "amount": tx["amount"],
                                "currency": tx["currency"], "merchant": tx["merchant_name"], "city": tx["transaction_city"],
                                "country": tx["transaction_country"], "channel": tx["channel"], "status": tx["transaction_status"],
                                "product": tx["product_type"], "last4": tx["last4"]} if tx else None),
            "risk_estimate": (tx or {}).get("risk"),
            "actions_taken": ["transaction located and explained" if tx else "no transaction involved",
                              "customer did not recognize it" if case_type in ("unrecognized_charge", "fraud_suspected") else case_type],
            "security_flags": s.security_flags,
            **{k: v for k, v in extra.items()},
        }


def _shared_answer(text: str) -> bool | None:
    """The answer to "did you share anything?": a leading yes or no, else an explicit "shared" or "didn't share"."""
    answer = _yes_no(text)
    return _yes_no_shared(text) if answer is None else answer


def _yes_no_shared(text: str) -> bool | None:
    t = text.lower()
    # Negatives first: "no compartí" contains "compartí".
    if any(k in t for k in ["no compartí", "no comparti", "no di ", "no le di", "nunca di", "não passei", "nao passei",
                            "não compartilhei", "nao compartilhei", "no hice clic", "não cliquei",
                            "didn't share", "did not share", "haven't shared", "have not shared", "never shared",
                            "didn't give", "did not give", "didn't click", "did not click"]):
        return False
    if any(k in t for k in ["compartí", "comparti", "le di", "di el código", "di el codigo", "passei", "compartilhei",
                            "hice clic", "cliqué", "cliquei", "shared", "i gave", "gave them", "gave the", "clicked"]):
        return True
    return None
