# Quickstart: checking the three languages

Run from the repository root on the owner's machine (the warehouse is built, `make setup` is done). Everything below runs in rules mode, for free, unless it says otherwise.

## 1. Gates

```bash
make test                          # backend: existing tests plus the new language tests, all passing
cd frontend && npm run build       # type-check: a text missing in any of en/es/pt fails here
make eval                          # three case sets, now with English and language_switch; regenerates docs/evaluation.md
```

**Expected**:
- **Spanish and Portuguese**: their rows in `docs/evaluation.md` (correct outcome, unsafe outcomes) are unchanged from before this feature.
- **English**: 0 unsafe outcomes, and correct outcomes within 5 points of Spanish (SC-403).
- **`language_switch`**: every case reaches its expected outcome with the same sources (SC-405).
- **Parity**: 100% identical tools, transactions, decisions, and handoffs across languages (SC-404).

## 2. UI checks

```bash
SESSIONS_PER_IP_HOUR=1000 LLM_DISABLED=1 make dev     # in its own terminal
cd frontend && npm run check:ui
```

**Expected**: every existing check still passes (the projects run in `es-MX`), and the new detection, switcher, and re-show checks pass ([contracts/ui.md](contracts/ui.md#checks)).

## 3. By hand: the demo path (Spanish, then Portuguese)

1. Open http://localhost:5173 with the browser set to English. Sign-in is in English, and the scenario labels are in English.
2. Sign in as the "Mexico, debit card, last 48 hours" customer. The opening line, in English, says you can write in English, Spanish, or Portuguese.
3. Tap the Spanish example message. The reply is in Spanish, and the whole app switches to Spanish, header included.
4. Answer "No fui yo", then give a statement. A case number appears.
5. Pick **PT** in the header:
   - every earlier message is now in Portuguese, with the same amounts, sources, and case number;
   - your own messages show a "Traduzido" mark. In rules mode they show the original with a note instead.
6. Download the PDF. It is in Portuguese, and your messages appear in the original Spanish with the translation beneath them (with a model). Check it in the specialist view: **Match**.
7. Open the specialist view. The case shows your Spanish statement, with a translation into the specialist's language.

## 4. Old PDFs still verify

```bash
cd backend && .venv/bin/python -m pytest -q tests/test_transcript.py -k "v1 or old"
```

**Expected**: a PDF rendered by the r1 renderer (a fixture produced before the change) verifies as a match.

## 5. With the model (costs money: ask the owner first)

```bash
make eval-llm     # about $3 with the larger sets
```

**Expected**: the same criteria as step 1, in Claude mode. The report states which numbers are Claude mode.
