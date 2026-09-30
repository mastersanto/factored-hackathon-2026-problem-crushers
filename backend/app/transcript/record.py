"""The conversation as the customer saw it (specs/002 data-model: Transcript, Entry).

The API feeds the recorder only what it streams to the browser, after the internal-event filter, so
nothing the customer never received can be recorded (FR-106). Turns are committed when their stream
ends; a reply still streaming is not exported. Everything lives in the session's memory and expires
with it: no conversation text is written to disk.
"""
from __future__ import annotations

import threading
import time
from datetime import datetime
from zoneinfo import ZoneInfo

from app.transcript.mask import mask

SCHEMA = 1
# Bump the suffix whenever the layout changes: verification re-renders byte for byte (research §5).
RENDERER = "fpdf2-2.8.9/r1"

TIME_ZONES = {"México": "America/Mexico_City", "Mexico": "America/Mexico_City", "Colombia": "America/Bogota",
              "Argentina": "America/Argentina/Buenos_Aires"}
DEFAULT_ZONE = "America/Bogota"


def _entry(event: dict, ts: float) -> dict | None:
    t = event.get("type")
    if t == "message":
        return {"kind": "message", "ts": ts, "text": event["text"],
                "statements": [{"text": st["text"], "basis": st["basis"], "source": st.get("source")}
                               for st in event.get("statements", [])]}
    if t == "candidates":
        return {"kind": "candidates", "ts": ts,
                "items": [{k: c.get(k) for k in ("option", "amount", "merchant", "when", "status")} for c in event["items"]]}
    if t == "verdict":
        return {"kind": "verdict", "ts": ts, "verdict": event["verdict"], "channel": event.get("channel")}
    if t == "handoff":
        return {"kind": "handoff", "ts": ts, "case_id": event["handoff"]["case_id"]}
    if t == "error":
        return {"kind": "notice", "ts": ts, "code": event.get("code"), "text": event["text"]}
    return None  # step events (the trace) and anything else are not part of the conversation


class TranscriptRecorder:
    def __init__(self):
        self._lock = threading.Lock()
        self._entries: list[dict] = []
        self._pending: list[dict] | None = None
        self._pending_masked = False
        self._pending_lang: str | None = None
        self.masked = False
        self.lang = "es"

    def begin(self, text: str, now: float | None = None) -> None:
        masked_text, was_masked = mask(text)
        self._pending = [{"kind": "customer", "ts": now or time.time(), "text": masked_text}]
        self._pending_masked, self._pending_lang = was_masked, None

    def record(self, event: dict, now: float | None = None) -> None:
        if self._pending is None or event.get("internal"):
            return
        if event.get("type") == "done":
            self._pending_lang = event.get("lang") or self._pending_lang
            return
        entry = _entry(event, now or time.time())
        if entry:
            self._pending.append(entry)

    def commit(self) -> None:
        with self._lock:
            if self._pending is None:
                return
            self._entries.extend(self._pending)
            self.masked |= self._pending_masked
            if self._pending_lang in ("es", "pt"):
                self.lang = self._pending_lang
            self._pending = None

    @property
    def entries(self) -> list[dict]:
        with self._lock:
            return list(self._entries)

    @property
    def has_turns(self) -> bool:
        return bool(self.entries)

    @property
    def case_ids(self) -> list[str]:
        return list(dict.fromkeys(e["case_id"] for e in self.entries if e["kind"] == "handoff"))

    def snapshot(self, *, conversation_ref: str, first_name: str, country: str, generated_at: datetime) -> dict:
        """The canonical transcript: what gets fingerprinted, rendered, and embedded in the PDF."""
        zone_name = TIME_ZONES.get(country, DEFAULT_ZONE)
        zone = ZoneInfo(zone_name)

        def at(ts: float) -> str:
            return datetime.fromtimestamp(ts, zone).isoformat(timespec="seconds")

        entries = [{"at": at(e["ts"]), **{k: v for k, v in e.items() if k != "ts"}} for e in self.entries]
        return {"schema": SCHEMA, "renderer": RENDERER, "conversation_ref": conversation_ref,
                "customer": {"first_name": first_name, "country": country}, "time_zone": zone_name,
                "lang": self.lang, "case_ids": self.case_ids,
                "masked": self.masked, "entries": entries,
                "generated_at": generated_at.astimezone(zone).isoformat(timespec="seconds")}
