# Implementation Plan: Suggestions in the language I'm writing in

**Branch**: `005-suggestions-language` | **Date**: 2026-10-01 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/005-suggestions-language/spec.md`

## Summary

- **Goal**: every suggestion follows the app's current language (specs/004), never a mix.
- **Example messages**: they move from a fixed mixed-language list in the browser to the demo API, which builds them in English, Spanish, and Portuguese from each customer's hint data, with amounts and dates in each language's format ([research.md](research.md) R1-R3). The browser shows the current language's list and swaps it instantly when the language changes.
- **Quick replies**: they already follow the language, including on a switch (R4). That gets a UI check.
- **Proof**: a backend test sends every example in every language through the real workflow and requires the same outcome as Spanish, with no language switch (R5).

## Technical Context

**Language/Version**: Python 3.10 (backend); TypeScript 6.0 with React 19 (frontend)

**Primary Dependencies**: FastAPI, DuckDB, Vite, TanStack Query. No new dependency.

**Storage**: none

**Testing**: pytest (`make test`, rules mode), Playwright and axe (`npm run check:ui`)

**Target Platform**: Azure Container Apps (one container); current desktop and phone browsers

**Project Type**: web application

**Performance Goals**: examples change in the same screen update as the language (no request)

**Constraints**: no change to understanding, the workflow, the guards, or evaluation results (FR-508). Spanish example wording unchanged apart from the amount format.

**Scale/Scope**: 5 example templates × 3 languages, one API field, one UI component change, one backend test, one UI spec

## Constitution Check

*GATE: checked before Phase 0 research, and again after Phase 1 design (v1.1.0).*

| Principle | How this plan meets it | Result |
|---|---|---|
| I. Deterministic core, AI at the edges | Examples are fixed templates filled from demo data. No model. | Pass |
| II. Permissions in the tool layer | Unchanged. The "another customer" example is still refused by the tool layer and the rules scan, in every language (tested). | Pass |
| III. Verified facts only | Unchanged. The examples are customer-side text, not assistant statements. | Pass |
| IV. No data or secrets in the repository | Examples are built at request time from the warehouse; no data in tracked files. | Pass |
| V. Evaluate before claiming | SC-502 is measured by a test over every demo customer and language. No evaluation numbers change. | Pass |
| Quality gates | `make test`, build, UI checks, secret scan. `make eval` is not needed (no workflow, understanding, or policy change). | Pass |

**Post-design re-check**: one additive API field and a frontend swap. Still passes.

## Project Structure

### Documentation (this feature)

```text
specs/005-suggestions-language/
├── spec.md
├── plan.md
├── research.md          # R1-R6
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
backend/app/api/main.py         # demo_customers: add examples {en, es, pt} (templates beside the scenario ids)
backend/tests/test_language.py  # every example understood like its Spanish counterpart; no language switch
frontend/src/api.ts             # DemoCustomer.examples
frontend/src/App.tsx            # remove suggestionsFor; pass the customer's examples
frontend/src/Chat.tsx           # show examples[lang]; lang attribute on every chip
frontend/e2e/suggestions.spec.ts  # contracts/ui.md checks
```

**Structure Decision**: the existing web layout. The example templates sit in `backend/app/api/main.py` next to the demo picker they belong to, since they are demo scaffolding, not workflow wording.

## Complexity Tracking

No constitution violations. Not needed.
