"""Fixed texts of the transcript PDF, in English, Spanish, and Portuguese (FR-105, FR-109; specs/004 FR-424). The notice is
customer-facing text: a test runs it through the same no-promise check as every other reply."""
from __future__ import annotations

LABELS: dict[str, dict] = {
    "en": {
        "title": "Copy of the conversation",
        "service": "Explain this charge · LATAM Bank",
        "customer": "Customer",
        "country": "Country",
        "conversation": "Conversation",
        "cases": "Case",
        "generated": "Generated",
        "customer_author": "You",
        "assistant_author": "Assistant",
        "basis": {
                "known": "verified",
                "guessed": "estimate",
                "rule": "rule"
        },
        "pending": "pending",
        "verdict": {
                "scam_asks_secret": "Scam: they asked for a code",
                "no_record": "No record from the bank",
                "bank_contact": "A real contact from the bank"
        },
        "handoff": "Case {case} sent to a specialist",
        "notice": "This is a copy of your conversation with the LATAM Bank assistant, for your records. This document does not decide the claim and does not promise any result, refund, or approval.",
        "keep_original": "Keep the original file: only the original can be verified with the check code.",
        "masked": "For your security, card numbers and codes you typed were hidden (••••).",
        "page": "Page {page} of {pages}",
        "check_code": "Check code",
        "file_prefix": "conversation",
        "translated": "Translation",
        "no_translation": "Shown as written: no translation was made."
    },
    "es": {
        "title": "Copia de la conversación",
        "service": "Explica este cargo · LATAM Bank",
        "customer": "Cliente", "country": "País", "conversation": "Conversación", "cases": "Caso",
        "generated": "Generado",
        "customer_author": "Usted", "assistant_author": "Asistente",
        "basis": {"known": "verificado", "guessed": "estimación", "rule": "política"},
        "pending": "pendiente",
        "verdict": {"scam_asks_secret": "Estafa: pidió un código", "no_record": "Sin registro del banco",
                    "bank_contact": "Contacto real del banco"},
        "handoff": "Caso {case} enviado a un especialista",
        "notice": ("Esta es una copia de su conversación con el asistente de LATAM Bank, para sus registros. "
                   "Este documento no decide el reclamo y no promete ningún resultado, reembolso ni aprobación."),
        "keep_original": "Conserve el archivo original: solo el original se puede verificar con el código de verificación.",
        "masked": "Por su seguridad, se ocultaron los números de tarjeta y los códigos que usted escribió (••••).",
        "page": "Página {page} de {pages}",
        "check_code": "Código de verificación",
        "file_prefix": "conversacion",
        "translated": "Traducción",
        "no_translation": "Tal como se escribió: no se hizo una traducción.",
    },
    "pt": {
        "title": "Cópia da conversa",
        "service": "Explica este cargo · LATAM Bank",
        "customer": "Cliente", "country": "País", "conversation": "Conversa", "cases": "Caso",
        "generated": "Gerado",
        "customer_author": "Você", "assistant_author": "Assistente",
        "basis": {"known": "verificado", "guessed": "estimativa", "rule": "política"},
        "pending": "pendente",
        "verdict": {"scam_asks_secret": "Golpe: pediu um código", "no_record": "Sem registro do banco",
                    "bank_contact": "Contato real do banco"},
        "handoff": "Caso {case} enviado a um especialista",
        "notice": ("Esta é uma cópia da sua conversa com o assistente do LATAM Bank, para os seus registros. "
                   "Este documento não decide a reclamação e não promete nenhum resultado, reembolso ou aprovação."),
        "keep_original": "Conserve o arquivo original: só o original pode ser verificado com o código de verificação.",
        "masked": "Para sua segurança, os números de cartão e os códigos que você digitou foram ocultados (••••).",
        "page": "Página {page} de {pages}",
        "check_code": "Código de verificação",
        "file_prefix": "conversa",
        "translated": "Tradução",
        "no_translation": "Como foi escrito: não foi feita uma tradução.",
    },
}


def labels(lang: str) -> dict:
    return LABELS.get(lang, LABELS["es"])
