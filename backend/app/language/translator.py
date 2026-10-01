"""Translator: verified statements -> wording in the language asked for (research R1, R6).

Every assistant statement keeps a recipe: its template key (or `rule:<id>` for a country right) and the raw
verified values it was built from. Rendering a recipe is deterministic and needs no model, so earlier messages
can be re-shown in another language with exactly the same facts, sources, and labels.
"""
from __future__ import annotations

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
