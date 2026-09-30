# Research: UI improvements

**Feature**: [spec.md](spec.md) · **Plan**: [plan.md](plan.md) · **Date**: 2026-09-30

## Visual reference

The owner approved a Claude Design prototype, "Bóveda". It is exported to [design/](design/): every screen at desktop (1200 px) and phone (390 px) width, in light and dark themes.

- **Where it lives**:
  - [`design/Explica este cargo.dc.html`](design/Explica%20este%20cargo.dc.html) is the canvas.
  - The screens are in [`Screen Login`](design/Screen%20Login.dc.html), [`Screen Chat`](design/Screen%20Chat.dc.html), [`Screen Specialist`](design/Screen%20Specialist.dc.html), [`App Header`](design/App%20Header.dc.html), and [`Components`](design/Components.dc.html).
  - The colour tokens are in [`design/handoff/tokens.css`](design/handoff/tokens.css).
  - The online original is <https://claude.ai/design/p/915d5cd3-b099-4104-9869-b5e788bc6cb8>, which is private to the owner's account.
- **What it shows**: invented example data, such as Ana Gómez, TX-990214, and C-1234. In the app, every value comes from the API.

Each decision below says what is built as drawn, what is adapted, and what is left out. Anything left out would need a change to the workflow or the API, and FR-218 rules that out for this feature.

---

## R1. Where the texts come from, and how they switch language

- **Decision**: a typed dictionary in `frontend/src/i18n.ts`, keyed by language (`es` or `pt`). A `useText(lang)` helper reads from it. The language is the one `useChat` already tracks from each `done` event's `lang`.
  - The dictionary covers the chat's fixed texts: source labels and their explanations, verdict titles, charge status, the case card, the opening line, the composer, the download action, the steps panel, the session notices, and spoken names.
  - `document.documentElement.lang` follows the conversation's language.
- **Rationale**:
  - There are about 60 strings in two languages. A library (react-i18next, FormatJS) would add dependencies, and plural or ICU rules aren't needed.
  - A `Record<Lang, Texts>` type makes TypeScript reject a missing Portuguese string at build time, which enforces FR-201 without extra tests.
- **Alternatives considered**:
  - react-i18next: too heavy for two locales and a fixed set of strings.
  - Asking the backend for the labels: that changes the API, which FR-218 rules out.
- **Note on the prototype**: the Portuguese example (3c) still has the Spanish title "Contacto real del banco". The dictionary uses "Contato real do banco". The prototype's Spanish wording is kept, and the Portuguese texts are written for this feature.

## R2. Statements and their source labels

The API sends each assistant message as `text` plus `statements[]`, each with `{text, basis, source}`.

