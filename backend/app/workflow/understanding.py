"""Understand step: what the customer means. Rule-based here; app.llm.understand replaces it with
Claude Haiku 4.5 when credentials exist, and falls back to this on any failure."""
from __future__ import annotations

import re
import unicodedata
from datetime import datetime, timedelta
from typing import Literal

from pydantic import BaseModel, Field

Intent = Literal["dispute_charge", "check_contact", "confirm_mine", "file_claim", "choose_option",
                 "provide_statement", "out_of_scope", "greeting", "reconfirm", "list_recent", "thanks", "help"]


class Understanding(BaseModel):
    # The message's language when it is clear; None when it is not (an option number, "ok", an amount). An unclear
    # message never changes the conversation's language (specs/004, FR-407, research R4).
    language: Literal["en", "es", "pt"] | None = None
    intent: Intent = "dispute_charge"
    amount: float | None = None
    merchant: str | None = None
    date: datetime | None = Field(default=None, description="day the customer refers to")
    channel: Literal["sms", "whatsapp", "email", "push", "call", "any"] | None = None
    asked_for_secret: bool = False
    shared_secret: bool | None = None
    option: int | None = None
    count: int | None = None  # how many recent movements were asked for (specs/007)
    other_customer_reference: bool = False
    injection_suspected: bool = False
    source: Literal["rules", "llm"] = "rules"


def _norm(text: str) -> str:
    text = text.lower().replace("\u2019", "'")  # typographic apostrophe: "wasn’t" reads as "wasn't"
    return "".join(c for c in unicodedata.normalize("NFD", text) if unicodedata.category(c) != "Mn")


PT_MARKERS = ["nao ", "voce", "cobranca", "cartao", "reconheco", "obrigad", "ontem", "hoje", "ligacao",
              "mensagem", "senha", "compra no", "fui eu", "nao fui", "estou", "meu ", "minha ", "ligaram", "dizendo",
              "pediram", "chegou", "do banco", "cobraram", "compartilhei", "voces", "fatura", "tem uma", "apareceu",
              "quais", "transacoes", "movimentos", "minhas", "ajuda", "extrato", "valeu"]
SECRET = ["codigo", "clave", "contrasena", "nip", " pin", "token", "senha", "cvv", "otp",
          " code", "password", "passcode", "security code"]
# Words that say the contact asked for the secret. "share" is left out on purpose: "I didn't share any code" is
# not a request.
ASKED = ["pid", "pedi", "solicit", "dame", "dar ", "piden", "pediram", "pediu",
         "asked", "requested", "wanted my", "wanted the", "give them", "give me", "send them", "send the", "told me to"]
CONTACT = ["me llamaron", "llamada", "llamo", "mensaje", "sms", "whatsapp", "correo", "email", "e-mail",
           "me escribieron", "ligacao", "ligaram", "mensagem", "notificacion", "notificacao", "alerta",
           "called me", "a call", "phone call", "text message", "message", "notification", "they called", "got a call"]
# Words that place the contact as coming "from the bank".
FROM_BANK = ["banco", "bank", "del banco", "do banco", "supuestamente", "decia ser", "dizia ser", "claiming to be",
             "said they were", "pretending to be"]
CHANNEL_WORDS = {"whatsapp": "whatsapp", "sms": "sms", "mensaje de texto": "sms", "correo": "email", "email": "email",
                 "e-mail": "email", "llam": "call", "ligac": "call", "ligaram": "call", "push": "push", "notificac": "push",
                 "text message": "sms", "called": "call", "phone call": "call", "a call": "call", "notification": "push"}
MINE = ["fui yo", "si fui", "lo reconozco", "ya lo reconozco", "si es mio", "es mio", "fui eu", "sim, fui", "reconheco",
        "e meu", "era mio", "ya recorde", "ya me acorde", "lembrei",
        "it was me", "i made it", "i made that", "i recognize it", "i remember it", "that's mine", "thats mine",
        "it's mine", "its mine", "i did it", "yes i did"]
