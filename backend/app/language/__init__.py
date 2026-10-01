"""Languages of the app (constitution v1.1.0). English is the base language: the common form of what the
customer means uses English names, and English is the source wording that every other language translates.

- interpreter: any supported language -> the common, language-neutral understanding. The safety checks run in
  code on the customer's original words, never only on a translation.
- translator: verified statements -> wording in the language asked for; customer words -> a marked translation.
"""
from __future__ import annotations

from typing import Literal

LANGS: tuple[str, ...] = ("en", "es", "pt")
Lang = Literal["en", "es", "pt"]
BASE_LANG: Lang = "en"
