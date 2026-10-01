"""HTTP API. Chat replies stream as server-sent events, one event per workflow event.

Run locally:  uvicorn app.api.main:app --reload --port 8000   (from backend/)
"""
from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from datetime import datetime, timedelta, timezone

import time
from collections import defaultdict, deque

from fastapi import FastAPI, File, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from app.config import settings
from app.data.store import get_store
from app.llm.claude import make_llm
from app.tools import banking
from app.transcript import fingerprint as transcript_keys
from app.transcript.fingerprint import FingerprintRegister, sign
from app.transcript.render import file_name, render
from app.transcript.verify import verify
from app.workflow.engine import Engine, HandoffQueue, SessionStore, public_event

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
log = logging.getLogger("api")

app = FastAPI(title="Explain this charge", version="0.1.0")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
                   allow_methods=["*"], allow_headers=["*"], expose_headers=["Content-Disposition", "X-Check-Code"])

store = get_store()
llm = make_llm()
engine = Engine(store, HandoffQueue(), llm)
sessions = SessionStore()
transcripts = FingerprintRegister()  # check-code fingerprints only, never conversation text (specs/002)


class SessionRequest(BaseModel):
    customer_id: str = Field(pattern=r"^CLI-[A-Z0-9]{6,}$")


class TranscriptRequest(BaseModel):
    session_id: str
    conversation_ref: str | None = Field(default=None, max_length=40)


class ChatRequest(BaseModel):
    session_id: str
    text: str = Field(min_length=1, max_length=2000)


@app.get("/api/health")
def health():
    return {"status": "ok", "as_of": store.as_of, "llm_enabled": llm is not None,
            "models": {"understand": settings.understand_model, "phrase": settings.phrase_model} if llm else None,
            "transcript_verification": transcript_keys.KEY_MODE}


# Stable scenario ids for the demo picker (specs/004, T012): the browser shows each in the app language. The
# English `label` stays for the UI checks.
SCENARIOS = {
    "charge flagged by the fraud-risk estimate": "fraud_flagged",
    "pending charge": "pending",
    "México, debit card, last 48 hours": "mx_debit_48h",
    "Colombia, card purchase": "co_purchase",
    "Argentina, card purchase": "ar_purchase",
    "charge under compliance review (synthetic)": "compliance",
    "received a real bank message": "bank_message",
}


@app.get("/api/demo/customers")
def demo_customers():
    """Development-only picker standing in for a trusted identity service: customers whose recent
    data exercises each path of the workflow, with a hint of a charge to ask about."""
    since = store.as_of - timedelta(days=30)
    picks = {
        "charge flagged by the fraud-risk estimate": "t.fraud_score > 30",
        "pending charge": "t.transaction_status = 'Pending' AND t.merchant_name IS NOT NULL",
        "México, debit card, last 48 hours": f"c.country = 'México' AND p.product_type = 'Tarjeta Débito' AND t.transaction_date >= TIMESTAMP '{store.as_of - timedelta(hours=48)}'",
        "Colombia, card purchase": "c.country = 'Colombia' AND t.transaction_type = 'Purchase' AND t.merchant_name IS NOT NULL",
        "Argentina, card purchase": "c.country = 'Argentina' AND t.transaction_type = 'Purchase' AND t.merchant_name IS NOT NULL",
        "charge under compliance review (synthetic)": "t.transaction_id IN (SELECT transaction_id FROM compliance_reviews) AND t.merchant_name IS NOT NULL",
    }
    out = []
    for label, cond in picks.items():
        rows = store.query(
            "SELECT c.customer_id, c.first_name, c.country, t.amount, t.currency, t.merchant_name, t.transaction_date "
            "FROM transactions t JOIN customers c USING (customer_id) JOIN products p USING (product_id) "
            f"WHERE t.transaction_date >= ? AND c.customer_status = 'Active' AND {cond} "
            + ("" if "compliance_reviews" in cond else "AND t.transaction_id NOT IN (SELECT transaction_id FROM compliance_reviews) ") +
            "AND t.transaction_type IN ('Purchase', 'Payment', 'Withdrawal', 'Transfer', 'Adjustment') "
            "ORDER BY t.transaction_date DESC LIMIT 1", [since])
        if rows:
            r = rows[0]
            out.append({"label": label, "scenario": SCENARIOS[label], "customer_id": r["customer_id"], "first_name": r["first_name"], "country": r["country"],
                        "hint": {"amount": r["amount"], "currency": r["currency"], "merchant": r["merchant_name"],
                                 "date": r["transaction_date"]}})
    contact = store.query(
        "SELECT o.customer_id, c.first_name, c.country, o.channel, o.contact_ts FROM outbound_contacts o "
        "JOIN customers c USING (customer_id) WHERE o.contact_ts >= ? AND o.channel IN ('SMS', 'WhatsApp') "
        "ORDER BY o.contact_ts DESC LIMIT 1", [since])
    if contact:
        r = contact[0]
        out.append({"label": "received a real bank message", "scenario": SCENARIOS["received a real bank message"],
                    "customer_id": r["customer_id"], "first_name": r["first_name"],
                    "country": r["country"], "hint": {"channel": r["channel"], "date": r["contact_ts"]}})
    return out


