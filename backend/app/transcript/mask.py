"""Masking for transcript PDFs (FR-107). Applied to the customer's words when they are recorded, so a
card number or code a customer typed never reaches the fingerprint, the embedded JSON, or the PDF.
The assistant never prints these, so its messages are not masked."""
from __future__ import annotations

import re

# 13 to 19 digits, optionally grouped by single spaces or dashes: a full card number.
_CARD = re.compile(r"(?<![\d.,])\d(?:[ -]?\d){12,18}(?![\d.,])")
# Words that name a secret, in Spanish and Portuguese.
_KW = r"(?:c[oó]digo|clave|contrase[nñ]a|pin|nip|otp|token|senha)"
_CODE = r"\d{4,8}"
# A code within four words after the keyword ("el código de verificação é 55123"), or before it ("482913 era el código").
_AFTER = re.compile(rf"(\b{_KW}\b(?:\W+[^\W\d]+){{0,4}}?\W+){_CODE}(?![\d.,])", re.IGNORECASE)
_BEFORE = re.compile(rf"(?<![\d.,]){_CODE}((?:\W+[^\W\d]+){{0,3}}?\W+{_KW}\b)", re.IGNORECASE)

DOTS = "••••"


def mask(text: str) -> tuple[str, bool]:
    """Return the text with card numbers reduced to their last four digits and codes replaced, and
    whether anything was masked."""
    out = _CARD.sub(lambda m: f"{DOTS} {re.sub(r'[ -]', '', m.group())[-4:]}", text)
    out = _AFTER.sub(lambda m: m.group(1) + DOTS, out)
    out = _BEFORE.sub(lambda m: DOTS + m.group(1), out)
    return out, out != text
