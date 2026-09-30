# Data Model: UI improvements

**Feature**: [spec.md](spec.md) · **Plan**: [plan.md](plan.md)

This feature adds no stored data and doesn't change the API: the backend, the warehouse, and the transcript record stay as they are. The entities below live only in the browser and are derived from what the API already sends ([`specs/001-dispute-intake-assistant/contracts/http-api.md`](../001-dispute-intake-assistant/contracts/http-api.md)).

## Lang

`'es' | 'pt'`. It already exists in `frontend/src/api.ts`.

- **Where it comes from**: the `lang` of the latest `done` event. It is `'es'` before the first reply (FR-202).
- **What it drives**: the text set shown, `document.documentElement.lang`, and each message's `lang` attribute.

## TextSet (`frontend/src/i18n.ts`)

A record of every fixed text in the customer's chat, one complete set per `Lang`.

| Group | Keys (examples) | Requirement |
|---|---|---|
| Source labels | `basis.known`, `basis.guessed`, `basis.rule`, `basis.explain.*`, `sources.title`, `sources.toggle` | FR-204, FR-206 |
| Verdicts | `verdict.bank_contact`, `verdict.no_record`, `verdict.scam_asks_secret` | FR-201 |
| Charges | `candidate.pick`, `candidate.picked`, `status.pending` | FR-201 |
| Case card | `case.sent`, `case.keep`, `case.pdfHint`, `case.steps.*` | FR-201 |
| Chat frame | `intro`, `composer.label`, `composer.placeholder`, `composer.send`, `typing`, `security.strip` | FR-201, FR-214 |
| PDF | `pdf.button`, `pdf.saved`, `pdf.expired`, `pdf.failed`, `pdf.notYet` (moved from `Chat.tsx`'s `PDF_TEXT`) | FR-201 |
| Steps panel | `steps.title`, `steps.subtitle`, `steps.names[5]`, `steps.lines[5]`, `steps.done`, `steps.now`, `steps.progress`, `steps.technical` | FR-201, FR-210 |
| Session | `session.expiredTitle`, `session.expiredBody`, `session.restart`, `session.change` | FR-201 |
| Spoken names | `aria.messages`, `aria.replies`, `aria.examples`, `aria.customer` | FR-214 |

**Validation**:

- The type is `Record<Lang, TextSet>`, so a key missing in either language fails the type-check (`tsc -b`).
- Strings with values (for example the case number or step progress) are functions, `(case: string) => string`, so nothing is concatenated in components.

## SourceLabel (derived per statement)

| Field | From | Rule |
|---|---|---|
| `basis` | `statement.basis` | `known` → verified, `guessed` → estimate, `rule` → rule |
| `word` | `TextSet.basis[basis]` | always shown, in words (FR-204) |
| `reference` | `statement.source` | shown exactly as sent; not shown when `null` (FR-207, US2 scenario 3) |
| `icon` | fixed per basis | `check_circle`, `calculate`, `policy` (decorative, `aria-hidden`) |

**Layout choice per message**: statement lines when `message.text` equals the statements' texts joined with spaces; otherwise a paragraph plus a source list ([research R2](research.md#r2-statements-and-their-source-labels)).

## Turn (extends `useChat`'s `Turn`)

| Field | New? | Meaning |
|---|---|---|
| `role`, `events`, `text` | existing | as today |
| `lang` | new | language of this turn, from its `done` event. The customer's message uses the next assistant turn's language, since it is detected in the same turn. |
| `at` | new | `Date.now()` when the turn started, shown as `HH:MM` in the customer's country's time zone ([R11](research.md#r11-times-on-messages)) |

## StepProgress (derived, steps panel)

- **Order**: `understand(0) → decide(1) → act(2) → verify(3) → escalate(4)`.
- **Current step**: the highest index among the latest assistant turn's `step` events. Before any turn there is none.

| State of step *i* | Condition |
|---|---|
| done | *i* < current |
| current | *i* = current (`aria-current="step"`) |
| to do | *i* > current, or there is no turn yet |

## CaseCard (derived from a `handoff` event)

| Field | From |
|---|---|
| `caseId` | `handoff.case_id`, the only field the customer's device receives (FR-219) |
| status steps | fixed texts only: received (done), specialist review (next), answer (to do). No dates ([R4](research.md#r4-case-card-after-a-handoff)). |

## ChatNotice (derived from an `error` event)

| `code` | Shown as |
|---|---|
| `session_expired` | expired-session card (`role="alert"`) with a button that returns to sign-in. The composer is hidden. |
| `turn_limit` | the same card, with the server's text |
| `network`, any other | error line with the server's text (already in the conversation's language) |
