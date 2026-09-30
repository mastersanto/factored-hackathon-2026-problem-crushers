"""Fixed texts of the transcript PDF, in Spanish and Portuguese (FR-105, FR-109). The notice is
customer-facing text: a test runs it through the same no-promise check as every other reply."""
from __future__ import annotations

LABELS: dict[str, dict] = {
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
    },
}


def labels(lang: str) -> dict:
    return LABELS.get(lang, LABELS["es"])
