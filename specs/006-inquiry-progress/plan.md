# Implementation Plan: Replies and progress that follow my inquiry

**Branch**: `006-inquiry-progress` | **Date**: 2026-10-01 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/006-inquiry-progress/spec.md`

## Summary

- **Progress (US1)**: the session gains an **inquiry** record (path, stage, done, outcome, case). The engine sets it at the points where it already changes the workflow stage or files a case ([data-model.md](data-model.md), transitions). It reaches the browser as `progress` on each `done` event and each conversation view.
  - The "How we review your case" panel shows the path's customer stages, which the owner chose as option A ([research.md](research.md) R2), and no longer the internal steps of the latest reply.
  - The internal trace stays under "Technical detail".
- **Replies (US2)**:
  - search replies with details name what was searched for and ask only for what's missing (R4);
  - pending questions (`choose`, `confirm`, `contact_shared`) are asked again after a greeting, an off-topic message, or an unclear answer, instead of the out-of-scope message or a silent "no" (R5).
  - Everything is done with templates and recipes, so rules mode, re-showing, and the PDF work unchanged.

## Technical Context

**Language/Version**: Python 3.10 (backend); TypeScript 6.0 with React 19 (frontend)

**Primary Dependencies**: FastAPI, DuckDB, Vite, TanStack Query. No new dependency.

**Storage**: none; the inquiry lives on the in-memory session, like the stage

**Testing**: pytest (`make test`, rules mode), `make eval` (rules mode), Playwright and axe (`npm run check:ui`)

**Target Platform**: Azure Container Apps (one container); current desktop and phone browsers

**Project Type**: web application

**Performance Goals**: no extra request; progress arrives with the reply it describes

**Constraints**:
- no change to understanding or the guards (FR-609);
- the PDF renderers are untouched (r1 frozen, r2 unchanged; the new recipe keys render through `render_text`);
- no rules-mode metric may drop.

**Scale/Scope**: one session field, 4 new templates × 3 languages, 2 `render_text` formatters, a re-ask branch for 3 stages, one panel rewrite, about 20 backend tests, one UI spec

## Constitution Check

*GATE: checked before Phase 0 research, and again after Phase 1 design (v1.1.0).*

| Principle | How this plan meets it | Result |
|---|---|---|
| I. Deterministic core, AI at the edges | Progress is set by code at fixed transitions. Echoes and re-asks are templates filled with the understanding's values, and work without any model. | Pass |
| II. Permissions in the tool layer | Unchanged. Refusals are unchanged and leave the progress alone. | Pass |
| III. Verified facts only | Echoed details are the values the search used. The merchant is already matched to a record name, and the amount is shown without an invented currency. Nothing masked is echoed. The compliance hold shows only "sent to a specialist". An unclear "did you share?" is asked again rather than read as "no", the safer reading, and gets a test that fails without it. | Pass |
| IV. No data or secrets in the repository | No data in tracked files. | Pass |
| V. Evaluate before claiming | `make eval` before commit (workflow change). No metric may drop. Any changed number is reported with `make eval-llm` only with the owner's approval. | Pass |
| Quality gates | `make test`, build, UI checks, `make eval`, secret scan. | Pass |

**Post-design re-check**: the design adds state and wording, and no new decision is moved to a model. Still passes.

## Project Structure

### Documentation (this feature)

```text
specs/006-inquiry-progress/
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
backend/app/workflow/engine.py      # Inquiry on Session; transitions; search echoes; reask_pending; contact follow-up order
backend/app/workflow/messages.py    # none_found_with, choose_with, too_many_with, need_answer (en/es/pt); searched/missing phrases
backend/app/language/translator.py  # render_text: searched and missing formatters; conversation_view: progress
backend/app/api/main.py             # (only if the view or done needs wiring beyond the engine)
backend/tests/test_progress.py      # transitions, no-move cases, re-asks, echoes, re-show parity, in en/es/pt
frontend/src/api.ts                 # Progress type; done.progress; ConversationView.progress
frontend/src/useChat.ts             # keep progress; remove stepProgress and STEP_ORDER
frontend/src/components/StepsPanel.tsx  # path lists, outcome line, summary
frontend/src/Chat.tsx               # pass progress
frontend/src/i18n.ts                # steps.charge/contact names and lines, outcomes, progress(n, total, name)
frontend/e2e/progress.spec.ts       # contracts/ui.md checks
```

**Structure Decision**: the existing web layout. Progress belongs to the workflow engine, which owns the stage and the cases. The panel only renders it.

## Complexity Tracking

No constitution violations. Not needed.