CLAIM = ["no fui yo", "no lo reconozco", "no reconozco", "reclamar", "reclamo", "fraude", "robo", "robaron",
         "nao fui eu", "nao reconheco", "contestar", "roubaram", "golpe", "clonaron", "clonada", "no lo hice",
         "no hice", "nao fiz", "no es mio", "nao e meu", "yo no fui", "eu nao",
         "wasn't me", "wasnt me", "was not me", "not me", "didn't make", "didnt make", "did not make",
         "don't recognize", "dont recognize", "do not recognize", "not mine", "wasn't mine", "fraud", "stolen",
         "dispute", "never made", "i didn't", "i did not"]
# At the confirmation step a bare yes/no answers the question.
CONFIRM_YES = re.compile(r"^\s*(si|sim|claro|correcto|exacto|yes|yeah|yep)\b")
CONFIRM_NO = re.compile(r"^\s*(no|nao|nop|negativo|nope)\b")
PROBLEM = ["algo anda mal", "algo errado", "problema", "raro", "estranh", "no entiendo", "nao entendo", "error", "erro ",
           "something wrong", "something's wrong", "is wrong", "wrong with", "not right", "weird", "strange",
           "don't understand", "overcharged"]
INJECTION = ["ignora las instrucciones", "ignore previous", "ignore all", "ignora todo", "system prompt",
             "actua como", "you are now", "olvida tus reglas", "ignore as instrucoes", "developer mode",
             "ignore your instructions", "ignore the instructions", "ignore your rules", "forget your rules", "act as"]
OUT_OF_SCOPE = ["prestamo", "credito nuevo", "invertir", "hipoteca", "abrir una cuenta", "emprestimo", "transferir dinero",
                "hacer una transferencia", "cambiar mi direccion", "saldo de mi cuenta",
                "loan", "balance", "transfer money", "make a transfer", "open an account", "change my address",
                "change my phone", "mortgage", "invest"]
GREETING = ["hola", "buenas", "buenos dias", "ola", "oi", "bom dia", "boa tarde", "boa noite", "hello", "hi", "hey",
            "good morning", "good afternoon", "good evening", "how are you", "como esta", "que tal", "tudo bem", "tudo bom"]
# specs/007: the customer's recent movements, thanks, and "what can you do?". Matched on normalized text.
# A list request names recent movements ("my last transactions"), or asks to see one's movements ("show my
# transactions"). A complaint that mentions them ("something in my transactions doesn't add up") stays a dispute.
RECENT = ["ultimos movimientos", "ultimos cargos", "ultimas compras", "ultimas transacciones", "ultimos gastos",
          "movimientos recientes", "historial de movimientos", "ultimos pagos",
          "ultimas transacoes", "ultimos movimentos", "ultimas movimentacoes", "ultimas cobrancas", "transacoes recentes",
          "last movements", "last transactions", "recent transactions", "last charges", "recent charges",
          "last purchases", "recent purchases", "recent movements", "last payments", "transaction history"]
OWN_MOVEMENTS = ["mis movimientos", "mis cargos", "mis compras", "mis transacciones", "meus movimentos", "minhas transacoes",
                 "minhas movimentacoes", "minhas compras", "my transactions", "my movements", "my charges", "my purchases"]
SHOW = ["muestrame", "mostrar", "quiero ver", "ver mis", "cuales son", "mostre", "mostra ", "quero ver", "ver minhas",
        "ver meus", "quais sao", "show", "see my", "list my", "what are my", "let me see"]
RECENT_COUNT_RE = re.compile(r"\b(?:ultim[oa]s|last|recent)\s+(\d{1,2})\b")
THANKS = ["gracias", "muchas gracias", "obrigad", "valeu", "thank", "thanks", "thx", "te agradezco", "agradeco"]
HELP = ["que puedes hacer", "que puede hacer", "en que me ayudas", "en que me puede ayudar", "ayuda", "como funciona",
        "o que voce faz", "o que voce pode fazer", "ajuda", "como funciona",
        "what can you do", "help", "how does this work", "how does it work"]
CHARGE_WORDS = ["cargo", "cobro", "compra", "cobranca", "debito", "movimiento", "transaccion", "movimentacao",
                "charge", "transaction", "payment", "debit", "purchase"]

