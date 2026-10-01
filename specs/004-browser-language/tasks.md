# Tasks: The whole app in English, Spanish, or Portuguese

**Input**: design documents in `specs/004-browser-language/`: spec.md, plan.md, research.md (R1-R14), data-model.md, contracts/http-api.md, contracts/ui.md, quickstart.md

**Tests**: included.
- Constitution III requires a test that fails without each new safety behaviour, so every guard gets English phrases, checked in all three languages with the deliberately wrong fake model (SC-406).
- Constitution V requires English evaluation cases.
- SC-401, SC-402, SC-405, SC-408, and SC-409 need automated checks ([contracts/ui.md](contracts/ui.md#checks), [quickstart.md](quickstart.md)).

**Deadline context**: submissions close 2026-10-05 at midnight, Colombia time, and the video is not recorded. Deliver in the three increments of [research R14](research.md#r14-delivery-order-given-the-deadline):
1. **Interface**: Phase 3 (US1) and Phase 7 (US4) before sign-in. Frontend only.
2. **Conversation**: Phases 4, 5, and 6 (US2, US3, US5). Includes the demo path: Spanish, then a switch to Portuguese.
3. **Records**: Phase 8 (the PDF and the specialist view) and Phase 9 (the evaluation).

Each increment ships only after every gate passes, and redeploying needs the owner's approval.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: can run in parallel (different files, no dependency on an incomplete task).
- **[Story]**: US1-US5, from spec.md.
- Paths are relative to the repository root.

## Quality gates (after every task that changes code)

- `make test`: every existing test passes **unchanged**. FR-429 forbids editing an existing assertion to make it pass; if one fails, the change is wrong.
- `cd frontend && npm run build` (the type-check fails if any text is missing in en, es, or pt).
- `cd frontend && npm run check:ui`, against `SESSIONS_PER_IP_HOUR=1000 LLM_DISABLED=1 make dev`.
- `make eval` after any change under `backend/app/workflow/`, `backend/app/language/`, `backend/app/llm/`, or `backend/app/policy/`. The Spanish and Portuguese rows of `docs/evaluation.md` must not get worse.
- The secret scan on the staged diff (zero matches).

A task is checked off only when its gates pass.

---

## Phase 1: Setup

**Purpose**: pin what must not change before anything changes, and add the shared language constants.

- [X] T001 Pin the r1 PDF bytes before any transcript change. Add `test_r1_render_is_frozen` to `backend/tests/test_transcript.py`:
  - build a schema-1 snapshot by hand with made-up text only (no dataset values): two customer messages, one message with statements of all three bases, one candidates entry, one verdict, one handoff, `lang: "pt"`;
  - sign it with a fixed test key (`fingerprint(..., key=b"test-key")`, then `check_code`);
  - render it with the current `app.transcript.render.render`;
  - assert the SHA-256 of the bytes equals a constant recorded now.

  Never commit the PDF itself (`CLAUDE.md`).
- [X] T002 [P] Create `backend/app/language/__init__.py` with `LANGS = ("en", "es", "pt")`, `Lang = Literal["en", "es", "pt"]`, and `BASE_LANG = "en"`, with a docstring citing constitution v1.1.0 (English is the base language).
- [X] T003 [P] Add `conversation-*.pdf` to `.gitignore`, next to `conversacion-*.pdf` and `conversa-*.pdf` (research R11).
- [X] T004 [P] Set `locale: 'es-MX'` in the `use` block of all four projects in `frontend/playwright.config.ts` (research R13). Run `npm run check:ui` and confirm the same counts as before (59 passed, 9 skipped).

---

## Phase 2: Foundational (the interpreter and translator boundaries, with no change in behaviour)

**Purpose**: introduce the two boundaries the owner asked for (research R1, R2) and the statement recipes (R6), with byte-identical output for Spanish and Portuguese. US2, US3, and US5 depend on this phase. US1 and US4 are frontend-only and can run in parallel with it.

- [X] T005 Create `backend/app/language/interpreter.py` with `interpret(text: str, *, stage: str, merchants: list[str], today: datetime, session_customer_id: str, llm) -> Understanding`:
  - move the body of `Engine._understand` from `backend/app/workflow/engine.py` here, keeping every rule exactly:
    - the rules scan always runs on the original text;
    - the model is skipped at stages `statement` and `contact_shared`;
    - `other_customer_reference` and `injection_suspected` are OR-ed into the model's result;
    - at `confirm`, a rules `file_claim` forces `file_claim`, and a model-only `confirm_mine` becomes `reconfirm`;
  - make `Engine._understand` a one-line call to it.
- [X] T006 Extend `Statement` in `backend/app/workflow/engine.py` with `key: str | None = None` and `params: dict = Field(default_factory=dict)`. At every place a `Statement` is built in `engine.py`, set:
  - `key`: the `messages.T` key, or `f"rule:{rule.id}"` for country rights;
  - `params`: the raw verified values, not formatted strings: `amount` (float), `currency`, `when`/`day`/`last` (ISO text), `merchant`, `city`, `country`, `channel` (code, e.g. `"POS"` or `"whatsapp"`), `product` (code, e.g. `"Tarjeta Débito"`), `kind` (transaction-type code), `last4`, `n`, `case`, `name`.
- [X] T007 Create `backend/app/language/translator.py` with:
  - `render_statement(st, lang) -> str`: formats `st.params` with the per-language helpers (`messages.money`, `messages.when`, `messages.day`, and the `CHANNEL_NAMES`, `PRODUCT_NAMES`, `TX_KINDS` lookups), then fills `messages.T[key][lang]`, or `policy.rules` text for `rule:<id>`;
  - `render(statements, lang) -> list[Statement]`: copies with `text` replaced and `key`, `params`, `basis`, and `source` unchanged.

  Then make the engine produce every statement's `text` through `render_statement`, so there is one path from recipe to text.
- [X] T008 Keep candidate cards' raw values server-side: in `Engine._card` in `backend/app/workflow/engine.py`, add `raw: {amount, currency, date (ISO), merchant, type, status}` to each item.
- [X] T009 In `backend/app/api/main.py` `chat().stream()`:
  - give the recorder the full event (`s.transcript.record(event)`);
  - serialize a public copy without `key`, `params` (inside `statements`), or `raw` (inside candidate items).

  The browser receives exactly what it receives today.
- [X] T010 In `backend/app/transcript/record.py`:
  - keep `key`, `params`, `raw`, a per-entry `lang` (the turn's `done.lang`), and `phrased_by` on recorded entries;
  - make `snapshot()` drop all of these, so schema-1 snapshots, and the PDFs and check codes built from them, are unchanged. T001 must still pass.
- [X] T011 Add `backend/tests/test_language.py` with:
  - `test_render_round_trip_es_pt`: for every statement each existing demo path emits (normal, pending, claim with rights, scam, real contact, no record, compliance, unauthorized, out of scope), `render_statement(st, st_lang) == st.text`;
  - `test_stream_has_no_recipes`: no streamed event contains `key`, `params`, or `raw`.

  Then run `make eval` and confirm `docs/evaluation.md` is byte-identical except its date line.

**Checkpoint**: same behaviour, same evaluation, same PDFs. The boundaries exist.

---

## Phase 3: User Story 1 - The app opens in my browser's language (Priority: P1) 🎯 MVP

**Goal**: every fixed text on every screen comes from the browser's preference (English fallback), decided before the first render.

**Independent Test**: open the app with `en-US`, `es-MX`, `pt-BR`, `fr-FR`, and `fr-FR,es`, and check that every fixed text on sign-in, the header, and the specialist view is in English, Spanish, Portuguese, English, and Spanish respectively (SC-401, SC-402).

- [X] T012 [P] [US1] Add a stable `scenario` id to each item of `GET /api/demo/customers` in `backend/app/api/main.py` (data-model: Demo customer): `fraud_flagged`, `pending`, `mx_debit_48h`, `co_purchase`, `ar_purchase`, `compliance`, `bank_message`. Keep `label` unchanged. Add a test in `backend/tests/test_language.py` that every item has one of these ids.
- [X] T013 [P] [US1] Create `frontend/src/language.ts` with:
  - `pickLanguage(prefs: readonly string[], stored: string | null): Lang`: "the stored choice, else the first preference whose primary subtag is en, es, or pt, else `en`", where the primary subtag is lower-cased and taken before the first `-`;
  - `readStoredLanguage()` and `storeLanguage(lang)`: use `localStorage["app-language"]`, wrapped in try/catch ("reading or writing it never throws");
  - `LanguageContext` and `useLanguage()`, giving `{ lang, setLang }`.
- [X] T014 [US1] In `frontend/src/api.ts`, set `Lang = 'en' | 'es' | 'pt'` and add `scenario` to `DemoCustomer`. In `frontend/src/i18n.ts`:
  - extend `TextSet` with:
    - `app`: view tabs, aria name of the nav, the health line (data date, "Claude active", "Rules mode (no AI)", "Connecting…"), and the footer;
    - `signIn`: heading, lead, synthetic notice, loading, connection error, retry, list aria name, start, opening, the session-limit error, the failed-start error;
    - `scenario`: `Record<ScenarioId, string>`;
    - `specialist`: every text in `AgentQueue.tsx`, including the priority labels, case types, verification results, field names, and the empty and error states;
  - fill `es` by moving the existing Spanish strings verbatim, and `pt` with Brazilian Portuguese in the same register as the chat's `pt` set;
  - update the header comment: specs/003 FR-203 is replaced by specs/004 FR-408.
- [X] T015 [US1] Add the complete `en` `TextSet` to `frontend/src/i18n.ts`, including every chat text from specs/003.
  - The `intro` and `BOTH_LANGUAGES` lines must say the assistant answers in **Spanish or Portuguese**, because English replies arrive only with US2 (T027 changes them).
  - The type `Record<Lang, TextSet>` must compile.
- [X] T016 [US1] In `frontend/src/main.tsx`, before `createRoot`:
  - compute `const lang = pickLanguage(navigator.languages ?? [], readStoredLanguage())`;
  - set `document.documentElement.lang = lang`;
  - render `<App />` inside a provider initialised with it (FR-404: no flash).
- [X] T017 [US1] In `frontend/src/App.tsx`, take every fixed text from `TEXT[appLang]`: header, nav, health line, security strip, footer, `DemoLogin` (heading, lead, notice, loading, error, retry, start, opening, both sign-in errors), and scenario labels via `TEXT[appLang].scenario[c.scenario]`.
  - Until US3 lands, the chat keeps specs/003's rule: its fixed texts follow the latest reply's language, and before the first reply they use the app language.
  - `<html lang>` follows the language of the visible fixed texts.
- [X] T018 [P] [US1] In `frontend/src/AgentQueue.tsx`, take every fixed text from `TEXT[appLang].specialist`. Customer words, facts, and IDs are shown as recorded.
- [X] T019 [US1] In `frontend/e2e/helpers.ts`:
  - `customer()` finds the item by `scenario` (map `SCENARIO` to ids);
  - `signIn()` clicks the card by `TEXT[lang].scenario[id]` for the page's language (default `es`);
  - `DemoCustomer` gains `scenario`.

  Every existing spec must pass unchanged in behaviour.
- [X] T020 [P] [US1] Add `frontend/e2e/detect.spec.ts`:
  - `en-US`, `es-MX`, `pt-BR`, `fr-FR` give EN, ES, PT, EN;
  - `['fr-FR', 'es']` gives ES;
  - an empty list gives EN (set through `page.addInitScript` overriding `navigator.languages`);
  - a stored `app-language = 'pt'` beats an `en-US` browser;
  - for each case, `<html lang>` and the sign-in heading are already right when the page is first visible (read them in `addInitScript` on `DOMContentLoaded`), with no switch afterwards.
- [X] T021 [US1] Extend `frontend/e2e/a11y.spec.ts` and `frontend/e2e/phone.spec.ts` with English runs (`test.use({ locale: 'en-US' })`) of sign-in and the specialist view: 0 axe violations in both themes, 0 sideways scroll at 375 px, and tap targets of at least 44 px.

**Checkpoint**: increment 1, part 1. Frontend and one additive API field. It can ship on its own.

---

## Phase 4: User Story 2 - I can talk to the assistant in English (Priority: P1)

**Goal**: the whole dispute workflow in English, in rules mode and with the model, with the same decisions and guards.

**Independent Test**: run the three required cases, the scam check, and the refusal of another customer's data in English, in rules mode, and compare each with its Spanish counterpart.

- [X] T022 [P] [US2] In `backend/app/workflow/messages.py`:
  - add `"en"` for every key of `T`, and to `MONTHS`, `CHANNEL_NAMES`, `PRODUCT_NAMES`, `TX_KINDS`, and `QUICK_REPLIES`. English goes first in each dict as the source text; Spanish and Portuguese are untouched word for word;
  - make `money(amount, currency, lang)` give `1,234.56 USD` for `en` and the current format for `es` and `pt`;
  - make `when` and `day` give `June 12, 2026, 14:05` and `June 12, 2026` for `en`;
  - English wording uses the same facts and placeholders as Spanish, with no promises and no request for secrets (FR-419);
  - English quick replies: confirm `["Yes, it was me", "It wasn't me"]`; statement `["I have my card and didn't share any code", "I shared a code over the phone", "I lost my card"]`; contact_shared `["Yes, I shared it", "No, I didn't share anything"]`.
- [X] T023 [P] [US2] Add `"en"` texts to every rule in `backend/app/policy/rules.py`, including `PROVISIONAL_CREDIT_MX`, with the same ids and meaning. Update the module docstring: the English texts are team translations of desk research, not legal advice.
- [X] T024 [US2] In `backend/app/workflow/understanding.py`:
  - **Language**: `Understanding.language` becomes `Literal["en", "es", "pt"] | None` (None = unclear).
  - **Detection** (research R4): add `EN_MARKERS` and `ES_MARKERS` next to `PT_MARKERS`, scored on the normalised text. The language is clear only when the top score is at least 1, strictly above the others, and the message has at least two words of letters.
  - **English keywords**, from the exact lists in research R3:
    - `SECRET`, plus the asked words "asked", "requested", "give", "send";
    - `INJECTION`;
    - `CLAIM`: "wasn't me", "was not me", "not me", "didn't make", "did not make", "don't recognize", "do not recognize", "not mine", "fraud", "stolen", "dispute";
    - `MINE`: "it was me", "yes it was me", "i made it", "i recognize it", "that's mine";
    - `CONFIRM_YES`/`CONFIRM_NO`: add "yes", "yeah", "nope";
    - `CONTACT`, `CHANNEL_WORDS` ("text message", "call", "email", "notification"), `OUT_OF_SCOPE` ("loan", "balance", "transfer money", "open an account"), `GREETING` ("hi", "hello", "good morning"), `PROBLEM`, and charge words ("charge", "transaction", "payment", "debit");
    - `_yes_no` and `_yes_no_shared` in `engine.py`: add English.
  - **Dates and amounts** (research R5): English month names ("June 12", "12 June"), "yesterday", and "today". Numeric dates stay day first.
- [X] T025 [US2] In `backend/app/llm/claude.py`:
  - `_LLMUnderstanding.language` becomes `Literal["en", "es", "pt", "unclear"]`;
  - `UNDERSTAND_SYSTEM` names English, Spanish, and Portuguese, and says to answer `unclear` for short or mixed messages;
  - map `unclear` to None, and apply the two-word minimum from T024;
  - `LANG_NAME["en"] = "English (clear, polite)"`;
  - add the English promises from research R5 to `PROMISES`.
- [X] T026 [US2] Accept English end to end:
  - **Engine** (`backend/app/workflow/engine.py`): when `u.language` is None, keep `s.lang`; `done.lang` may be `en`.
  - **Recorder** (`backend/app/transcript/record.py`): `commit()` accepts any of `LANGS`.
  - **Session** (`backend/app/api/main.py`): `SessionRequest` gains `lang: Literal["en", "es", "pt"] = "es"`, which sets `Session.lang`, and the response echoes `lang` (contracts/http-api.md).
  - **Frontend** (`frontend/src/api.ts`): `startSession(customer_id, lang)` sends the app language.
- [X] T027 [US2] In `frontend/src/i18n.ts`, change the `intro` of all three sets and `BOTH_LANGUAGES` to say the customer can write in English, Spanish, or Portuguese.
- [X] T028 [US2] Add English workflow and guard tests to `backend/tests/test_language.py`, in rules mode, mirroring `test_workflow.py` and `test_guards.py`:
  - **Workflow**: normal path (explain and "Yes, it was me"); human-required claim ("It wasn't me", a statement, rights in English); ambiguous request; scam that asked for a code, escalated when shared; real bank message; another customer's ID refused; out of scope.
  - **Guards**: a parametrized test that runs each guard phrase in en, es, and pt with the deliberately wrong fake model (it always says `confirm_mine`, never flags anything). Each guard must fire in all three languages (SC-406).
  - **Rest**: English quick replies are understood; an English model rewording with a promise is rejected by `faithful`.
- [X] T029 [US2] In `backend/app/eval/cases.py`:
  - add `"en"` to every phrasing dict: `DESCRIBE`, `CONFIRM`, `CLAIM`, `STATEMENT`, `VAGUE`, `OUT`, `SCAM`, `SHARED_YES`, `SHARED_YES_CODE`, `STATEMENT_CARD`, `CONTACT`, `CHANNEL_WORD`, `UNAUTH`, `INJECT`;
  - add `"en"` to every `HELDOUT` group. Write these **before** tuning the rules on English, and never use them to tune;
  - extend `_date` to English;
  - loop over `("es", "pt", "en")`, with English last, so the Spanish and Portuguese random draws stay identical. Give English its own seed offsets (`+2`), leaving the existing `(lang == "pt")` offsets unchanged;
  - in `backend/app/eval/report.py`, compute the language count instead of the hard-coded "2 languages (Spanish, Portuguese)".
- [X] T030 [US2] Run `make eval`. Then:
  - confirm the Spanish and Portuguese rows in `docs/evaluation.md` match those before T029;
  - check English: 0 unsafe outcomes, and correct outcomes within 5 points of Spanish (SC-403);
  - if English falls short, fix the rules using the **dev** set only (seed 7), with a general fix and a regression test (constitution V). Never fix it with case-specific patches.

**Checkpoint**: English conversations work in rules mode, with guard parity.

---

## Phase 5: User Story 3 - The app follows the language I write in (Priority: P1)

**Goal**: a clear message language switches the reply and the whole app, at any stage.

**Independent Test**: with an English browser, sign in and send a Spanish message: the reply and every fixed text are Spanish. Send "1" or "ok": the language stays.

- [X] T031 [US3] In `Engine._turn` in `backend/app/workflow/engine.py`, replace the condition `if s.stage in ("start", "closed") or u.intent in (...)` with `if u.language: s.lang = u.language`, so a clear language switches at any stage and an unclear one never does (FR-407).
- [X] T032 [US3] Add tests to `backend/tests/test_language.py`:
  - a session created with `lang="en"`, then a Spanish message, gives a Spanish reply with `done.lang == "es"`;
  - "1" at the choose stage keeps the language;
  - "yes" at the confirm stage of a Spanish conversation keeps Spanish and still closes only with the rules' agreement;
  - a Portuguese "Não fui eu" at the confirm stage of a Spanish conversation files the claim and switches to Portuguese.

  Every existing test passes unchanged.
- [X] T033 [US3] Make the app language the single source for every fixed text, chat included (FR-408 replaces specs/003 FR-201):
  - in `frontend/src/useChat.ts` and `frontend/src/Chat.tsx`, when a `done` event's `lang` differs from the app language, call `setLang(done.lang)` from `useLanguage()`. Don't store it (data-model: App language transitions);
  - the header, sign-in, and specialist texts follow at once;
  - remove the separate `chatLang` state from `frontend/src/App.tsx`.
- [X] T034 [US3] Extend `frontend/e2e/language.spec.ts` with two checks:
  - in an `en-US` browser, sign in and send the Spanish example. The header, the nav, and every chat fixed text are then Spanish, and `<html lang="es">`;
  - an English conversation shows 0 Spanish or Portuguese fixed texts (SC-402).

**Checkpoint**: the app follows the customer.

---

## Phase 6: User Story 5 - Switching language re-shows the whole conversation (Priority: P1)

**Goal**: on a language change, every earlier message is re-shown in the new language. Assistant messages are rebuilt with identical facts; customer messages get a marked translation, with the original kept.

**Independent Test**: hold a Spanish conversation to a filed claim, then write in Portuguese: every earlier message is shown in Portuguese with the same amounts, sources, and case number (SC-405).

- [X] T035 [US5] Add `Claude.translate(text, target_lang) -> str | None` to `backend/app/llm/claude.py`:
  - Claude Haiku 4.5 (`settings.understand_model`);
  - the text passed as data inside `<customer_message>` tags, with the instruction "translate only; add nothing";
  - logged in `usage_log`, and None when `over_budget()`.

  In `backend/app/language/translator.py`, add `translate_customer(session, entry_index, masked_text, target, llm)`:
  - accept the result only if the set of numbers is identical and its length is between 0.5× and 2× the original (research R7);
  - cache it in `Session.translations[(entry_index, target)]`, which is new on `Session` in `engine.py` ("`None` records 'no usable translation', so it is not retried");
  - with no model, return None.
- [X] T036 [US5] Add `conversation_view(session, lang, llm) -> dict` to `backend/app/language/translator.py`, built from `session.transcript.entries`, shaped exactly as in contracts/http-api.md.
  - **Customer turns**:
    - the original when `entry.lang == lang`;
    - else the translation, with `translated: true` and `original: {text, lang}`;
    - else the original with `translation_missing: true`.
  - **Message entries**: the stored text when `entry.lang == lang`, else `render(statements, lang)`, keeping basis and source.
  - **Candidates**: rebuilt from `raw` in `lang`.
  - **Verdict and handoff**: unchanged.
  - **Notices**: rebuilt from their code.
  - **Also returned**: `stage` and `suggestions` (`QUICK_REPLIES[stage][lang]`).
  - Never `step` events, `key`, `params`, or `raw`.
- [X] T037 [US5] In `backend/app/api/main.py`, add:
  - `POST /api/session/language` (body `{session_id, lang}`): sets `s.lang` and returns `conversation_view`; 401 for an unknown or expired session; 422 for a `lang` outside en, es, pt;
  - `GET /api/session/conversation?session_id=…`: the view in `s.lang`.

  Neither calls a tool or reads the store.
- [X] T038 [US5] Add tests to `backend/tests/test_language.py`:
  - a Spanish claim path, then views in pt, en, and es: identical `basis`, `source`, verdicts, and case ids in every language, and the es view's assistant texts equal the originals (FR-420, FR-423);
  - the store's query count is unchanged across the views (no tool call);
  - in rules mode, customer turns have `translation_missing: true`;
  - a fake model whose translation drops a number gives `translation_missing`, and a second view makes no new call (cache);
  - 401 and 422;
  - a 20-message conversation is re-shown in under 2 s in rules mode (SC-407).
- [X] T039 [US5] In `frontend/src/api.ts`, add `setSessionLanguage(sessionId, lang)` and `getConversation(sessionId)`. In `frontend/src/useChat.ts`:
  - add `replaceTurns(view)`, which maps the view to `Turn[]`, keeping `at` from the server's ISO time;
  - when `done.lang` differs from the app language (T033), fetch `getConversation` once and replace the turns in a single update;
  - keep the newest message in view;
  - announce "Conversation shown in {language}" once, through the existing status region, in the new language (contracts/ui.md).
- [X] T040 [US5] In `TurnView` in `frontend/src/Chat.tsx`, for a translated customer turn:
  - show the translation with a mark (`TEXT[lang].translated`);
  - add a toggle button (`showOriginal` / `hideOriginal`), keyboard-operable, with a spoken name, that reveals the original in an element with `lang={original.lang}`;
  - for `translation_missing`, show the original with `TEXT[lang].noTranslation`.

  Add these keys to all three sets in `frontend/src/i18n.ts`, and the styles in `frontend/src/index.css`, meeting the specs/003 contrast and tap-target rules.
- [X] T041 [US5] Add `frontend/e2e/reshow.spec.ts` (rules mode):
  - run the Spanish claim path, then send a Portuguese message;
  - every earlier assistant message is shown in Portuguese, with the same source references and case number as before;
  - customer messages show the original with the "no translation" note;
  - axe passes on the re-shown chat, and phone width has no sideways scroll.

**Checkpoint**: increment 2 is complete. The demo path (Spanish, then Portuguese) works.

---

## Phase 7: User Story 4 - I can pick the language myself (Priority: P2)

**Goal**: an ES / PT / EN switcher on every screen, remembered on the device, that also re-shows an open conversation.

**Independent Test**: on each screen, pick each language in turn. Every fixed text switches at once, the choice survives a reload, and an open conversation continues.

- [X] T042 [P] [US4] Create `frontend/src/components/LanguageSwitcher.tsx` per contracts/ui.md:
  - a labelled group of three buttons, "EN", "ES", "PT";
  - spoken names "English", "Español", "Português", each with its own `lang` attribute;
  - `aria-pressed` on the current option;
  - each option at least 44 × 44 px at phone width.
- [X] T043 [US4] Place the switcher in the header in `frontend/src/App.tsx`, and adjust `.header-inner` in `frontend/src/index.css` so the header fits at 360 and 375 px with no sideways scroll. On pick:
  - `setLang(l)` and `storeLanguage(l)`;
  - during a session, call `setSessionLanguage` and `replaceTurns` (T039);
  - keep the composer's unsent text, and keep focus on the switcher.
- [X] T044 [US4] Add `frontend/e2e/switcher.spec.ts`:
  - switching on sign-in, in the chat, and in the specialist view changes every fixed text;
  - the choice persists across a reload;
  - during a conversation, a switch re-shows earlier messages;
  - spoken names and the pressed state are correct;
  - tap targets are at least 44 px, and there is no sideways scroll at 375 px, in both themes.

**Checkpoint**: increment 1 is complete (US1 and US4). With Phase 6, the demo can switch by tapping PT.

---

## Phase 8: Records - the PDF and the specialist view (FR-424 to FR-427, extending US5)

**Goal**: the record follows the re-show rules. PDFs issued before this feature keep verifying.

- [X] T045 [US5] Create `backend/app/transcript/render_v1.py`: a frozen copy of the current `render.py` (`_Doc`, `render`, `file_name`), with its own frozen copy of the current Spanish and Portuguese `LABELS`. Point the T001 test at `render_v1.render`. It must give the pinned hash.
- [X] T046 [US5] Make `snapshot(lang, translations)` in `backend/app/transcript/record.py` produce schema `2`, with renderer `fpdf2-2.8.9/r2`, in the session's language (data-model: Transcript snapshot, schema 2):
  - customer entries carry `original` and `original_lang`, and, when `original_lang != lang`, `translation` or `translation_missing: true`;
  - message entries carry text and statements in `lang`, without `key` or `params`.
- [X] T047 [US5] In `backend/app/transcript/labels.py`, add the `en` labels: title "Copy of the conversation", authors "You" and "Assistant", bases "verified", "estimate", and "rule", the verdicts, handoff, notice (no promise: the test runs it through the same check), page, check code, and `file_prefix` "conversation". Add `translated` and `no_translation` to all three languages.

  In `backend/app/transcript/render.py`, print a customer translation beneath the original in grey, marked as a translation.
- [X] T048 [US5] In `backend/app/transcript/verify.py`, choose the renderer by `(schema, renderer)`:
  - `(1, "fpdf2-2.8.9/r1")` → `render_v1.render`;
  - `(2, "fpdf2-2.8.9/r2")` → `render.render`;
  - anything else → `unknown_version`.
- [X] T049 [US5] In `transcript_pdf` in `backend/app/api/main.py`, build the snapshot in `s.lang`. First fill the missing customer translations through `translate_customer`, within the spend cap. Use the language-specific file name.
- [X] T050 [US5] Add tests to `backend/tests/test_transcript.py`:
  - a schema-1 r1 PDF (the T001 snapshot) verifies as a match through `verify()`;
  - a PDF in each of en, es, and pt verifies as a match;
  - one edited byte gives altered;
  - changing `lang` or a translation in the embedded JSON gives altered;
  - the English notice passes the no-promise check.

  Update `backend/app/eval/transcript_check.py` for schema 2.
- [X] T051 [US5] In `backend/app/api/main.py`, make `GET /api/handoffs` accept an optional `lang`. For cases whose `language` differs, add `translations: {request?, customer_statement?}` from `translate_customer` rules, cached per `(case_id, field, lang)` in memory and never written to the queue file. In `frontend/src/AgentQueue.tsx`:
  - send the app language;
  - show each translation beneath the customer's words, marked;
  - leave facts and IDs untranslated.

  Add a test with a fake model (translation present) and rules mode (absent).

**Checkpoint**: the record follows the re-show rules, and PDFs already issued keep verifying.

---

## Phase 9: Polish and evaluation (increment 3)

- [X] T052 Add the category `language_switch` to `CATEGORIES` and to `generate()` in `backend/app/eval/cases.py`, with 6 cases per set:
  - describe a charge in one language, answer "was it you?" in another, then give a statement;
  - expected: the same transaction, a handoff, and every earlier assistant message re-rendered with the same sources;
  - **parity**: 6 transactions, each run through describe, claim, and statement in all three languages.

  In `backend/app/eval/run.py`, grade switch cases with `conversation_view` (sources identical in every language), and parity cases by comparing the tools called, the transaction, the decision, and the handoff case type (SC-404, SC-405). Add both to `report.py`.
- [X] T053 Run `make eval` and regenerate `docs/evaluation.md`. Check:
  - Spanish and Portuguese are no worse than before T029;
  - English has 0 unsafe outcomes, within 5 points of Spanish;
  - `language_switch` is at 100%;
  - parity is at 100%.
- [ ] T054 [P] Update the documentation:
  - **`README.md`**: three languages, the switcher, re-showing, English team-generated and labelled.
  - **`docs/limitations.md`**:
    - customer words are not translated in rules mode or past the spend cap;
    - English and Portuguese evaluation cases are team-generated;
    - numeric dates are read day first;
    - a model-reworded reply re-shows in fixed wording in other languages;
    - the specialist's translations are not stored.
  - **`docs/model-card.md`**: the new Haiku use, translating customer words, with its checks.
  - **`docs/build-plan.md`**: decisions as built.
  - **`CLAUDE.md`**: the 004 status line and the English PDF name pattern.
- [ ] T055 Run all the gates: `make test`, the frontend build, `npm run check:ui` against `SESSIONS_PER_IP_HOUR=1000 LLM_DISABLED=1 make dev`, `make eval`, and the secret scan.
- [ ] T056 Ask the owner before `make eval-llm` (about $3 with the larger sets). If approved, run it and confirm SC-403 to SC-406 in Claude mode.
- [ ] T057 Ask the owner before `make deploy-azure`. After deploying:
  - wait for 100% traffic on the new revision, and check `/api/health`;
  - walk through quickstart §3 on the live URL at 375 px (EN browser, Spanish claim, switch to PT, then to EN, download the PDF and verify it);
  - confirm a PDF issued before this feature still verifies as a match.

---

## Dependencies and execution order

- **Setup (T001-T004)**: first. T001 must run before any change to `backend/app/transcript/`.
- **Foundational (T005-T011)**: blocks US2, US3, and US5. It does not block US1 (Phase 3) or US4's sign-in part, which are frontend-only.
- **US1 (Phase 3)**: after Setup. Can run in parallel with Phase 2.
- **US2 (Phase 4)**: after Phase 2, and after T014 and T015 (the frontend must accept `en`).
- **US3 (Phase 5)**: after US2 (it needs language detection in all three languages).
- **US5 (Phase 6)**: after Phase 2 and US3 (re-show is triggered by a language change). It needs US2 only for English views; Spanish and Portuguese views work without it.
- **US4 (Phase 7)**: T042 can start after US1. T043's in-conversation re-show needs T039 (US5).
- **Records (Phase 8)**: after US5. T045 must precede T046-T048.
- **Polish (Phase 9)**: after Phases 4-8.

```text
Setup ──► Foundational ──► US2 ──► US3 ──► US5 ──► Records ──► Polish
   └────► US1 ──────────────────────────────► US4 ─┘
```

## Parallel opportunities

- **Setup**: T002, T003, and T004 together.
- **Phase 2 and Phase 3**: run side by side (backend boundaries alongside frontend detection and texts). In Phase 3, T012, T013, T018, and T020 are in different files.
- **US2**: T022 (`messages.py`) and T023 (`rules.py`) together, then T024 and T025.
- **US4**: T042 can be built alongside US5's backend tasks.
- **Polish**: T054 alongside T052 and T053.

## Implementation strategy

1. **MVP (increment 1)**: Setup, then Phase 3 (US1), then T042-T044 (the switcher before sign-in and its tests). Validate the detection, switcher, axe, and phone checks, then ask about a redeploy. Frontend only, low risk.
2. **Increment 2 (the demo)**: Phase 2, US2, US3, US5, then T043's in-conversation part. Validate with quickstart §3 in rules mode, then ask about a redeploy. This is what the video needs: Spanish, then a switch to Portuguese.
3. **Increment 3 (records and evidence)**: Phase 8, then Phase 9, then ask about `make eval-llm` and the final redeploy.

**If time runs short**: increments 1 and 2 cover every P1 story. The specialist's translations (T051) and the switch and parity evaluation (T052) are the first to defer. Write each deferral in `docs/limitations.md`, and don't claim a metric that wasn't run.
