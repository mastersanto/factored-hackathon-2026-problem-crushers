# UI Contract: customer chat, sign-in, and specialist view

**Feature**: [spec.md](../spec.md) · **Visual reference**: [design/](../design/) ([research](../research.md#visual-reference))

This contract is what the automated checks (`frontend/e2e/ui.spec.ts`) and the manual checks in [quickstart.md](../quickstart.md) rely on. Each item names:

- the roles and accessible names a test can query;
- the texts that must follow the conversation's language;
- the layout rules at 375 px.

**The HTTP API does not change.** It stays as defined in [`specs/001/.../http-api.md`](../../001-dispute-intake-assistant/contracts/http-api.md) and [`specs/002/.../http-api.md`](../../002-chat-transcript-pdf/contracts/).

## Everywhere

| Rule | Check |
|---|---|
| No sideways page scroll at 375 px and above | `document.documentElement.scrollWidth <= clientWidth` on every screen |
| Visible focus on every focusable element | 2 px `--focus-ring` outline with a 2 px offset |
| Tap targets at least 44 × 44 px | bounding box of every `button`, `a`, `input`, and `[role=button]` at 375 px |
| WCAG 2.1 AA | axe (`wcag2a`, `wcag2aa`, `wcag21aa`) reports 0 violations, light and dark |
| Footer | "Demostración con datos sintéticos · Factored AI & Data Hackathon 2026", which labels the input data |

## Header (all views)

- **Brand**: "Explica este cargo" · "LATAM Bank".
- **View switch**: `nav` named "Vista", with buttons "Cliente" and "Especialista". The active one has `aria-current="page"`. On phones it sits on a second row.
- **Status**: "Datos al {fecha} · Claude activo" or "… · Modo reglas (sin IA)", from `/api/health`.
- **Security strip** (customer view only): "Conversación segura · Nunca le pediremos contraseñas, PIN ni códigos SMS". It follows the conversation's language.

## Sign-in (Spanish; FR-203)

- **Heading**: `h1` "Revisemos juntos su cargo", plus the synthetic-customer notice.
- **Customer list**: `list` named "Clientes de prueba". Each item is one `button` showing initial, first name, country, label, and "Empezar".
- **Loading**: `role="status"` "Cargando clientes de prueba…", with placeholder cards hidden from screen readers.
- **Error**: `role="alert"` "No pudimos conectar…", with a "Reintentar" button that fetches again.

## Customer chat (follows the conversation's language; FR-201)

| Element | Role and name | Notes |
|---|---|---|
| Customer bar | `region` named by `aria.customer` | first name, country, label; "Cambiar cliente" link-button; PDF download button |
| PDF button | `button` `pdf.button` | disabled with a visible reason `pdf.notYet` before the first completed turn; outcome in `role="status"` |
| Steps panel | `complementary` named `steps.title` (desktop) / `button` with `aria-expanded` (phone) | five steps; current step has `aria-current="step"`; "Detalle técnico" disclosure holds the raw trace |
| Opening | intro text `intro(firstName)` | not a message: no time and no "Asistente" line, and it is not in the PDF |
| Message list | `log` named `aria.messages`, `aria-live="polite"` | each message has `lang`; assistant messages end with "HH:MM · Asistente" |
| Statement label | text `basis.*` (VERIFICADO / ESTIMACIÓN / POLÍTICA or the PT equivalents) + reference in monospace | never colour alone; the reference is visible text, not a tooltip |
| Sources explainer | `button` `sources.toggle` with `aria-expanded` → `dl` of the three meanings | one per assistant message that has statements |
| Charge options | one `button` `candidate.pick` per option, with amount, merchant, date, and `status.pending` when pending | sends the option number, as today |
| Verdict card | `role="status"`, title `verdict.*`, statements under it | tone good / warn / bad, plus an icon and a title word |
| Case card | `article` named "Caso {id}" | `case.sent`, `case.keep`, three status steps with no dates, `case.pdfHint` |
| Quick replies | `group` named `aria.replies` | texts from the server, already in the conversation's language |
| Examples | `group` named `aria.examples` | shown before the first reply, as today |
| Composer | `form`; `textbox` with a visually hidden `label` `composer.label`; `button` `composer.send` | sticky at the bottom; disabled while busy; focus stays in the text box after sending |
| Typing | static dots + `typing` text | no animation when the customer prefers reduced motion |
| Session ended | `role="alert"` card with `session.expiredTitle`, `session.expiredBody`, `button` `session.restart` | shown for `session_expired` and `turn_limit`; replaces the composer |

**Not shown to the customer**: case type, priority, security flags, risk estimate, or any handoff field other than the case number (FR-219).

## Specialist view (Spanish; FR-203)

- **Heading**: `h1` "Casos para revisar", plus the count and the ordering note.
- **PDF check**: `region` labelled by "Verificar PDF de conversación". A file `label` accepts a click or a dropped file. The result is in `role="status"`: Coincide / Alterado / Versión desconocida / No legible, each with an icon, a title word, and an explanation.
- **Case cards**: one `article` per case, sorted by priority.
  - The header shows priority as an icon and a word (Urgente / Alta / Normal), the case ID, the case type as a Spanish label, the time, and the language.
  - The fields are in a `dl`. The facts table sits in its own horizontally scrolling box.
- **Case-type labels**:
  - `unrecognized_charge` → Cargo no reconocido
  - `fraud_suspected` → Posible fraude
  - `fake_contact_secret_shared` → Posible estafa: compartió un código
  - `compliance_review` → Revisión de cumplimiento
  - `technical_fallback` → Falla técnica
  - An unknown code is shown as it is.
- **Empty**: "Sin casos todavía. Abra un reclamo desde el chat." with a button that switches to the customer view.
