"""Understand step: what the customer means. Rule-based here; app.llm.understand replaces it with
Claude Haiku 4.5 when credentials exist, and falls back to this on any failure."""
from __future__ import annotations

import re
import unicodedata
from datetime import datetime, timedelta
from typing import Literal

from pydantic import BaseModel, Field

Intent = Literal["dispute_charge", "check_contact", "confirm_mine", "file_claim", "choose_option",
                 "provide_statement", "out_of_scope", "greeting", "reconfirm"]


class Understanding(BaseModel):
    language: Literal["es", "pt"] = "es"
    intent: Intent = "dispute_charge"
    amount: float | None = None
    merchant: str | None = None
    date: datetime | None = Field(default=None, description="day the customer refers to")
    channel: Literal["sms", "whatsapp", "email", "push", "call", "any"] | None = None
    asked_for_secret: bool = False
    shared_secret: bool | None = None
    option: int | None = None
    other_customer_reference: bool = False
    injection_suspected: bool = False
    source: Literal["rules", "llm"] = "rules"


def _norm(text: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", text.lower()) if unicodedata.category(c) != "Mn")


PT_MARKERS = ["nao ", "voce", "cobranca", "cartao", "reconheco", "obrigad", "ontem", "hoje", "ligacao",
              "mensagem", "senha", "compra no", "fui eu", "nao fui", "estou", "meu ", "minha ", "ligaram", "dizendo",
              "pediram", "chegou", "do banco", "cobraram", "compartilhei", "voces", "fatura", "tem uma", "apareceu"]
SECRET = ["codigo", "clave", "contrasena", "nip", " pin", "token", "senha", "cvv", "otp"]
CONTACT = ["me llamaron", "llamada", "llamo", "mensaje", "sms", "whatsapp", "correo", "email", "e-mail",
           "me escribieron", "ligacao", "ligaram", "mensagem", "notificacion", "notificacao", "alerta"]
CHANNEL_WORDS = {"whatsapp": "whatsapp", "sms": "sms", "mensaje de texto": "sms", "correo": "email", "email": "email",
                 "e-mail": "email", "llam": "call", "ligac": "call", "ligaram": "call", "push": "push", "notificac": "push"}
MINE = ["fui yo", "si fui", "lo reconozco", "ya lo reconozco", "si es mio", "es mio", "fui eu", "sim, fui", "reconheco",
        "e meu", "era mio", "ya recorde", "ya me acorde", "lembrei"]
CLAIM = ["no fui yo", "no lo reconozco", "no reconozco", "reclamar", "reclamo", "fraude", "robo", "robaron",
         "nao fui eu", "nao reconheco", "contestar", "roubaram", "golpe", "clonaron", "clonada", "no lo hice",
         "no hice", "nao fiz", "no es mio", "nao e meu", "yo no fui", "eu nao"]
# At the confirmation step a bare yes/no answers the question.
CONFIRM_YES = re.compile(r"^\s*(si|sim|claro|correcto|exacto|yes)\b")
CONFIRM_NO = re.compile(r"^\s*(no|nao|nop|negativo)\b")
PROBLEM = ["algo anda mal", "algo errado", "problema", "raro", "estranh", "no entiendo", "nao entendo", "error", "erro "]
INJECTION = ["ignora las instrucciones", "ignore previous", "ignore all", "ignora todo", "system prompt",
             "actua como", "you are now", "olvida tus reglas", "ignore as instrucoes", "developer mode"]
OUT_OF_SCOPE = ["prestamo", "credito nuevo", "invertir", "hipoteca", "abrir una cuenta", "emprestimo", "transferir dinero",
                "hacer una transferencia", "cambiar mi direccion", "saldo de mi cuenta"]
GREETING = ["hola", "buenas", "buenos dias", "ola", "oi", "bom dia"]

AMOUNT_RE = re.compile(r"(?<![\w/])(?:\$|usd|cop|ars|r\$)?\s*(\d{1,3}(?:[.,]\d{3})+(?:[.,]\d{1,2})?|\d+(?:[.,]\d{1,2})?)(?!\s*/)")
DATE_RE = re.compile(r"\b(\d{1,2})[/-](\d{1,2})(?:[/-](\d{2,4}))?\b")
MONTH_NAMES = {m: i + 1 for i, m in enumerate(["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto",
                                               "septiembre", "octubre", "noviembre", "diciembre"])}
MONTH_NAMES.update({m: i + 1 for i, m in enumerate(["janeiro", "fevereiro", "marco", "abril", "maio", "junho", "julho",
                                                    "agosto", "setembro", "outubro", "novembro", "dezembro"])})
MONTH_NAMES["setiembre"] = 9
NAMED_DATE_RE = re.compile(r"\b(\d{1,2})\s+de\s+(" + "|".join(sorted(MONTH_NAMES, key=len, reverse=True)) + r")(?:\s+(?:de|del)\s+(\d{4}))?\b")
CUSTOMER_ID_RE = re.compile(r"\bCLI-[A-Z0-9]{6,}\b", re.I)


def _parse_amount(raw: str) -> float | None:
    s = raw.strip()
    if re.fullmatch(r"\d{1,3}(?:[.,]\d{3})+", s):             # 1.500 / 1,500 / 1.500.000
        return float(re.sub(r"[.,]", "", s))
    m = re.fullmatch(r"(\d{1,3}(?:[.,]\d{3})*)[.,](\d{1,2})", s)  # 1.500,50 / 1,500.50 / 99,90
    if m:
        return float(re.sub(r"[.,]", "", m.group(1)) + "." + m.group(2))
    try:
        return float(s)
    except ValueError:
        return None


def understand(text: str, merchants: list[str], today: datetime, expecting: str | None = None,
               session_customer_id: str | None = None) -> Understanding:
    t = f" {_norm(text)} "
    u = Understanding(language="pt" if sum(m in t for m in PT_MARKERS) >= 1 and "usted" not in t else "es")

    ids = {m.upper() for m in CUSTOMER_ID_RE.findall(text)}
    u.other_customer_reference = bool(ids - {(session_customer_id or "").upper()})
    u.injection_suspected = any(k in t for k in INJECTION)

    for m in merchants:
        if _norm(m) in t:
            u.merchant = m
            break
    named = NAMED_DATE_RE.search(_norm(text))
    text_wo_dates = NAMED_DATE_RE.sub(" ", _norm(text))
    text_wo_dates = DATE_RE.sub(" ", text_wo_dates)
    for raw in AMOUNT_RE.findall(text_wo_dates.lower()):
        val = _parse_amount(raw)
        if val and val >= 1 and not (1900 <= val <= 2100 and "." not in raw and "," not in raw):
            u.amount = val
            break
    if "ayer" in t or "ontem" in t:
        u.date = (today - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    elif " hoy " in t or " hoje " in t:
        u.date = today.replace(hour=0, minute=0, second=0, microsecond=0)
    elif named:
        d, mo, y = int(named.group(1)), MONTH_NAMES[named.group(2)], named.group(3)
        year = int(y) if y else (today.year if (mo, d) <= (today.month, today.day) else today.year - 1)
        try:
            u.date = datetime(year, mo, d)
        except ValueError:
            pass
    elif (m := DATE_RE.search(text)):
        d, mo, y = int(m.group(1)), int(m.group(2)), m.group(3)
        year = today.year if not y else (int(y) + 2000 if len(y) == 2 else int(y))
        try:
            u.date = datetime(year, mo, d)
        except ValueError:
            pass

    u.asked_for_secret = any(k in t for k in SECRET) and any(k in t for k in ["pid", "pedi", "solicit", "dame", "dar ", "piden", "pediram", "pediu"])
    # Negatives first: "no comparti" contains "comparti".
    if any(k in t for k in ["no lo di", "no comparti", "nao passei", "nao compartilhei", "no di ", "no le di", "nunca lo di", "nunca di"]):
        u.shared_secret = False
    elif any(k in t for k in ["di el codigo", "le di", "comparti", "passei", "compartilhei", "di mi clave", "si lo di"]):
        u.shared_secret = True
    for word, ch in CHANNEL_WORDS.items():
        if word in t:
            u.channel = ch
            break

    if expecting == "choose" and (m := re.fullmatch(r"\s*(?:la |el |a |o )?(?:opcion |opcao |#)?([1-9])\s*[.)]?\s*", _norm(text))):
        u.intent, u.option = "choose_option", int(m.group(1))
    elif expecting == "statement":
        u.intent = "provide_statement"
    elif expecting == "confirm" and CONFIRM_NO.match(t.strip()):
        u.intent = "file_claim"
    elif expecting == "confirm" and CONFIRM_YES.match(t.strip()) and not any(k in t for k in CLAIM):
        u.intent = "confirm_mine"
    elif any(k in t for k in CONTACT) and any(k in t for k in ["banco", "bank", "del banco", "do banco", "supuestamente", "decia ser", "dizia ser"]):
        u.intent = "check_contact"
    elif any(k in t for k in CLAIM):  # before MINE: "no fui yo" contains "fui yo"
        u.intent = "file_claim" if expecting == "confirm" else "dispute_charge"
    elif any(k in t for k in MINE):
        u.intent = "confirm_mine"
    elif any(k in t for k in OUT_OF_SCOPE):
        u.intent = "out_of_scope"
    elif u.amount or u.merchant or any(k in t for k in ["cargo", "cobro", "compra", "cobranca", "debito", "movimiento", "transaccion", "movimentacao"]) or any(k in t for k in CLAIM) or any(k in t for k in PROBLEM):
        u.intent = "dispute_charge"
    elif any(t.strip().startswith(g) for g in GREETING):
        u.intent = "greeting"
    else:
        u.intent = "out_of_scope"
    return u
