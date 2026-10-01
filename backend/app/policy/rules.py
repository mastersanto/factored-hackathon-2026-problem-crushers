"""Country rules for dispute intake: deadlines and customer rights while a claim is open.

Sources are summarized in the ideation repository (explain-this-charge/research.md, sections
"Assessor research on the synthetic policies" and "External review: AI acting as a financial
specialist", 2026-09-30). These are desk research, not legal advice; the financial specialist's
validation is pending. Each rule carries an id so every statement to the customer can cite it.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass(frozen=True)
class Rule:
    id: str
    text: dict[str, str]  # by language: "es", "pt"


RULES: dict[str, list[Rule]] = {
    "México": [
        Rule("MX-LTOSF-23-deadline", {
            "es": "Tiene 90 días naturales desde la fecha de corte o de la operación para solicitar la aclaración; el banco debe responder en un máximo de 45 días.",
            "pt": "Você tem 90 dias corridos a partir da data de corte ou da operação para solicitar o esclarecimento; o banco deve responder em até 45 dias."}),
        Rule("MX-LTOSF-23-no-payment", {
            "es": "Mientras la aclaración está abierta, no está obligado a pagar el monto reclamado.",
            "pt": "Enquanto o esclarecimento estiver aberto, você não é obrigado a pagar o valor contestado."}),
    ],
    "Colombia": [
        Rule("CO-D587-reversal", {
            "es": "Para compras no solicitadas o fraudulentas puede pedir la reversión del pago dentro de los 5 días hábiles siguientes a conocer el hecho; el emisor tiene 15 días hábiles para reversar.",
            "pt": "Para compras não solicitadas ou fraudulentas, você pode pedir a reversão do pagamento em até 5 dias úteis após tomar conhecimento; o emissor tem 15 dias úteis para reverter."}),
        Rule("CO-complaint-15d", {
            "es": "El banco debe responder su reclamo en un plazo de 15 días hábiles.",
            "pt": "O banco deve responder sua reclamação em até 15 dias úteis."}),
    ],
    "Argentina": [
        Rule("AR-25065-26", {
            "es": "Puede impugnar el resumen dentro de los 30 días de recibido; el emisor debe acusar recibo en 7 días y corregir o justificar en 15 (60 si la operación fue en el exterior).",
            "pt": "Você pode contestar a fatura em até 30 dias após recebê-la; o emissor deve confirmar em 7 dias e corrigir ou justificar em 15 (60 se a operação foi no exterior)."}),
        Rule("AR-25065-no-block", {
            "es": "Mientras se resuelve, el emisor no puede bloquear su tarjeta ni exigirle el pago de los consumos cuestionados.",
            "pt": "Enquanto o caso é resolvido, o emissor não pode bloquear seu cartão nem exigir o pagamento das compras contestadas."}),
    ],
}

PROVISIONAL_CREDIT_MX = Rule("MX-BANXICO-provisional-credit", {
    "es": "Como es un cargo con tarjeta de débito hecho en las 48 horas previas a su reclamo, el banco debe abonarle el importe a más tardar el segundo día hábil.",
    "pt": "Como é uma cobrança no cartão de débito feita nas 48 horas anteriores à sua reclamação, o banco deve creditar o valor até o segundo dia útil."})

# Answer deadline, in calendar days, used to date the handoff (business days approximated x1.4).
ANSWER_DEADLINE_DAYS = {"México": 45, "Colombia": 21, "Argentina": 22}


def rights_for(country: str, tx: dict, claim_time: datetime) -> list[Rule]:
    rules = list(RULES.get(country, []))
    if (country == "México" and tx.get("product_type") == "Tarjeta Débito"
            and claim_time - tx["transaction_date"] <= timedelta(hours=48)):
        rules.append(PROVISIONAL_CREDIT_MX)
    return rules


def answer_deadline(country: str, claim_time: datetime) -> datetime:
    return claim_time + timedelta(days=ANSWER_DEADLINE_DAYS.get(country, 30))


def rule_text(rule_id: str, lang: str) -> str:
    """The text of a rule by its id, in `lang`: the wording a statement citing `rule:<id>` shows."""
    for rule in [r for rules in RULES.values() for r in rules] + [PROVISIONAL_CREDIT_MX]:
        if rule.id == rule_id:
            return rule.text[lang]
    raise KeyError(rule_id)
