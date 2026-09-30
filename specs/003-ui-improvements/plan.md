# Implementation Plan: UI improvements (language, source labels, phone width, accessibility)

**Branch**: `003-ui-improvements` | **Date**: 2026-09-30 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/003-ui-improvements/spec.md`, plus the owner-approved design prototype "Bóveda" as the visual reference ([design/](design/), online original <https://claude.ai/design/p/915d5cd3-b099-4104-9869-b5e788bc6cb8>).

## Summary

- **What changes**: the customer chat, sign-in, and specialist view are rebuilt in React to match the approved prototype.
  - The chat's fixed texts follow the conversation's language through a typed two-language dictionary.
  - Source labels show their kind in words, with a visible reference and an explainer.
  - The page works from 360 px up, with a sticky composer and a steps drawer.
  - It meets WCAG 2.1 AA: live announcements, real labels, `lang` marks, visible focus, and checked contrast.
- **Frontend only**:
  - No API, workflow, or PDF change (FR-218). Every element of the prototype that would need one is listed as left out, with the reason ([research R10](research.md#r10-what-the-prototype-has-that-this-feature-doesnt-build)).
  - Acceptance is by Playwright screenshots at 1200 and 375 px in both themes, plus automated axe, sideways-scroll, and language checks. The existing 46 backend tests keep the safety guarantees in place.

## Technical Context

- **Language/Version**: TypeScript ~6.0, React 19, Node 20+ (22 on the owner's machine).
- **Primary Dependencies**:
  - Existing: Vite 8, @tanstack/react-query 5.
  - New runtime dependencies: `@fontsource/ibm-plex-sans`, `@fontsource/jetbrains-mono` (self-hosted fonts, [R8](research.md#r8-fonts-and-icons)).
  - New dev dependencies: `@playwright/test`, `@axe-core/playwright` ([R9](research.md#r9-acceptance-checks-screenshots-and-automated-accessibility)).
- **Storage**: none. Everything is derived in the browser from the existing API events ([data-model.md](data-model.md)).
- **Testing**:
  - Backend: `make test` (pytest, 46 tests), unchanged.
  - Frontend: `tsc -b`, `npm run build`, and the new `npm run check:ui` (Playwright with axe) against `make dev` in rules mode.
- **Target Platform**:
  - Current Chrome, Safari, Firefox, and Edge, on desktop and on phones (iOS Safari, Android Chrome).
  - Served by Vite in development and by FastAPI in the container.
- **Project Type**: web application (`backend/` FastAPI, `frontend/` React). Only `frontend/` changes.
- **Performance Goals**: first screen interactive in under 2 s on a phone over 4G; fonts limited to 3 weights and the Latin subset; icons inline, with no icon font.
- **Constraints**:
  - Frontend-only (FR-218).
  - The customer's device receives only a case number (FR-219, Constitution III).
  - No third-party requests at run time.
  - Tap targets at least 44 px; no sideways scroll from 360 px.
- **Scale/Scope**: 3 screens (sign-in, chat, specialist) and about 60 fixed strings × 2 languages. Built before the 2026-10-05 deadline.

## Constitution Check

*GATE: checked before Phase 0 research, and again after Phase 1 design.*

| Principle | How this plan complies | Result |
|---|---|---|
| **I. Deterministic core, AI at the edges** | No workflow code changes. Verdict titles and case cards map deterministic codes (`verdict`, `handoff.case_id`) to fixed texts. The model is not involved. | Pass |
| **II. Permissions in the tool layer** | No new data reads or endpoints. The customer bar uses only the session's own customer fields, already returned. | Pass |
| **III. Verified facts only** | Every statement keeps its label and source, including questions and refusals, which the prototype had shown without one ([R2](research.md#r2-statements-and-their-source-labels)). The customer reads the server's text exactly. The case card shows only the case number and no deadline copied out of text ([R4](research.md#r4-case-card-after-a-handoff)). It also doesn't claim a review has started. No promise wording is added. | Pass |
| **IV. No data or secrets in the repository** | The design files hold invented examples only. The export zip and `uploads/` are git-ignored. Screenshots are git-ignored: they show synthetic organizer rows, and the repository is public. The secret scan runs before every commit. | Pass |
| **V. Evaluate before claiming** | No metric changes. `docs/evaluation.md` must stay unchanged (SC-206). The UI success criteria are measured by the checks in [quickstart.md](quickstart.md), and the manual ones (SC-202, the screen-reader part of SC-204) are recorded there. | Pass |
| **Quality gates** | `make test`, the frontend type-check and build, and the secret scan, plus `npm run check:ui` for this feature. `make eval` isn't required, since workflow and understanding don't change. | Pass |

**Post-design re-check**: Phase 1 artifacts ([data-model.md](data-model.md), [contracts/ui.md](contracts/ui.md)) add no API fields, no stored data, and no customer-facing internal data. **Pass.**

## Project Structure

### Documentation (this feature)

```text
specs/003-ui-improvements/
├── spec.md              # what must improve (no visuals)
├── plan.md              # this file
├── research.md          # decisions R1-R12, incl. what the prototype has that is not built
├── data-model.md        # browser-side derived entities (no stored data)
├── contracts/ui.md      # roles, names, texts, layout rules the checks rely on
├── quickstart.md        # automated and manual validation
├── checklists/requirements.md
├── design/              # approved prototype (visual reference), exported from Claude Design
│   ├── Explica este cargo.dc.html   # canvas: all screens, desktop/phone, light/dark
│   ├── Screen Login|Chat|Specialist.dc.html, App Header.dc.html, Components.dc.html, PDF Copy.dc.html
│   ├── handoff/tokens.css           # colour, type, radius, tap tokens (source for index.css)
│   └── support.js                   # prototype viewer runtime
└── tasks.md             # /speckit-tasks (not created here)
```

### Source Code (repository root)

```text
frontend/
├── src/
│   ├── App.tsx          # header, view switch, sign-in (rebuilt), footer, sets <html lang>
│   ├── Chat.tsx         # customer bar, steps panel/drawer, message log, composer (rebuilt)
│   ├── AgentQueue.tsx   # specialist view (restyled; Spanish labels for case types)
│   ├── useChat.ts       # + per-turn lang and time; step progress
│   ├── api.ts           # unchanged types; PDF_TEXT moves to i18n.ts
│   ├── i18n.ts          # NEW: Record<Lang, TextSet> (R1)
│   ├── icons.tsx        # NEW: inline Material Symbols SVGs, aria-hidden (R8)
│   ├── components/      # NEW: SourceLabel, Statements, VerdictCard, CaseCard, StepsPanel, CandidateList
│   ├── main.tsx         # + @fontsource imports
│   └── index.css        # tokens from design/handoff/tokens.css; layout; focus; reduced motion
├── e2e/
│   ├── ui.spec.ts       # NEW: screenshots, axe, sideways scroll, language, keyboard, tap size (R9)
│   └── screenshots/     # NEW, git-ignored output
├── playwright.config.ts # NEW: 1200×900 and 375×812, light/dark projects, baseURL :5173
└── package.json         # + fonts, + playwright/axe, + "check:ui" script

backend/                 # unchanged
```

**Structure decision**: this is the existing web-application layout. Only `frontend/` changes. Small presentational components go in `frontend/src/components/`, since `Chat.tsx` would otherwise pass 400 lines. The existing flat files stay where they are.

## Complexity Tracking

No constitution violations to justify.

| Addition | Why needed | Simpler alternative rejected because |
|---|---|---|
| Playwright + axe (dev only) | The owner's acceptance check is screenshots at two widths; SC-203 and SC-205 need automated measurement | Manual screenshots aren't repeatable and can't gate a change |
| `@fontsource` fonts | The prototype's type; no third-party requests from a bank page | Google Fonts links make third-party requests at run time |
