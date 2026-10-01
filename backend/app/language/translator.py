"""Translator: verified statements -> wording in the language asked for (research R1, R6).

Every assistant statement keeps a recipe: its template key (or `rule:<id>` for a country right) and the raw
verified values it was built from. Rendering a recipe is deterministic and needs no model, so earlier messages
can be re-shown in another language with exactly the same facts, sources, and labels.
"""
from __future__ import annotations

import re
from datetime import datetime

from app.policy import rules as policy
from app.workflow import messages as M


def _dt(value) -> datetime:
    return value if isinstance(value, datetime) else datetime.fromisoformat(value)


def render_text(key: str, params: dict, lang: str) -> str:
    """The wording of one statement in `lang`, from its recipe."""
    if key.startswith("rule:"):
        return policy.rule_text(key.removeprefix("rule:"), lang)
    kw = {}
    for name, value in params.items():
        if name == "currency":
            continue
        if name == "amount":
            kw[name] = M.money(value, params["currency"], lang)
        elif name == "when":
            kw[name] = M.when(_dt(value), lang)
        elif name in ("day", "last"):
            kw[name] = M.day(_dt(value), lang) if value else ""
        elif name == "channel":
            kw[name] = M.CHANNEL_NAMES[lang].get(value, value)
        elif name == "product":
            kw[name] = M.PRODUCT_NAMES[lang].get(value, value)
        elif name == "kind":
            kw[name] = M.TX_KINDS[lang].get(value, value)
        else:
            kw[name] = value
    return M.t(key, lang, **kw)


def render_statement(st, lang: str) -> str:
    return render_text(st.key, st.params, lang)


def render(statements: list, lang: str) -> list:
    """Copies of `statements` worded in `lang`. Basis, source, key, and params are unchanged."""
    return [st.model_copy(update={"text": render_statement(st, lang)}) if st.key else st for st in statements]


# ---- the customer's own words (research R7) -------------------------------------------------------------
NUM_RE = re.compile(r"\d+(?:[.,]\d+)*")


def acceptable_translation(original: str, translated: str | None) -> bool:
    """The same numbers, no new ones, and a plausible length: otherwise no translation is shown."""
    if not translated:
        return False
    if set(NUM_RE.findall(original)) != set(NUM_RE.findall(translated)):
        return False
    return 0.5 * len(original) <= len(translated) <= 2 * len(original) + 20


def translate_customer(session, index: int, masked_text: str, target: str, llm) -> str | None:
    """A marked translation of one customer message, or None. Cached per session, message, and language; only
    the masked text is sent (constitution IV)."""
    key = (index, target)
    if key in session.translations:
        return session.translations[key]
    if llm is None:  # rules mode: no translation, and nothing to cache (a model may be configured later)
        return None
    out = llm.translate(masked_text, target)
    result = out if acceptable_translation(masked_text, out) else None
    session.translations[key] = result
    return result


# ---- the whole conversation in one language (FR-420 to FR-423) -------------------------------------------
def _candidate(item: dict, raw: dict | None, lang: str) -> dict:
    if not raw:
        return item
    when = M.when(_dt(raw["date"]), lang)
    merchant = raw["merchant"] or M.TX_KINDS[lang].get(raw["type"], raw["type"])
    return {"option": item["option"], "transaction_id": "", "when": when, "amount": M.money(raw["amount"], raw["currency"], lang),
            "merchant": merchant, "status": raw["status"]}


def conversation_view(session, lang: str, llm) -> dict:
    """Every turn of the session's conversation, in `lang`, in the event shapes the chat already streams.

    Assistant messages are rebuilt from their recipes (no model): the same statements, bases, and sources, worded
    in `lang`; in their own language they are shown exactly as first sent. Customer messages are shown as written
    in their own language, else as a marked translation, else as written with `translation_missing`."""
    tr = session.transcript
    entries, recipes = tr.entries, tr.recipes
    turns: list[dict] = []
    for i, (e, rc) in enumerate(zip(entries, recipes)):
        kind, own = e["kind"], rc.get("lang", "es")
        at = int(e["ts"] * 1000)
        if kind == "customer":
            turn = {"role": "customer", "text": e["text"], "lang": lang, "at": at}
            if own != lang:
                translated = translate_customer(session, i, e["text"], lang, llm)
                if translated:
                    turn.update(text=translated, translated=True, original={"text": e["text"], "lang": own})
                else:
                    turn.update(lang=own, translation_missing=True)
            turns.append(turn)
            turns.append({"role": "assistant", "lang": lang, "at": at, "events": []})
            continue
        if not turns:  # defensive: an assistant entry always follows a customer one
            turns.append({"role": "assistant", "lang": lang, "at": at, "events": []})
        events = turns[-1]["events"]
        turns[-1]["at"] = at
        if kind == "message":
            if own == lang:
                events.append({"type": "message", "text": e["text"], "statements": e["statements"]})
            else:
                statements = [{**st, "text": render_text(r["key"], r["params"], lang) if r.get("key") else st["text"]}
                              for st, r in zip(e["statements"], rc.get("statements", []))]
                events.append({"type": "message", "text": " ".join(st["text"] for st in statements), "statements": statements})
        elif kind == "candidates":
            raws = rc.get("raw") or [None] * len(e["items"])
            events.append({"type": "candidates", "items": [_candidate(it, r, lang) for it, r in zip(e["items"], raws)]})
        elif kind == "verdict":
            events.append({"type": "verdict", "verdict": e["verdict"], "channel": e.get("channel")})
        elif kind == "handoff":
            events.append({"type": "handoff", "handoff": {"case_id": e["case_id"]}})
        elif kind == "notice":
            text = M.t(e["code"], lang) if e.get("code") in M.T else e["text"]
            events.append({"type": "error", "code": e.get("code"), "text": text})
    for t in turns:  # each finished reply carries its done marker, as when it was streamed
        if t["role"] == "assistant":
            t["events"].append({"type": "done", "stage": None, "suggestions": None, "lang": lang})
    return {"lang": lang, "stage": session.stage, "suggestions": M.QUICK_REPLIES.get(session.stage, {}).get(lang), "turns": turns}