# Language scoring (research R4). Portuguese keeps its existing marker rule, unchanged. English and Spanish are
# scored on words that are distinctive for each, after removing merchant names.
EN_WORDS = {"the", "i", "my", "is", "was", "wasn't", "don't", "didn't", "it", "it's", "this", "that", "what", "why",
            "charge", "from", "bank", "and", "you", "your", "please", "hello", "hi", "yes", "recognize", "called",
            "asked", "message", "card", "they", "have", "at", "on", "got", "received", "someone", "today", "yesterday",
            "wrong", "not", "did", "do", "does", "can", "want", "help", "account", "transaction", "payment",
            "purchase", "code", "shared", "share", "lost", "thanks", "thank", "last", "recent", "transactions", "show", "of", "for", "with", "me", "mine", "made", "phone", "text",
            "call", "there", "an", "a", "be", "real", "pending", "loan", "balance", "i'm", "can't", "won't"}
ES_WORDS = {"el", "la", "los", "las", "un", "una", "del", "mi", "mis", "con", "por", "para", "es", "esta", "este",
            "esa", "ese", "fui", "yo", "cargo", "cobro", "cobraron", "tarjeta", "reconozco", "hola", "llamaron",
            "llamada", "mensaje", "pidieron", "clave", "contrasena", "cuenta", "quiero", "tengo", "hice", "pague",
            "compre", "lo", "le", "se", "usted", "senor", "gracias", "ayer", "hoy", "dinero", "si", "y", "pero",
            "cuando", "donde", "porque", "mio", "mia", "hay", "algo", "raro", "duda", "movimiento", "comercio",
            "dia", "di", "comparti", "nada", "eso", "esto", "salio", "aparece", "cobrado", "prestamo", "saldo",
            "ayuda", "ultimos", "movimientos", "muestrame", "cuales", "puedes", "estas"}
GREETING_WORDS = {"hola", "hello", "hi", "hey", "ola", "oi"}
# One-word courtesy that still says the language (specs/007): "gracias", "thanks", "help".
COURTESY_WORDS = GREETING_WORDS | {"gracias", "thanks", "thank", "thx", "help", "ayuda"}


def detect_language(t: str) -> str | None:
    """The language of a normalised message, or None when it is not clear (research R4)."""
    words = re.findall(r"[a-z']+", t)
    if any(m in t for m in PT_MARKERS) and "usted" not in t:
        return "pt"
    en = sum(w in EN_WORDS for w in words)
    es = sum(w in ES_WORDS for w in words)
    if len(words) < 2 and not (words and words[0] in COURTESY_WORDS):
        return None
    if en > es:
        return "en"
    if es >= 1:
        return "es"  # a tie goes to Spanish, the language the app used before English existed
    return None

AMOUNT_RE = re.compile(r"(?<![\w/])(?:\$|usd|cop|ars|r\$)?\s*(\d{1,3}(?:[.,]\d{3})+(?:[.,]\d{1,2})?|\d+(?:[.,]\d{1,2})?)(?!\s*/)")
DATE_RE = re.compile(r"\b(\d{1,2})[/-](\d{1,2})(?:[/-](\d{2,4}))?\b")
MONTH_NAMES = {m: i + 1 for i, m in enumerate(["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto",
                                               "septiembre", "octubre", "noviembre", "diciembre"])}
MONTH_NAMES.update({m: i + 1 for i, m in enumerate(["janeiro", "fevereiro", "marco", "abril", "maio", "junho", "julho",
                                                    "agosto", "setembro", "outubro", "novembro", "dezembro"])})
MONTH_NAMES["setiembre"] = 9
EN_MONTHS = {m: i + 1 for i, m in enumerate(["january", "february", "march", "april", "may", "june", "july", "august",
                                            "september", "october", "november", "december"])}
_EN_MONTH = "|".join(sorted(EN_MONTHS, key=len, reverse=True))
# "June 12", "June 12th, 2026", "12 June", "12th of June 2026"
EN_DATE_RE = re.compile(r"\b(?:(" + _EN_MONTH + r")\s+(\d{1,2})(?:st|nd|rd|th)?|(\d{1,2})(?:st|nd|rd|th)?\s+(?:of\s+)?(" + _EN_MONTH
                        + r"))(?:,?\s+(\d{4}))?\b")
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