_session_log: dict[str, deque] = defaultdict(deque)


def _client_ip(request: Request) -> str:
    # The hosting proxy (Azure Container Apps ingress) appends the address it saw to X-Forwarded-For.
    # Earlier entries come from the client and can be forged, so only the last one counts.
    fwd = request.headers.get("x-forwarded-for", "")
    return fwd.split(",")[-1].strip() or (request.client.host if request.client else "unknown")


_transcript_log: dict[str, deque] = defaultdict(deque)


def _limit(log_: dict[str, deque], request: Request, per_hour: int, detail: str) -> None:
    """Abuse guard for a public demo link: a bounded number of requests per visitor per hour."""
    ip, now = _client_ip(request), time.time()
    recent = log_[ip]
    while recent and now - recent[0] > 3600:
        recent.popleft()
    if len(recent) >= per_hour:
        raise HTTPException(429, detail)
    recent.append(now)


@app.post("/api/session")
def create_session(req: SessionRequest, request: Request):
    _limit(_session_log, request, settings.sessions_per_ip_hour, "too many sessions; try again later")
    customer = banking.get_customer(store, req.customer_id)
    if not customer:
        raise HTTPException(404, "unknown customer")
    s = sessions.create(customer)
    log.info("session created for %s", customer.customer_id)
    return {"session_id": s.id, "conversation_ref": s.conversation_ref,
            "customer": {"first_name": customer.first_name, "country": customer.country},
            "expires_in_seconds": settings.session_ttl_seconds}


@app.post("/api/chat")
def chat(req: ChatRequest):
    s = sessions.get(req.session_id)
    if not s:
        raise HTTPException(401, "invalid session")

    def stream():
        # The transcript records exactly what is sent, after the internal filter (specs/002, FR-106), and
        # commits the turn when the stream ends, including when the client disconnects.
        s.transcript.begin(req.text)
        try:
            for event in engine.handle(s, req.text):
                if event.get("internal"):  # staff-only trace (risk estimate, compliance holds, case types): never sent
                    continue
                s.transcript.record(event)
                public = public_event(event)
                yield f"event: {public['type']}\ndata: {json.dumps(public, default=str, ensure_ascii=False)}\n\n"
        finally:
            s.transcript.commit()

    return StreamingResponse(stream(), media_type="text/event-stream", headers={"Cache-Control": "no-cache"})


@app.post("/api/transcript")
def transcript_pdf(req: TranscriptRequest, request: Request):
    """The customer's copy of their own conversation, as shown, with a check code (specs/002).
    No model call: the PDF is rendered from what was streamed to this session."""
    s = sessions.get(req.session_id)
    if not s or s.expired():
        raise HTTPException(401, "invalid session")
    if req.conversation_ref and req.conversation_ref != s.conversation_ref:
        s.security_flags.append("transcript_other_conversation")
        log.warning("transcript request for another conversation refused (session %s)", s.conversation_ref)
        raise HTTPException(403, "not your conversation")
    _limit(_transcript_log, request, settings.transcript_requests_per_ip_hour, "too many requests; try again later")
    if not s.transcript.has_turns:
        raise HTTPException(409, "nothing to export yet")
    snapshot = s.transcript.snapshot(conversation_ref=s.conversation_ref, first_name=s.customer.first_name,
                                     country=s.customer.country, generated_at=datetime.now(timezone.utc))
    signed, fp = sign(snapshot)
    pdf = render(signed)
    transcripts.add(signed, fp)
    return Response(pdf, media_type="application/pdf",
                    headers={"Content-Disposition": f'attachment; filename="{file_name(signed)}"',
                             "X-Check-Code": signed["check_code"], "Cache-Control": "no-store"})


MAX_VERIFY_BYTES = 2 * 1024 * 1024


@app.post("/api/transcripts/verify")
async def verify_transcript(request: Request, file: UploadFile = File(...)):
    """Match, altered, unknown version, or unreadable. The upload is not stored, and the answer never
    contains message text. Unauthenticated in the demo, like the specialist queue (docs/limitations.md)."""
    _limit(_transcript_log, request, settings.transcript_requests_per_ip_hour, "too many requests; try again later")
    data = await file.read(MAX_VERIFY_BYTES + 1)
    if len(data) > MAX_VERIFY_BYTES:
        raise HTTPException(413, "file too large")
    return verify(data, transcripts)


@app.get("/api/handoffs")
def handoffs():
    return list(reversed(engine.handoffs.items))


@app.get("/api/metrics")
def metrics():
    usage = llm.usage_log if llm else []
    return {"llm_calls": len(usage), "usd": round(sum(u["usd"] for u in usage), 6), "usd_cap": settings.max_llm_usd,
            "by_model": {m: sum(1 for u in usage if u["model"] == m) for m in {u["model"] for u in usage}}}


# In the container the API also serves the built frontend (one process, one port). Mounted last so
# every /api route above takes precedence. In development the folder is absent and Vite serves the app.
FRONTEND_DIST = Path(os.environ.get("FRONTEND_DIST", Path(__file__).resolve().parents[3] / "frontend" / "dist"))
if FRONTEND_DIST.is_dir():
    app.mount("/", StaticFiles(directory=FRONTEND_DIST, html=True), name="frontend")

