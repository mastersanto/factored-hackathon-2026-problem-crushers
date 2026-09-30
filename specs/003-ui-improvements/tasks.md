# Tasks: UI improvements (language, source labels, phone width, accessibility)

**Input**: design documents in `specs/003-ui-improvements/`: spec.md, plan.md, research.md (R1-R12), data-model.md, contracts/ui.md, quickstart.md, and the approved prototype in `design/`

**Tests**: included. The owner's plan makes screenshots at desktop and phone width the acceptance check. SC-201, SC-203, SC-204, and SC-205 need automated measurement ([research R9](research.md#r9-acceptance-checks-screenshots-and-automated-accessibility)). The backend's 46 tests must keep passing unchanged (SC-206).

**Open items**: see [pending.md](pending.md).

**Deadline context**: submissions close 2026-10-05 at midnight, Colombia time. The MVP is **User Stories 1 and 2** (both P1): the chat in the customer's language, with clear source labels. Stories 3 and 4 follow if time allows.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: can run in parallel (different files, no dependency on an incomplete task).
- **[Story]**: US1-US4, from spec.md.
- Paths are relative to the repository root.
- **Visual reference**: for each screen, open the named `design/*.dc.html` file (it needs `design/support.js` next to it) and match its layout, spacing, and tokens. The differences listed in [research R10](research.md#r10-what-the-prototype-has-that-this-feature-doesnt-build) are intended: don't build those elements.

## Quality gates (after every task that changes code)

- `make test` (46 passed, unchanged);
- `cd frontend && npx tsc -b && npm run build`;
- `cd frontend && npm run check:ui` (once T008 exists; needs `make dev` running);
- the secret scan on the staged diff (zero matches).

`make eval` isn't needed, since no backend file changes. **If a task seems to need a backend change, stop: that's out of scope (FR-218).**

A task is checked off only when its gates pass.

---

## Phase 1: Setup

**Purpose**: a clean lock file, the dependencies, and the check harness.

- [X] T001 Restore `frontend/package-lock.json` with `git checkout frontend/package-lock.json`. The setup's `npm install` ran with npm 10, which dropped the `libc` fields. Then run every later install with npm 11 or later (`npm i -g npm@11` under nvm, or `npx npm@11 install ...`), so the lock keeps its format and `npm ci` in the `Dockerfile` (node:22-slim) still works.
- [X] T002 Add runtime dependencies `@fontsource/ibm-plex-sans` and `@fontsource/jetbrains-mono`, and dev dependencies `@playwright/test` and `@axe-core/playwright`, to `frontend/package.json`. Add the script `"check:ui": "playwright test"`. Then install Chromium once with `cd frontend && npx playwright install chromium` (on WSL, if it fails to start: `sudo npx playwright install-deps chromium`).
- [X] T003 [P] Create `frontend/playwright.config.ts`:
  - `testDir: 'e2e'`, `baseURL: 'http://localhost:5173'`, `outputDir: 'test-results'`, `workers: 1`, `retries: 0`;
  - four projects, `desktop-light` (1200×900), `desktop-dark` (1200×900, `colorScheme: 'dark'`), `phone-light` (375×812, `isMobile: true`, `hasTouch: true`), and `phone-dark`;
  - no `webServer` block: the developer runs `make dev` in rules mode, as in quickstart §2.
  - Also add `e2e` to the `include` of a new `frontend/tsconfig.e2e.json` referenced from `frontend/tsconfig.json`, so `tsc -b` type-checks the tests.
- [X] T004 [P] Ignore rules in `.gitignore`, already added during planning: the design export's `*.zip`, `.thumbnail`, and `uploads/`, plus `frontend/e2e/screenshots/`, `frontend/test-results/`, and `frontend/playwright-report/`

**Checkpoint**: `npm ci` works from the restored lock, and `npx playwright test --list` runs, even with no tests yet.

---

## Phase 2: Foundational (blocks every story)

**Purpose**: tokens, fonts, icons, the text dictionary, per-turn metadata, the page shell, and test helpers.

- [X] T005 [P] Replace the `:root` and dark blocks in `frontend/src/index.css` with the tokens from `specs/003-ui-improvements/design/handoff/tokens.css`, copied exactly, both themes. Then add:
  - `body { font-family: var(--font-sans); font-variant-numeric: tabular-nums; }`;
  - `:focus-visible { outline: 2px solid var(--focus-ring); outline-offset: 2px; }`;
  - a `.sr-only` utility for visually hidden text;
  - `@media (prefers-reduced-motion: reduce) { *, *::before, *::after { animation: none !important; transition: none !important; scroll-behavior: auto !important; } }`;
  - `overflow-wrap: anywhere` on message text and references.
  - Keep the existing class names working until the stories replace them. Per the prototype's notes: radius 8 px (4 px for labels), no shadows, no pill shapes.
- [X] T006 [P] Import `@fontsource/ibm-plex-sans/latin-400.css`, `-500.css`, `-600.css` and `@fontsource/jetbrains-mono/latin-400.css`, `-600.css` in `frontend/src/main.tsx`, before `./index.css`. No other font is loaded ([R8](research.md#r8-fonts-and-icons)).
- [X] T007 [P] Create `frontend/src/icons.tsx`:
  - export an `Icon` component: `({ name, size = 20 }) => <svg aria-hidden="true" focusable="false" width={size} height={size} viewBox="0 -960 960 960" fill="currentColor">…</svg>`;
  - include inline path data from Google Material Symbols Outlined (weight 400, Apache 2.0; attribution comment at the top of the file) for exactly these names: `account_balance, download, task_alt, route, expand_more, expand_less, check_circle, radio_button_checked, radio_button_unchecked, calculate, policy, info, support_agent, verified_user, help, gpp_bad, arrow_forward, lock, send, schedule, shield_lock, science, arrow_upward, priority_high, remove, upload_file, difference, block, inbox, flag, check, warning, refresh, cloud_off, rule, verified, close`;
  - type `name` as a union of those names, so a typo fails the type-check.
- [X] T008 Create `frontend/src/i18n.ts` per [data-model TextSet](data-model.md#textset-frontendsrci18nts):
  - `export type TextSet = {...}` and `export const TEXT: Record<Lang, TextSet>`, with **every** group in the data model: source labels, verdicts, charges, case card, chat frame (including `security.strip`), PDF, steps panel, session, and spoken names;
  - Spanish wording taken from `design/Screen Chat.dc.html` and `design/App Header.dc.html`; Portuguese written for this feature. For example, `verdict.bank_contact` is "Contato real do banco" ([R1](research.md#r1-where-the-texts-come-from-and-how-they-switch-language));
  - move `PDF_TEXT` out of `frontend/src/Chat.tsx` into it, and add `pdf.notYet` ("Disponible al terminar la consulta" / "Disponível ao terminar a consulta");
  - texts with values are functions, for example `case.sent: (id: string) => string`;
  - export `useText(lang: Lang): TextSet`.
  - **Constraint**: the type is `Record<Lang, TextSet>`, so a key missing in either language must fail `tsc -b`.
- [X] T009 Extend `Turn` in `frontend/src/useChat.ts` with `lang: Lang` and `at: number`. Set `at: Date.now()` when a turn is created. On the assistant turn's `done` event, set that turn's `lang` and also the preceding customer turn's `lang` (the customer's message is detected in the same turn, data-model "Turn"). Also:
  - export `stepProgress(turns): number | null`, the highest index in `['understand','decide','act','verify','escalate']` among the latest assistant turn's `step` events, or `null` before any turn ([data-model StepProgress](data-model.md#stepprogress-derived-steps-panel));
  - export `formatTime(at: number, country: string): string` → `HH:MM`, using `Intl.DateTimeFormat` with `timeZone` mapped as México/Mexico → `America/Mexico_City`, Colombia → `America/Bogota`, Argentina → `America/Argentina/Buenos_Aires`, and anything else → `America/Bogota` (the same mapping as `backend/app/transcript/record.py` `TIME_ZONES`, [R11](research.md#r11-times-on-messages));
  - change the network-error text so it no longer hard-codes Spanish: take it from `TEXT[lang]`.
- [X] T010 Rebuild the page shell in `frontend/src/App.tsx` per `design/App Header.dc.html`:
  - a navy header with the brand and "LATAM Bank";
  - a `nav` with `aria-label="Vista"` and "Cliente" / "Especialista" buttons carrying `aria-current="page"`, moving to a second row below 860 px;
  - the status line with an icon ("Datos al {as_of} · Claude activo" / "… · Modo reglas (sin IA)");
  - the security strip, customer view only, with its text from `TEXT[lang].security.strip`;
  - the footer "Demostración con datos sintéticos · Factored AI & Data Hackathon 2026".
  - Lift the conversation `lang` from `Chat` to `App` with a callback, and set `document.documentElement.lang` to it in an effect (FR-215). Keep it `'es'` on sign-in and in the specialist view.
- [X] T011 [P] Create `frontend/e2e/helpers.ts` with:
  - `signIn(page, labelMatch: RegExp)`: open `/`, click the demo customer whose label matches, and wait for the composer;
  - `send(page, text)`: fill the textbox named "Mensaje"/"Mensagem", press Enter, and wait for the send button to be enabled again;
  - `shot(page, name)`: save `e2e/screenshots/{project}/{name}.png`, full page;
  - `noSideScroll(page)`: expect `document.documentElement.scrollWidth <= document.documentElement.clientWidth`;
  - `spanishOnly()`: the list of `TEXT.es` string values (functions called with a sample value) that differ from their `TEXT.pt` counterpart, imported from `../src/i18n`.

**Checkpoint**: the app still works end to end in the old layout with the new tokens and fonts, `tsc -b` passes, and the header matches the prototype.

---

## Phase 3: User Story 1 - The whole chat in my language (Priority: P1) 🎯 MVP

**Goal**: every fixed text in the customer's chat follows the language of the latest assistant message (FR-201, FR-202).

**Independent test**: run the call check in Portuguese and the claim in Spanish. In the Portuguese run, none of the chat's fixed texts is in Spanish (SC-201).

- [X] T012 [P] [US1] Write `frontend/e2e/language.spec.ts`:
  - sign in as a demo customer and send "Recebi uma ligação do banco em {date}, é real?" (take the date from the customer's hint as `App.tsx` `suggestionsFor` does, or use a customer whose label mentions an outbound contact);
  - after the reply, expect no element inside the `main` landmark, other than customer-typed text, to contain any string from `spanishOnly()`;
  - then run the Spanish claim path and expect the Spanish strings to be present;
  - also assert that `<html lang>` is `pt` after the Portuguese reply and `es` after a Spanish one.
  - The test fails until T013-T016 are done.
- [X] T013 [P] [US1] Create `frontend/src/components/VerdictCard.tsx` per `design/Screen Chat.dc.html` outcomes `c-good`, `c-warn`, and `c-bad`:
  - props `{ verdict, lang, children }`;
  - `role="status"`, a tone class `good|warn|bad`, an icon (`verified_user|help|gpp_bad`), and a title from `TEXT[lang].verdict[verdict]`;
  - `children` holds the following message's statements (US2 renders them).
- [X] T014 [P] [US1] Create `frontend/src/components/CaseCard.tsx` per the prototype's outcome `b`:
  - an `article` with `aria-label={TEXT[lang].case.label(caseId)}`, the `support_agent` icon, `case.sent(caseId)`, and a three-step status list: received with `check_circle` done, specialist review with `radio_button_checked` next, answer with `radio_button_unchecked` to do;
  - **no dates, and no "Ahora" on the middle step**;
  - `case.keep(caseId)` and `case.pdfHint`.
  - **Constraint**: it takes only `caseId` from the `handoff` event, "the only field the customer's device receives (FR-219)" ([R4](research.md#r4-case-card-after-a-handoff)).
- [X] T015 [P] [US1] Create `frontend/src/components/CandidateList.tsx` per the prototype's outcome `a` (picker):
  - one card per candidate with merchant, `when`, the amount in bold, `TEXT[lang].status.pending` when `status === 'Pending'`, and a primary button `candidate.pick` that calls `onPick(String(option))`;
  - after the customer picks, the chosen card shows `candidate.picked` with `check_circle`, and the others are muted.
  - **Don't build "Ninguno de estos cargos coincide"** ([R10](research.md#r10-what-the-prototype-has-that-this-feature-doesnt-build)).
- [X] T016 [US1] Rewire `frontend/src/Chat.tsx` to take every fixed text from `useText(lang)`:
  - the opening line as an intro block (not a message: no time, no "Asistente", [contract](contracts/ui.md#customer-chat-follows-the-conversations-language-fr-201)) with `intro(firstName)`, inviting the customer to write in Spanish or Portuguese in both languages (US1 scenario 3);
  - the composer placeholder and send button, the PDF button and its outcomes, the typing text, `VerdictCard` for `verdict` events, `CaseCard` for `handoff` events, and `CandidateList` for `candidates` events.
  - Messages already shown keep their text (FR-202).
- [X] T017 [US1] Add the session-ended card to `frontend/src/Chat.tsx`, per the prototype's outcome `expired`:
  - when the latest assistant turn has an `error` event with `code` `session_expired` or `turn_limit`, hide the composer and show a `role="alert"` card with the `schedule` icon, `session.expiredTitle`, the server's `text` as the body, and a `session.restart` button that calls a new `onRestart` prop;
  - in `frontend/src/App.tsx`, pass `onRestart={() => setSession(null)}`;
  - also map a 401 from the PDF download to the same card.

**Checkpoint**: `language.spec.ts` passes in all four projects. US1 is done.

---

## Phase 4: User Story 2 - I can tell what each source label means (Priority: P1) 🎯 MVP

**Goal**: labels name their kind in words, show their reference as visible text, and are explained in the chat (FR-204 to FR-207).

**Independent test**: an answer with verified, estimated, and rule statements shows three worded labels with visible references. The explainer opens by tap, click, and keyboard, in the conversation's language.

- [X] T018 [P] [US2] Write `frontend/e2e/labels.spec.ts`:
  - claim path in rules mode, up to the explained charge;
  - expect at least one label with text VERIFICADO and one with POLÍTICA, each followed by a visible reference whose text equals the statement's `source` (read it from the SSE response via `page.waitForResponse('/api/chat')`, or assert the `transaction:` prefix);
  - expect no element with a `title` attribute to be the only carrier of a reference;
  - focus the explainer button with Tab, press Enter, expect `aria-expanded="true"` and three `dt` terms;
  - in the Portuguese run, expect the labels in Portuguese.
- [X] T019 [P] [US2] Create `frontend/src/components/SourceLabel.tsx`:
  - props `{ basis, source, lang }`;
  - renders a 24 px-high, 4 px-radius, uppercase label with an icon (`check_circle|calculate|policy`, `aria-hidden`) and `TEXT[lang].basis[basis]`, coloured with `--good`/`--warn`/`--accent` on the matching `-soft` background, as in the prototype;
  - then `source` in `--font-mono` 12 px `--muted`, **exactly as sent**, with no `title` tooltip. Nothing is rendered for the reference when `source === null`;
  - accessible text reads "{word}: {source}", with a `.sr-only` separator.
  - **Constraint**: `basis` maps "`known` → verified, `guessed` → estimate, `rule` → rule", and the reference is "shown exactly as sent; not shown when `null` (FR-207, US2 scenario 3)".
- [X] T020 [US2] Create `frontend/src/components/Statements.tsx` per [R2](research.md#r2-statements-and-their-source-labels):
  - props `{ text, statements, lang }`;
  - when `text === statements.map(s => s.text).join(' ')`, render a `ul` with one `li` per statement: its text, then a `SourceLabel`;
  - otherwise render `<p>{text}</p>` followed by a `sources.title` heading ("Fuentes" / "Fontes") and a `ul` of `SourceLabel`s only;
  - both variants end with the `sources.toggle` button ("¿De dónde sale este dato?" / "De onde vem esta informação?", `info` icon, `aria-expanded`, `aria-controls`) that shows a `dl` of the three `basis.explain.*` texts.
  - **Every statement shows its label**, including questions and refusals ([R2, adapted from the prototype](research.md#r2-statements-and-their-source-labels)). Never alter or drop `text`.
- [X] T021 [US2] Use `Statements` in `frontend/src/Chat.tsx` for every `message` event, inside the assistant bubble (`--surface-2` background), and inside `VerdictCard` when a `verdict` event is followed by a `message` in the same turn. Remove the old `BASIS_LABEL` map and the `.statements`/`.badge` CSS in `frontend/src/index.css`.

**Checkpoint**: `labels.spec.ts` and `language.spec.ts` pass. **The MVP (US1 + US2) can be committed and deployed here.**

---

## Phase 5: User Story 3 - Use it on a phone (Priority: P2)

**Goal**: every screen works from 360 px with no sideways scroll, a composer that stays visible, a steps drawer, and 44 px tap targets (FR-208 to FR-211).

**Independent test**: at 375 px, complete the claim and call-check paths and open the specialist queue with no sideways scroll, and every control is at least 44 × 44 px (SC-203).

- [X] T022 [P] [US3] Write `frontend/e2e/phone.spec.ts`, phone projects only:
  - on sign-in, chat (claim path to the case card, and the call check), and specialist views, call `noSideScroll`;
  - for each visible `button, a, input, [role=button]`, expect the bounding box to be at least 44×44;
  - after sending a message, expect the textbox to be inside the viewport;
  - expect the steps drawer button to have `aria-expanded="false"` by default, and to toggle.
- [X] T023 [P] [US3] Create `frontend/src/components/StepsPanel.tsx` per the prototype's rail and mobile drawer:
  - props `{ progress: number | null, trace: ChatEvent[], lang, variant: 'rail' | 'drawer' }`;
  - five steps from `TEXT[lang].steps`, each with `check_circle` + `steps.done` (index < progress), `radio_button_checked` + `steps.now` + `aria-current="step"` (index = progress), or `radio_button_unchecked` (after, or `progress === null`);
  - `rail`: an `aside` with `aria-label={steps.title}`, 300 px wide;
  - `drawer`: a full-width button (min-height 56 px, `route` icon, `steps.title`, `steps.progress(n, name)`, `expand_more|expand_less`, `aria-expanded`), closed by default;
  - at the bottom of both, a closed `<details>` with `summary` `steps.technical` ("Detalle técnico" / "Detalhe técnico"), holding the existing trace list (step name + JSON of the non-internal detail) ([R3](research.md#r3-steps-panel-cómo-revisamos-su-caso)).
- [X] T024 [US3] Rebuild the chat layout in `frontend/src/Chat.tsx` and `frontend/src/index.css` per `design/Screen Chat.dc.html`:
  - customer bar (the first name's initial on navy, first name, country · label, the "Cambiar cliente" link-button, the PDF button on the right; it wraps on phones);
  - then `StepsPanel variant="drawer"` below 860 px;
  - then the conversation card with message log, quick replies, examples, and composer, next to `StepsPanel variant="rail"` at 860 px and wider;
  - the page scrolls as one, with no fixed-height chat box. The composer is `position: sticky; bottom: 0` with the `--surface` background, and heights use `dvh`;
  - customer bubbles use `--bubble-customer`, max-width `min(520px, 85%)`; assistant blocks are max 680 px with the `account_balance` avatar;
  - each message ends with `formatTime(turn.at, country)`, plus `· Asistente`/`· Assistente` for assistant turns;
  - quick replies and examples are 44 px-high buttons that wrap;
  - move `session-bar` from `frontend/src/App.tsx` into the customer bar.
  - **Don't build "Hablar con una persona"** ([R10](research.md#r10-what-the-prototype-has-that-this-feature-doesnt-build)).
- [X] T025 [US3] Rebuild sign-in in `frontend/src/App.tsx` (`DemoLogin`) per `design/Screen Login.dc.html`:
  - `h1` "Revisemos juntos su cargo", the intro line, and the `science` notice about synthetic customers;
  - a `ul` with `aria-label="Clientes de prueba"` of card buttons showing the initial, first name, country, label, and "Empezar →". Show **only** fields the API returns: no full name, card, or currency ([R10](research.md#r10-what-the-prototype-has-that-this-feature-doesnt-build));
  - loading: a `role="status"` line plus 6 `aria-hidden` placeholder cards using `--skeleton`;
  - error: a `role="alert"` block with `cloud_off`, "No pudimos conectar. Sus datos están a salvo; intente de nuevo.", and a "Reintentar" button calling `refetch()`;
  - the card being opened shows "Abriendo…" with `aria-busy`, and the others are disabled.
- [X] T026 [US3] Restyle the specialist view in `frontend/src/AgentQueue.tsx` per `design/Screen Specialist.dc.html`:
  - `h1` "Casos para revisar" with count and ordering note;
  - the PDF check `section` with `aria-labelledby`, a large file `label` drop zone (click or drop, `onDrop` → the same handler), and result blocks with icon, title word, and explanation for match / altered / unknown_version / unreadable, using the prototype's texts;
  - cards with a coloured left rule, and priority as icon + word (Urgente / Alta / Normal);
  - case-type labels mapped as in [contracts/ui.md](contracts/ui.md#specialist-view-spanish-fr-203) (an unknown code is shown as it is);
  - fields as `dl` rows, stacked on phones;
  - the facts table in a `div` with `overflow-x: auto`;
  - security flags as a list with `flag`, or "Sin alertas";
  - the empty state with `inbox` and a "Ir a la vista Cliente" button (pass an `onGoToCustomer` prop from `App.tsx`).
  - **Don't build "Tomar caso"**.

**Checkpoint**: `phone.spec.ts` passes. The screenshots at 375 px match the prototype's phone frames.

---

## Phase 6: User Story 4 - Usable with a keyboard and a screen reader (Priority: P2)

**Goal**: keyboard-only use, live announcements, spoken names, `lang` marks, AA contrast, and reduced motion (FR-212 to FR-217).

**Independent test**: axe reports 0 violations on the three screens in both themes, and the claim path is completed with the keyboard alone (SC-204, SC-205).

- [X] T027 [P] [US4] Write `frontend/e2e/a11y.spec.ts`:
  - run `new AxeBuilder({ page }).withTags(['wcag2a','wcag2aa','wcag21aa']).analyze()` on sign-in, on the chat after an explained charge, after the case card, after a scam verdict, and on the specialist view (with at least one case and one PDF-check result), and expect `violations` to equal `[]`;
  - keyboard test on `desktop-light`: complete sign-in → claim → case card using only `page.keyboard` (Tab, Shift+Tab, Enter, Space, typing), with no `click()`;
  - expect `role=log` to exist with `aria-live="polite"`;
  - expect every assistant message element to have a `lang` attribute equal to the turn's language;
  - with `page.emulateMedia({ reducedMotion: 'reduce' })`, expect the log's scroll to use `behavior: 'auto'` (spy on `Element.prototype.scrollIntoView`).
- [X] T028 [US4] Accessibility wiring in `frontend/src/Chat.tsx`:
  - the message list is `role="log"`, `aria-live="polite"`, `aria-label={aria.messages}`;
  - each message wrapper has `lang={turn.lang}`;
  - the composer input has a real `<label className="sr-only">` with `composer.label`;
  - quick replies and examples are in `role="group"` with `aria-label`;
  - the PDF outcome is `role="status"`;
  - after sending, focus returns to the input (`inputRef.current?.focus()`);
  - scroll to the newest message with `behavior: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth'`;
  - the typing indicator is static dots plus text, `aria-hidden` on the dots.
- [X] T029 [US4] (2026-09-30: axe reported 0 violations on the first run in all four projects; no token changed, so no R13.) Run `a11y.spec.ts` and fix every reported violation in the component that causes it: `frontend/src/components/*.tsx`, `frontend/src/App.tsx`, `frontend/src/AgentQueue.tsx`, or `frontend/src/index.css`.
  - If a contrast failure comes from a token in `design/handoff/tokens.css`, darken or lighten only that token, the smallest change that passes. Record the change and its ratio in [research.md](research.md), under a new "R13. Token changes after the contrast check".

**Checkpoint**: `a11y.spec.ts` passes in all four projects.

---

## Phase 7: Polish and cross-cutting

- [X] T030 [P] Write `frontend/e2e/screens.spec.ts`, which takes the reference screenshots named in [quickstart §2](quickstart.md#2-automated-ui-checks):
  - sign-in (ready);
  - chat (explained charge with the explainer open, case card, bank contact in PT, no record, scam, refusal);
  - specialist (queue with a match result, and empty);
  - each in all four projects, saved with `shot()`.
  - No assertions beyond `noSideScroll`: they are for visual comparison with `design/`.
- [X] T031 Run the full quality gates:
  - `make test` (expect 46 passed);
  - `cd frontend && npx tsc -b && npm run build`;
  - `npm run check:ui` against `make dev` in rules mode.
  - Then compare the screenshots in `frontend/e2e/screenshots/` with the matching frames in `design/Explica este cargo.dc.html`. Fix any difference not listed in [R10](research.md#r10-what-the-prototype-has-that-this-feature-doesnt-build).
- [ ] T032 (owner) Run the manual checks in [quickstart §3](quickstart.md#3-manual-checks): a real phone with the keyboard open, NVDA or VoiceOver on the claim path, the label test with 3 people (SC-202), and reduced motion. Record the results as a dated "Results" section at the end of `specs/003-ui-improvements/quickstart.md`.
- [X] T033 [P] Update `README.md`: in "How it works", one line on the chat following the customer's language, with worded source labels and phone and accessibility support. Also add `npm run check:ui` to "Run it locally". Take a new screenshot for `docs/slides/` only if the owner asks.
- [X] T034 [P] Check off the tasks in this file. Update `specs/003-ui-improvements/spec.md` `**Status**` to "Implemented", with the date, and add a "Results" line for each success criterion (SC-201 to SC-206), with its measurement.
- [ ] T035 (2026-09-30, partial: Docker isn't reachable from this WSL, since only the Windows CLI is installed. What the image build depends on was checked instead: `npm ci` from the lock plus `npm run build` on a clean copy both pass, and `COPY frontend/` with `.dockerignore` excludes the screenshots. `make docker` is still pending.) Build the container to prove the fonts and lock work in `npm ci` (`make docker`), then run it (`make docker-run`) and open `http://localhost:8080` at phone width. **Deploying to Azure (`make deploy-azure`) is the owner's call**, after the pull request merges.
- [ ] T036 (2026-09-30: committed and pushed on the owner's request with a **substitute scan**, since the official scan files aren't on this machine. The substitute checked for AWS keys, API keys, the local HMAC key, S3 and bucket references, customer, transaction, and contact IDs, and dataset names and merchants, with 0 findings. It also replaced dataset values hard-coded in the tests with values built at run time. **The official scan is still to run before merging.**) Stage the changes: `specs/003-ui-improvements/` (without the ignored design export files), `frontend/`, `.gitignore`, `docs/build-plan.md`, and `README.md`.
  - Run the secret scan on the staged diff (must be 0).
  - Commit on `003-ui-improvements`, push, and give the owner the compare link. The owner opens the pull request.

---

## Dependencies and execution order

```text
Phase 1 Setup (T001 → T002 → T003; T004 done)
        ↓
Phase 2 Foundational (T005, T006, T007, T011 in parallel; T008 → T009 → T010)
        ↓
  ┌─────────────┬──────────────┐
  US1 (P1)      US2 (P1)        ← MVP; US2's T021 edits Chat.tsx after US1's T016
  └─────┬───────┴──────┐
        US3 (P2)        US4 (P2)  ← both edit Chat.tsx: do US3's T024 before US4's T028
        └──────┬───────┘
          Phase 7 Polish (T030-T036)
```

- **Between stories**:
  - US1 and US2 touch different new components, but both wire into `frontend/src/Chat.tsx`: do T016 before T021.
  - US3's layout rebuild (T024) and US4's wiring (T028) also both edit `Chat.tsx`: do T024 first.
  - US4's axe fixes (T029) come after US3, since layout changes affect contrast and target sizes.
- **Within a story**: write the story's `e2e/*.spec.ts` first. It fails. Then build the components, then wire them into the screen.

## Parallel examples

- **Phase 2**: T005 (`index.css`), T006 (`main.tsx`), T007 (`icons.tsx`), and T011 (`e2e/helpers.ts`) touch different files.
- **US1**: T012, T013, T014, and T015 in parallel (test + three new components), then T016 and T017.
- **US2**: T018 and T019 in parallel, then T020 → T021.
- **US3**: T022 and T023 in parallel. T025 (`App.tsx`) and T026 (`AgentQueue.tsx`) can run alongside T024 (`Chat.tsx`).
- **Polish**: T030, T033, and T034 in parallel.

## Implementation strategy

1. **MVP (US1 + US2)**:
   - Setup → Foundational → US1 → US2.
   - This closes the language gap against spec 001's FR-015 and makes the source labels readable: the two P1 items, and the ones judges see first.
   - It can be committed and deployed on its own.
2. **Phone (US3)**: the layout rebuild that brings the prototype's look to every screen.
3. **Accessibility (US4)**: wiring and the axe fixes. It comes last because it checks the final layout.
4. **Polish**: reference screenshots, manual checks, docs, the container check, and the commit.

If time runs short before 2026-10-05, stop after any checkpoint. Every phase leaves a working app, and the backend and its 46 tests are untouched throughout.