def _asks_for_recent(t: str) -> bool:
    """A request to see one's recent movements, not a complaint about them (specs/007)."""
    if any(k in t for k in PROBLEM) or any(k in t for k in CLAIM):
        return False
    t = RECENT_COUNT_RE.sub(lambda m: m.group(0)[:m.start(1) - m.start(0)].rstrip(), t)  # "last 8 transactions"
    return any(k in t for k in RECENT) or (any(k in t for k in SHOW) and any(k in t for k in OWN_MOVEMENTS))


def understand(text: str, merchants: list[str], today: datetime, expecting: str | None = None,
               session_customer_id: str | None = None) -> Understanding:
    t = f" {_norm(text)} "
    t_lang = t
    for m in sorted(merchants, key=len, reverse=True):  # a merchant called "The ..." or "La ..." says nothing
        t_lang = t_lang.replace(_norm(m), " ")
    u = Understanding(language=detect_language(t_lang))

    ids = {m.upper() for m in CUSTOMER_ID_RE.findall(text)}
    u.other_customer_reference = bool(ids - {(session_customer_id or "").upper()})
    u.injection_suspected = any(k in t for k in INJECTION)

    for m in merchants:
        if _norm(m) in t:
            u.merchant = m
            break
    named = NAMED_DATE_RE.search(_norm(text))
    en_named = EN_DATE_RE.search(_norm(text))
    text_wo_dates = EN_DATE_RE.sub(" ", NAMED_DATE_RE.sub(" ", _norm(text)))
    text_wo_dates = DATE_RE.sub(" ", text_wo_dates)
    if (cm := RECENT_COUNT_RE.search(text_wo_dates)):  # "my last 8 movements": a count, not an amount of 8
        u.count = int(cm.group(1))
        text_wo_dates = text_wo_dates[:cm.start(1)] + " " + text_wo_dates[cm.end(1):]
    for raw in AMOUNT_RE.findall(text_wo_dates.lower()):
        val = _parse_amount(raw)
        if val and val >= 1 and not (1900 <= val <= 2100 and "." not in raw and "," not in raw):
            u.amount = val
            break
    if "ayer" in t or "ontem" in t or "yesterday" in t:
        u.date = (today - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    elif " hoy " in t or " hoje " in t or " today " in t:
        u.date = today.replace(hour=0, minute=0, second=0, microsecond=0)
    elif named:
        d, mo, y = int(named.group(1)), MONTH_NAMES[named.group(2)], named.group(3)
        year = int(y) if y else (today.year if (mo, d) <= (today.month, today.day) else today.year - 1)
        try:
            u.date = datetime(year, mo, d)
        except ValueError:
            pass
    elif en_named:
        mo = EN_MONTHS[en_named.group(1) or en_named.group(4)]
        d, y = int(en_named.group(2) or en_named.group(3)), en_named.group(5)
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

    u.asked_for_secret = any(k in t for k in SECRET) and any(k in t for k in ASKED)
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
    elif any(k in t for k in CONTACT) and any(k in t for k in FROM_BANK):
        u.intent = "check_contact"
    elif _asks_for_recent(t) and not (u.amount or u.merchant or u.date):
        u.intent = "list_recent"  # details win: "my last movements at Uber" is a search
    elif any(k in t for k in CLAIM):  # before MINE: "no fui yo" contains "fui yo"
        u.intent = "file_claim" if expecting == "confirm" else "dispute_charge"
    elif any(k in t for k in MINE):
        u.intent = "confirm_mine"
    elif any(k in t for k in OUT_OF_SCOPE):
        u.intent = "out_of_scope"
    elif u.amount or u.merchant or any(k in t for k in CHARGE_WORDS) or any(k in t for k in CLAIM) or any(k in t for k in PROBLEM):
        u.intent = "dispute_charge"
    elif any(k in t for k in HELP):
        u.intent = "help"
    elif any(k in t for k in THANKS):
        u.intent = "thanks"
    elif any(re.sub(r"^[^a-z]+", "", t.strip()).startswith(g) for g in GREETING):  # "¿cómo está?"
        u.intent = "greeting"
    else:
        u.intent = "out_of_scope"
    return u