- **How `text` relates to the statements**:
  - With template wording (rules mode, and every turn whose wording isn't checked by a model), `text` is exactly the statements' texts joined with spaces.
  - When Claude rewords a message and the rewording passes the faithfulness check, `text` is the rewording, and the statements keep the template texts.
- **Decision**:
  - When `text === statements.map(s => s.text).join(' ')`, show one line per statement, each with its label and reference, as the prototype draws it.
  - Otherwise, show `text` as a paragraph, followed by a "Fuentes" / "Fontes" list of label and reference pairs, without the statement texts.
  - Either way, the customer reads exactly the text the server streamed. The server's records, which the PDF is built from, stay as they are.
- **Label design**:
  - Each label shows an icon and a word: VERIFICADO / VERIFICADO, ESTIMACIÓN / ESTIMATIVA, POLÍTICA / POLÍTICA. Colour is never the only difference between kinds (FR-204).
  - The reference is shown next to the label as visible monospace text, exactly as sent (FR-207). This replaces the hover-only `title` tooltip (FR-205).
  - A "¿De dónde sale este dato?" / "De onde vem esta informação?" disclosure button explains the three labels (FR-206). It is a real button with `aria-expanded`, so it works by tap, click, and keyboard.
- **Adapted from the prototype**:
  - The prototype shows the closing question ("¿Reconoce este cargo?") and the refusal without a label. Constitution III requires every statement to carry a basis and a source, so they keep their POLÍTICA label.
  - References such as `flow` or `policy:scope` are shown as they are, not replaced with friendly names. They are internal, but they are what the audit trail and the PDF use.
- **Alternatives considered**:
  - Always showing the statements and hiding Claude's rewording: that changes what the chat says (FR-218), and the screen would no longer match the PDF.
  - Adding a `phrased_by` field to the message event: the exact-equality check needs no API change and gives the same answer.

## R3. Steps panel ("Cómo revisamos su caso")

- **Decision**: replace the JSON trace with the prototype's five plain-language steps:
  - Entender, Decidir, Actuar, Verificar, Escalar.
  - Portuguese: Entender, Decidir, Agir, Verificar, Encaminhar.
- **How the current step is set**:
  - It is the furthest workflow step reached in the latest turn, taken from the streamed `step` events (`understand` → `escalate`).
  - Earlier steps show as done, later ones as to do.
  - Before the first turn, every step shows as to do.
  - Internal steps never reach the browser, since the API already filters them.
- **Layout**: a 300 px column on the right at desktop width. Below 860 px it becomes a collapsible drawer above the chat, closed by default ("Paso 3 de 5 · Actuar"), which covers FR-210.
- **Kept for the demo**: the raw trace moves into a closed "Detalle técnico" / "Detalhe técnico" disclosure at the bottom of the panel. Judges can still see the intent, tool calls, and results, and customers aren't shown JSON.
  - This updates the spec's "flow panel keeps its content" assumption: the content stays, one tap away.
- **Alternatives considered**:
  - Keeping the JSON as the main content: the owner's prototype replaced it.
  - Removing the trace altogether: it's part of how the demo shows controlled automation.

## R4. Case card after a handoff

- **What the API allows**: the customer's device receives only `{case_id}` (Constitution III; `engine.py` `_handoff_event`). The deadline and the rights arrive as POLÍTICA statements in the message that follows.
- **Decision**:
  - Build the case card: an icon, "Caso X enviado a un especialista", "Guarde su número de caso", and the PDF hint.
  - The three-step status ("Recibido / Revisión por un especialista / Respuesta") shows no dates.
  - The response date is not copied into the card. The customer reads it in the labelled rule statement right below, exactly as the server sent it.
- **Adapted from the prototype**:
  - The prototype puts "a más tardar el 21 de julio de 2026" inside the card. Doing that means parsing the date out of a statement's text (fragile) or adding it to the handoff event (API change, and more data on the device). Neither is allowed.
  - The middle step says "Revisión por un especialista" rather than "En revisión · Ahora", so it doesn't claim someone is already working on the case.
- **The same card serves every handoff**: claims, suspected scams, technical fallbacks, and compliance holds. It shows no case type, so a compliance hold looks like any other case and the customer isn't tipped off.

## R5. Verdicts on "was it really my bank?"

- **Decision**: draw the prototype's verdict card:
  - an icon and a title from the dictionary, chosen by the deterministic `verdict` code;
  - under the title, the statements of the message that follows, with their labels.
  - Tones: `bank_contact` good, `no_record` warn, `scam_asks_secret` bad.
  - Each card has `role="status"`, and its title is a word, never a colour alone.
- **Rationale**: the title maps a code the rules produced (Constitution I). All the facts still come from the statements.

## R6. Layout, phone width, and the composer

- **Decision**: follow the prototype's single scrolling page.
  - Header, security strip, customer bar, steps (a drawer on phones), then the conversation card with quick replies and the composer, then the footer.
  - The composer sticks to the bottom of the screen (`position: sticky; bottom: 0`), and heights use `dvh`, so the text box stays above the on-screen keyboard (FR-209).
  - New messages scroll into view, without smooth animation when the customer prefers reduced motion (FR-217).
  - Every interactive element is at least 44 × 44 px (`--tap`), which covers FR-211.
  - Long values (merchants, references) use `overflow-wrap: anywhere`. The specialist's facts table sits in its own `overflow-x: auto` box (FR-208).
- **Alternatives considered**: the current fixed-height chat box, which is what fails at phone width with the keyboard open.

## R7. Accessibility

- **Screen readers**:
  - The message list is `role="log"` with `aria-live="polite"`, so each new message, verdict, case card, or notice is announced once as it's added (FR-213).
  - The PDF outcome is `role="status"`. The expired-session notice is `role="alert"`.
- **Names**:
  - The composer's input has a visually hidden `<label>` (FR-214).
  - Buttons that show only an icon get an `aria-label` from the dictionary.
  - The view switch is a `<nav>` with `aria-current="page"`.
  - Quick replies and examples are `role="group"` with a name.
- **Language**: each message element gets `lang` from its turn's language, since the customer's message is detected in the same turn. The page's `lang` follows the conversation (FR-215).
- **Focus**: every focusable element gets `:focus-visible` with a 2 px `--focus-ring` outline and a 2 px offset. The focus order follows the page. After sending, focus stays in the composer (FR-212).
- **Contrast**: the prototype's tokens are chosen for WCAG 2.1 AA, and they are verified automatically (R9) in both themes (FR-216).
- **Motion**: the typing indicator uses static dots, as the prototype's component sheet says. Scrolling respects `prefers-reduced-motion`.

## R8. Fonts and icons

- **Decision**:
  - IBM Plex Sans and JetBrains Mono are self-hosted through `@fontsource/ibm-plex-sans` and `@fontsource/jetbrains-mono`, weights 400, 500, and 600, Latin subset.
  - About 25 Material Symbols icons are copied as inline SVG into `frontend/src/icons.tsx` (Apache 2.0, with attribution in the file).
- **Rationale**:
  - The prototype loads Google Fonts and the Material Symbols variable font at run time. That means a third-party request from a bank page, several MB for the icon font, and a page that breaks without internet.
  - Self-hosting is private and works offline or in the container.
  - Inline SVG icons are tiny, and marking them `aria-hidden` is simple.
- **Alternatives considered**:
  - Google Fonts links: third-party requests.
  - The full Material Symbols font: size.
  - An icon library such as lucide-react: its icons don't match the prototype's.

## R9. Acceptance checks: screenshots and automated accessibility

- **Decision**: add `@playwright/test` and `@axe-core/playwright` as frontend devDependencies, with a `frontend/e2e/ui.spec.ts` suite that runs `npm run check:ui` against `make dev`.
  - It walks the claim path (Spanish), the call check (Portuguese), a scam, and a refusal.
  - It takes screenshots at 1200 × 900 and 375 × 812, in light and dark themes (`colorScheme` emulation), into `frontend/e2e/screenshots/`. That folder is git-ignored and written on each run.
  - It asserts that nothing scrolls sideways (`scrollWidth <= clientWidth`), which covers SC-203.
  - It asserts no Spanish fixed text in the Portuguese run, which covers SC-201. The check is dictionary-driven: no `es` string that differs from its `pt` string may appear.
  - It runs axe (`wcag2a`, `wcag2aa`, `wcag21aa`) on sign-in, chat, and specialist with 0 violations, which covers SC-205.
  - It completes the claim path with the keyboard alone, which covers the automated part of SC-204.
- **Rationale**:
  - The owner's plan names screenshots at both widths as the acceptance check.
  - Axe catches contrast and naming errors automatically.
  - Rules mode makes the runs free and deterministic.
- **Setup needed**: Playwright needs a Chromium binary (`npx playwright install chromium`). On WSL it may also need system libraries (`sudo npx playwright install-deps chromium`), which the owner installs once.
- **Still manual**: the screen-reader run (SC-204) and the three-person label test (SC-202), recorded in `quickstart.md`.
- **Alternatives considered**: manual screenshots only, which aren't repeatable and can't gate a change.

## R10. What the prototype has that this feature doesn't build

Each item below needs a workflow or API change (FR-218). They are listed as candidates for a later feature.

| Element in the prototype | Why it's left out |
|---|---|
| "Hablar con una persona" link in the composer | There's no "ask for a person" intent. Sent as a message, it would get the out-of-scope answer, so the link would promise something the workflow doesn't do. |
| "Ninguno de estos cargos coincide" under the charge list | There's no "none of these" intent. Today it would re-ask the choice. |
| "Tomar caso" button on specialist cards | There's no case assignment in the API. |
| Full name, card last four digits, and currency on sign-in and in the customer bar | The demo-customer endpoint returns first name, country, label, and hints. Adding fields means an API change, and more data. The prototype's layout is kept, with those fields. |
| Deadline date inside the case card | See R4. |
| New PDF layout ("PDF Copy") | specs/002 verifies a PDF by rendering it again byte for byte, so a new layout means a new renderer version and verification changes. Out of scope (spec, Out of Scope). |

## R11. Times on messages

- **Decision**: show `HH:MM` under each message, taken from the moment the browser receives it and formatted in the customer's country's time zone. That's the same mapping the PDF uses (`backend/app/transcript/record.py` `TIME_ZONES`): Mexico → America/Mexico_City, Colombia → America/Bogota, Argentina → America/Argentina/Buenos_Aires.
- **Trade-off**: the server stamps the PDF's times when it records each event. The browser's time can differ by a network round trip, so rarely by a minute at a minute boundary. The PDF is the record, and screen times are for orientation. This is noted in the quickstart.
- **Alternatives considered**:
  - Adding server timestamps to events: an API change.
  - Showing no times: the prototype has them, and they help the customer relate the chat to the PDF.

## R12. Design files in the repository

- **Decision**: commit the extracted design folder as the visual reference. That covers the `.dc.html` screens, `support.js` (the prototype's viewer runtime, needed to open the files locally), `handoff/tokens.css`, and `github.md`.
  - The export's `.zip`, the `.thumbnail`, and `uploads/` are git-ignored. `uploads/` holds earlier Stitch explorations the prototype started from, and it duplicates what's already in the files.
- **Data check**: the prototype uses invented names and IDs, not organizer data. The owner's secret scan runs on the staged diff before committing, as with every commit.
