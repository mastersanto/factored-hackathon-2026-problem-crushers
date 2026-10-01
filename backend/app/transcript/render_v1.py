"""FROZEN: the r1 renderer, schema 1 (specs/002), kept byte for byte so PDFs issued before specs/004 keep verifying.

Never edit this file or its labels: verification re-renders an r1 PDF with it and compares every byte. The
live renderer is render.py (r2). What follows is the original r1 docstring.

Deterministic PDF of a signed transcript (specs/002 research §3).

The same signed transcript always renders to the same bytes: the creation date is the transcript's
`generated_at`, the producer is fixed, and fpdf2 is pinned. Verification relies on this: it re-renders
the embedded transcript and compares the whole file (research §5). Change RENDERER in record.py
whenever this layout changes.
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path

from fpdf import FPDF

from app.transcript.fingerprint import embedded_json

LABELS_V1: dict[str, dict] = {
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
    return LABELS_V1.get(lang, LABELS_V1["es"])


FONT_DIR = Path(__file__).parent / "fonts"
PRODUCER = "Explica este cargo - transcript"
GREY, INK, TINT = (90, 96, 105), (20, 24, 28), (234, 244, 246)


def _hhmm(at: str) -> str:
    return at[11:16]


def _stamp(at: str) -> str:
    d = datetime.fromisoformat(at)
    z = f"{d:%z}"  # e.g. -0500
    return f"{d:%d/%m/%Y %H:%M} (UTC{z[:3]}:{z[3:]})"


class _Doc(FPDF):
    def __init__(self, t: dict):
        super().__init__(format="A4")
        self.t, self.L = t, labels(t["lang"])
        self.add_font("DV", fname=str(FONT_DIR / "DejaVuSans.ttf"))
        self.add_font("DV", style="B", fname=str(FONT_DIR / "DejaVuSans-Bold.ttf"))
        self.set_margins(16, 14, 16)
        self.set_auto_page_break(True, margin=18)
        self.set_creation_date(datetime.fromisoformat(t["generated_at"]))
        self.set_producer(PRODUCER)
        self.set_title(self.L["title"])

    def header(self) -> None:
        L, t = self.L, self.t
        self.set_text_color(*INK)
        self.set_font("DV", "B", 11)
        self.cell(0, 6, L["service"], new_x="LMARGIN", new_y="NEXT")
        self.set_font("DV", "", 8.5)
        self.set_text_color(*GREY)
        self.cell(0, 4.5, f'{L["customer"]}: {t["customer"]["first_name"]}  ·  {L["country"]}: {t["customer"]["country"]}'
                           f'  ·  {L["conversation"]}: {t["conversation_ref"]}', new_x="LMARGIN", new_y="NEXT")
        cases = ", ".join(t["case_ids"]) or "—"
        self.multi_cell(0, 4.5, f'{L["cases"]}: {cases}  ·  {L["generated"]}: {_stamp(t["generated_at"])}, {t["time_zone"]}',
                        new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(200, 205, 210)
        self.line(self.l_margin, self.get_y() + 1.5, self.w - self.r_margin, self.get_y() + 1.5)
        self.ln(5)
        self.set_text_color(*INK)

    def footer(self) -> None:
        L = self.L
        self.set_y(-12)
        self.set_font("DV", "", 8)
        self.set_text_color(*GREY)
        self.cell(self.epw / 2, 5, f'{L["check_code"]}: {self.t["check_code"]}')
        self.cell(self.epw / 2, 5, L["page"].format(page=self.page_no(), pages="{nb}"), align="R")

    # ---- body -----------------------------------------------------------------------------------
    def para(self, text: str, *, size: float = 10, bold: bool = False, indent: float = 0, fill: bool = False,
             color=INK, h: float = 5) -> None:
        self.set_font("DV", "B" if bold else "", size)
        self.set_text_color(*color)
        self.set_x(self.l_margin + indent)
        self.multi_cell(self.epw - indent, h, text, fill=fill, align="L", new_x="LMARGIN", new_y="NEXT")

    def author_line(self, who: str, at: str) -> None:
        self.ln(2)
        self.para(f"{who}  ·  {_hhmm(at)}", size=8.5, bold=True, color=GREY, h=4.5)

    def body(self) -> None:
        L, t = self.L, self.t
        self.para(L["title"], size=13, bold=True, h=7)
        self.ln(1)
        self.set_fill_color(*TINT)
        self.para(L["notice"], size=9.5, fill=True)
        self.para(L["keep_original"], size=8.5, color=GREY, h=4.5)
        if t["masked"]:
            self.para(L["masked"], size=8.5, color=GREY, h=4.5)
        self.ln(2)
        previous = None
        for e in t["entries"]:
            kind = e["kind"]
            if kind == "customer":
                self.author_line(L["customer_author"], e["at"])
                self.set_fill_color(*TINT)
                self.para(e["text"], fill=True)
            else:
                if previous in (None, "customer"):
                    self.author_line(L["assistant_author"], e["at"])
                if kind == "message":
                    self.para(e["text"])
                    for st in e["statements"]:
                        source = f'  —  {st["source"]}' if st.get("source") else ""
                        self.para(f'[{L["basis"][st["basis"]]}] {st["text"]}{source}', size=8.5, indent=5, color=GREY, h=4.5)
                elif kind == "candidates":
                    for c in e["items"]:
                        pending = f' ({L["pending"]})' if c.get("status") == "Pending" else ""
                        self.para(f'{c["option"]}. {c["amount"]} · {c["merchant"]} · {c["when"]}{pending}', indent=5)
                elif kind == "verdict":
                    self.para(L["verdict"].get(e["verdict"], e["verdict"]), bold=True)
                elif kind == "handoff":
                    self.para(L["handoff"].format(case=e["case_id"]), bold=True)
                elif kind == "notice":
                    self.para(e["text"], color=GREY)
            previous = kind


def render(signed: dict) -> bytes:
    """The PDF for a signed transcript (one that carries its check code)."""
    doc = _Doc(signed)
    doc.add_page()
    doc.body()
    doc.embed_file(bytes=embedded_json(signed), basename="transcript.json", mime_type="application/json",
                   modification_date=datetime.fromisoformat(signed["generated_at"]))
    return bytes(doc.output())


def file_name(signed: dict) -> str:
    d = datetime.fromisoformat(signed["generated_at"])
    return f'{labels(signed["lang"])["file_prefix"]}-{signed["conversation_ref"]}-{d:%Y%m%d-%H%M}.pdf'
