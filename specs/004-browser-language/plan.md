# Implementation Plan: The whole app in English, Spanish, or Portuguese

**Branch**: `004-browser-language` | **Date**: 2026-09-30 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/004-browser-language/spec.md`

## Summary

- **The goal**: one app language (English, Spanish, or Portuguese) drives every screen and the conversation.
  - It starts from the browser's preference, with English as the fallback.
  - It follows the language the customer writes in, and an ES/PT/EN switcher can change it.
  - Changing it re-shows the earlier conversation in the new language.
- **The approach** (owner's direction; [research.md](research.md) R1, R2): English is the base language.
  - **An interpreter** turns a message in any language straight into the existing language-neutral understanding (English names). The safety checks run in code on the original words.
  - **A translator** takes the target language as a parameter:
    - it rebuilds assistant messages deterministically from a recipe kept with each statement (template key and verified values);
    - it translates the customer's own words with Claude Haiku, marked as a translation, with the original kept as the record.
  - Both are modules with narrow interfaces inside the existing container, not separate services.
- **The PDF** gets a new renderer version, with the old one frozen, so PDFs already issued keep verifying.
- **Delivery**: three increments, each passing every gate (R14):
  1. the interface;
  2. the conversation, including the demo path (Spanish, then a switch to Portuguese);
  3. the PDF, the specialist's translations, and the evaluation.

## Technical Context

**Language/Version**: Python 3.10 (backend, container `python:3.10-slim`); TypeScript 6.0 with React 19 (frontend)

**Primary Dependencies**: FastAPI, Anthropic Python SDK (Haiku 4.5 to understand and to translate customer words, Sonnet 5.5 to phrase), DuckDB, fpdf2 2.8.9 and pypdf 6.19.0 (pinned), TanStack Query, Vite. No new dependency.

**Storage**: none new. Sessions, transcripts, and the translation cache stay in memory. The language choice is in the visitor's `localStorage`. The handoff queue and the fingerprint register are unchanged.

**Testing**: pytest (`make test`, rules mode), the evaluation (`make eval`, rules mode; `make eval-llm` with the owner's approval), Playwright and axe (`npm run check:ui`)

**Target Platform**: Azure Container Apps (one container, scale to zero); current desktop and phone browsers

**Project Type**: web application (FastAPI backend + React frontend)

**Performance Goals**: a language switch re-shows a 20-message conversation in under 2 s (SC-407). Re-rendering assistant messages makes no model call, and each customer translation is one Haiku call, cached.

**Constraints**: works with no model in all three languages (constitution I). Safety checks in code on the original words (constitution III, v1.1.0). PDFs already issued keep verifying. Spanish and Portuguese evaluation results must not get worse. Submissions close 2026-10-05.

**Scale/Scope**: about 35 template keys × 3 languages, 6 country-rule texts × 3, about 120 interface texts × 3, 7 demo scenario labels, eval sets of 270 cases (from 180) plus 6 switch cases and 6 parity cases per set

## Constitution Check

*GATE: checked before Phase 0 research, and again after Phase 1 design (v1.1.0).*

| Principle | How this plan meets it | Result |
|---|---|---|
| I. Deterministic core, AI at the edges | The engine, tools, rules, deadlines, and permissions don't change. The interpreter's model path only fills the existing `Understanding`. Assistant messages are re-rendered from recipes with no model. The model translates only customer words for display, marked as such. Rules mode works in all three languages (R2, R6, R7) | Pass |
| II. Permissions in the tool layer | No tool signature changes. The new endpoints read only the session's own stored entries, keyed by the session token. The specialist's translations are of cases already in the queue | Pass |
| III. Verified facts only | Re-rendered statements keep basis and source. Model rewording still passes the faithfulness check, now with English promises. The safety scans gain English and run on the original words, and the model cannot drop them (R3). English texts pass the no-promise and no-secrets checks | Pass |
| IV. No data or secrets in the repository | No data files. Customer translations send only the masked text. English eval cases are written to the git-ignored `backend/data/eval/`. English PDF names are added to `.gitignore` | Pass |
| V. Evaluate before claiming | English tuning and held-out phrasings, a switch category, and a parity check. Results broken down by language, rules mode free. Claude-mode numbers only after `make eval-llm` (R12) | Pass |
| Hackathon Constraints (v1.1.0) | English, Spanish, and Portuguese, with English as the base and every language in rules mode | Pass |
| Quality gates | `make test`, the build, the secret scan, and `make eval` (workflow and understanding change) for each increment | Pass |

**Post-design re-check**: the data model and contracts add no tool, no data read, and no model decision. `POST /api/session/language` re-renders stored entries only. Still passes.

## Project Structure

### Documentation (this feature)

```text
specs/004-browser-language/
├── spec.md
├── plan.md              # this file
├── research.md          # R1-R14
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── http-api.md
│   └── ui.md
├── checklists/requirements.md
└── tasks.md             # /speckit-tasks
```

### Source Code (repository root)

```text
backend/app/
├── language/                 # new
│   ├── __init__.py
│   ├── interpreter.py        # interpret(text, context) -> Understanding: rules scan + optional model, merged (R3, R4)
│   └── translator.py         # render(statements, lang); translate_customer(text, target) with checks and cache (R6, R7)
├── workflow/
│   ├── understanding.py      # English keywords, language scoring, English dates and amounts
│   ├── messages.py           # "en" for every key, format helpers per language, English quick replies
│   └── engine.py             # Statement key/params; s.lang set by a clear language at any stage; calls interpreter
├── policy/rules.py           # English rights texts, same rule ids
├── llm/claude.py             # language en|es|pt|unclear; English promises; translate() for customer words
├── api/main.py               # session lang; POST /api/session/language; GET /api/session/conversation; handoffs?lang; scenario ids; strip key/params
├── transcript/
│   ├── record.py             # entry lang, recipes, raw candidate values; snapshot schema 2 in a target language
│   ├── labels.py             # English labels (r2)
│   ├── render.py             # r2 layout: customer original plus marked translation
│   ├── render_v1.py          # new: frozen copy of the r1 renderer and labels
│   └── verify.py             # pick the renderer by schema/renderer
└── eval/cases.py, run.py, report.py   # English phrasings, language_switch, parity, report by language

