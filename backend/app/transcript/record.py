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

from app.language import LANGS
from app.language.translator import render_text
from app.transcript.mask import mask
from app.workflow import messages as M

SCHEMA = 2
# Bump the suffix whenever the layout changes: verification re-renders byte for byte (research §5). r1 (schema 1)
# is frozen in render_v1.py so PDFs issued before specs/004 keep verifying.
RENDERER = "fpdf2-2.8.9/r2"

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


def _recipe(event: dict) -> dict:
    """What it takes to re-word an entry in another language (specs/004, R6). Kept beside the entries, never
    in them: the entries stay exactly what the customer saw, and are what the PDF records."""
    t = event.get("type")
    if t == "message":
        return {"statements": [{"key": st.get("key"), "params": st.get("params") or {}} for st in event.get("statements", [])]}
    if t == "candidates":
        return {"raw": [c.get("raw") for c in event["items"]]}
    return {}


def _item(item: dict, raw: dict | None, lang: str) -> dict:
    """A charge option re-worded in `lang` from its raw values; the same keys the entry already has."""
    if not raw:
        return item
    return {"option": item["option"], "amount": M.money(raw["amount"], raw["currency"], lang),
            "merchant": raw["merchant"] or M.TX_KINDS[lang].get(raw["type"], raw["type"]),
            "when": M.when(datetime.fromisoformat(raw["date"]), lang), "status": raw["status"]}


class TranscriptRecorder:
    def __init__(self):
        self._lock = threading.Lock()
        self._entries: list[dict] = []
        self._recipes: list[dict] = []  # one per entry: its language and how to re-word it
        self._pending: list[dict] | None = None
        self._pending_recipes: list[dict] = []
        self._pending_masked = False
        self._pending_lang: str | None = None
        self.masked = False
        self.lang = "es"

    def begin(self, text: str, now: float | None = None) -> None:
        masked_text, was_masked = mask(text)
        self._pending = [{"kind": "customer", "ts": now or time.time(), "text": masked_text}]
        self._pending_recipes = [{}]
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
            self._pending_recipes.append(_recipe(event))

    def commit(self) -> None:
        with self._lock:
            if self._pending is None:
                return
            self._entries.extend(self._pending)
            self.masked |= self._pending_masked
            if self._pending_lang in LANGS:
                self.lang = self._pending_lang
            # The turn's language: the language the reply was given in, which the customer's message took too.
            self._recipes.extend({**r, "lang": self.lang} for r in self._pending_recipes)
            self._pending = None

    @property
    def entries(self) -> list[dict]:
        with self._lock:
            return list(self._entries)

    @property
    def recipes(self) -> list[dict]:
        """One per entry, aligned with `entries`: `lang`, plus `statements` (key, params) for messages and
        `raw` for charge options."""
        with self._lock:
            return list(self._recipes)

    @property
    def has_turns(self) -> bool:
        return bool(self.entries)

    @property
    def case_ids(self) -> list[str]:
        return list(dict.fromkeys(e["case_id"] for e in self.entries if e["kind"] == "handoff"))

    def snapshot(self, *, conversation_ref: str, first_name: str, country: str, generated_at: datetime,
                 lang: str | None = None, translations: dict[int, str] | None = None) -> dict:
        """The canonical transcript, schema 2: what gets fingerprinted, rendered, and embedded in the PDF.

        It is in `lang` (the session's language at download; the latest reply's by default), by the same rules as
        re-showing the conversation (specs/004, FR-424, FR-425): assistant messages in another language are rebuilt
        from their recipes, and each customer message keeps its own words (`text`, `original_lang`) plus, when its
        language differs, the translation already made for display or `translation_missing`. No model is called
        here (specs/002, FR-112): only translations already in `translations` are used."""
        lang = lang or self.lang
        translations = translations or {}
        zone_name = TIME_ZONES.get(country, DEFAULT_ZONE)
        zone = ZoneInfo(zone_name)

        def at(ts: float) -> str:
            return datetime.fromtimestamp(ts, zone).isoformat(timespec="seconds")

        with self._lock:
            pairs = list(zip(self._entries, self._recipes))
        entries = []
        for i, (e, rc) in enumerate(pairs):
            out = {"at": at(e["ts"]), **{k: v for k, v in e.items() if k != "ts"}}
            own = rc.get("lang", self.lang)
            if e["kind"] == "customer":
                out["original_lang"] = own
                if own != lang:
                    if translations.get(i):
                        out["translation"] = translations[i]
                    else:
                        out["translation_missing"] = True
            elif own != lang and e["kind"] == "message":
                statements = [{**st, "text": render_text(r["key"], r["params"], lang) if r.get("key") else st["text"]}
                              for st, r in zip(e["statements"], rc.get("statements") or [{}] * len(e["statements"]))]
                if any(r.get("key") for r in rc.get("statements") or []):
                    out["statements"], out["text"] = statements, " ".join(st["text"] for st in statements)
            elif own != lang and e["kind"] == "candidates" and rc.get("raw"):
                out["items"] = [_item(it, raw, lang) for it, raw in zip(e["items"], rc["raw"])]
            elif own != lang and e["kind"] == "notice" and e.get("code") in M.T:
                out["text"] = M.t(e["code"], lang)
            entries.append(out)
        return {"schema": SCHEMA, "renderer": RENDERER, "conversation_ref": conversation_ref,
                "customer": {"first_name": first_name, "country": country}, "time_zone": zone_name,
                "lang": lang, "case_ids": self.case_ids,
                "masked": self.masked, "entries": entries,
                "generated_at": generated_at.astimezone(zone).isoformat(timespec="seconds")}