backend/tests/
├── test_language.py          # new: detection, guard parity in 3 languages, render round-trip, re-show endpoint
├── test_transcript.py        # r1 fixture still verifies; r2 in each language
└── test_workflow.py, test_guards.py   # unchanged, still passing

frontend/src/
├── language.ts               # new: pickLanguage, storeLanguage, context
├── components/LanguageSwitcher.tsx   # new
├── i18n.ts                   # Record<'en'|'es'|'pt', TextSet>, extended to sign-in, header, specialist view
├── main.tsx                  # decide the language before the first render
├── App.tsx, AgentQueue.tsx   # texts from TextSet; switcher in the header
├── useChat.ts, Chat.tsx      # re-show on switch or on a changed done.lang; translated-message mark
└── api.ts                    # Lang adds 'en'; new calls

frontend/e2e/                 # locale es-MX on existing projects; detect, switcher, reshow specs (contracts/ui.md)
```

**Structure Decision**: the existing web-application layout (`backend/app`, `frontend/src`) is kept. The new `backend/app/language/` package holds the interpreter and translator boundaries the owner asked for, so either can move out into its own service later without touching the engine (R1).

## Complexity Tracking

No constitution violations to justify.

One deliberate deviation from the owner's wording is recorded in the spec's Clarifications (FR-411): understanding goes straight from each language to the common form, rather than through an English translation of the customer's text.

The choice of modules over separate services (R1) is a plan decision the owner can overturn. The interfaces are designed so that splitting them later changes no engine code.
