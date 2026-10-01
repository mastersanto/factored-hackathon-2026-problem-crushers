# Tasks: Suggestions in the language I'm writing in

**Input**: design documents in `specs/005-suggestions-language/`: spec.md, plan.md, research.md (R1-R6), data-model.md, contracts/http-api.md, contracts/ui.md, quickstart.md

**Tests**: included.
- SC-502 (every example understood like its Spanish counterpart) is measured by a backend test (research R5).
- SC-501 and SC-503 are measured by UI checks ([contracts/ui.md](contracts/ui.md)).

**Builds on**: specs/004 (the app language, the switcher, re-showing), built and not yet deployed.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: can run in parallel (different files, no dependency on an incomplete task).
- **[Story]**: US1, US2, from spec.md.
- Paths are relative to the repository root.

## Quality gates (after every task that changes code)

- `make test`: every existing test passes unchanged.
- `cd frontend && npm run build`.
- `cd frontend && npm run check:ui`, against `SESSIONS_PER_IP_HOUR=1000 LLM_DISABLED=1 make dev`.
- The secret scan on the staged diff (zero matches).
- `make eval` only if a task touches `backend/app/workflow/`, `language/`, `llm/`, or `policy/`. None should.

**No Setup or Foundational phase**: the feature adds one API field and changes one screen. Nothing blocks both stories.

---

## Phase 1: User Story 1 - Example messages in my language (Priority: P1) 🎯 MVP

**Goal**: the example messages are built per language on the server and shown only in the app's current language.

**Independent Test**: in `en-US`, `es-MX`, and `pt-BR` browsers, sign in. Every example is in that language, and tapping each one gets a reply in the same language.

- [X] T001 [US1] Add per-language example messages to `GET /api/demo/customers` in `backend/app/api/main.py`, per contracts/http-api.md:
  - **Templates**: a module-level `EXAMPLES` dict next to `SCENARIOS`, with the five templates of research R2 in `en`, `es`, and `pt` (keep the Spanish wording exactly as in today's `suggestionsFor` in `frontend/src/App.tsx`).
  - **Builder**: `_examples(hint) -> {"en": [...], "es": [...], "pt": [...]}`. Order: charge (with merchant, or without), then contact, then scam, then the other-customer request.
  - **Formats** (research R3):
    - amounts via `messages.money(amount, currency, lang)` with the currency code removed, so `1,234.56` in en and `1.234,56` in es and pt;
    - contact dates as `DD/MM/YYYY` in es and pt, and `June 18, 2026` in en (`messages.day(dt, "en")`);
    - channel names as recorded (`SMS`, `WhatsApp`).
  - **Validation**, quoted from data-model.md:
    - "the three lists have the same length";
    - "a charge example only with an amount; a contact example only with a channel and date";
    - "the scam and other-customer examples are always present".
  - **Output**: add `"examples": _examples(hint)` to every item, for both the charge customers and the bank-message customer.
- [X] T002 [US1] In `backend/tests/test_language.py`, add `test_demo_examples_are_well_formed`:
  - every item has `examples` with keys `en`, `es`, and `pt`;
  - the lists are of equal length;
  - each list ends with the scam and the other-customer examples;
  - an item without `hint.amount` has no charge example;
  - an item without `hint.channel` has no contact example.
- [X] T003 [US1] In `backend/tests/test_language.py`, add `test_every_example_is_understood_like_spanish` (research R5). For each demo customer and each example position, send the example in each language in a fresh session created with `lang` set to that language (rules mode), then require:
  - `done.lang` equals the example's language, so tapping never switches;
  - the same outcome in all three languages:
    - **charge**: the same set of asserted `transaction:` sources, or the same candidate options;
    - **contact**: the same verdict;
    - **scam**: `scam_asks_secret`;
    - **other customer**: the `refuse_unauthorized` action and the `other_customer_reference` flag.

  If an example is not understood, fix the example's wording, not the rules: FR-508 forbids changing understanding.
- [X] T004 [P] [US1] In `frontend/src/api.ts`, add `examples: Record<Lang, string[]>` to `DemoCustomer`. In `frontend/e2e/helpers.ts`, add the same field to the helpers' `DemoCustomer`.
- [X] T005 [US1] Show the examples in the current language:
  - in `frontend/src/App.tsx`, remove `suggestionsFor` and pass `session.customer.examples` to `Chat`, renaming the prop to `examples: Record<Lang, string[]>`;
  - in `frontend/src/Chat.tsx`, render `examples[lang]` in the examples group, and give each example button `lang={lang}` (FR-501, FR-505, FR-507).
- [X] T006 [US1] Create `frontend/e2e/suggestions.spec.ts` with the US1 rows of contracts/ui.md:
  - **Examples per language**: in `en-US`, `es-MX`, and `pt-BR` (via `test.use({ locale })` per `describe`), every chip in the examples group has that `lang`, and none of the other two languages' example texts (taken from the API's `examples`) is on screen.
  - **The switcher before the first message**: picking each language replaces every example at once.
  - **Tapping keeps the language**: in `en-US`, tapping the first example gets a reply with `<html lang="en">`, and the reply's message contains "The charge is for".
  - **Phone width**: 375 px, no sideways scroll, and every chip is at least 44 px tall, in all three languages.

**Checkpoint**: US1 complete. Example messages are always in the app's language.

---

## Phase 2: User Story 2 - Suggestions follow me when the language changes (Priority: P1)

**Goal**: quick replies and example messages change at once with the language, whether by writing or by the switcher.

**Independent Test**: in a Spanish conversation at "was it you?", pick EN. The quick replies read "Yes, it was me" / "It wasn't me". After the case closes, write in Portuguese: the examples are Portuguese.

- [X] T007 [US2] In `frontend/src/useChat.ts`, keep the language the quick replies came in (`repliesLang`):
  - set it from `done.lang` on each reply and from `view.lang` on each re-show;
  - return it.

  In `frontend/src/Chat.tsx`, give each quick-reply button `lang={repliesLang}` (FR-504, FR-507).
- [X] T008 [US2] Add the US2 checks to `frontend/e2e/suggestions.spec.ts`:
  - **The switcher at a question**: run the Spanish charge example, then at the confirm question pick EN. The quick replies are exactly `["Yes, it was me", "It wasn't me"]`, with `lang="en"`. Tapping "It wasn't me" files the claim (the statement question appears in English).
  - **Writing in another language after a case closes**: complete a claim in Spanish so the examples return, then send a Portuguese message. The examples become `examples.pt`.

**Checkpoint**: US2 complete. No suggestion is ever shown in a language other than the app's.

---

## Phase 3: Polish

- [X] T009 [P] Update the documentation:
  - `CLAUDE.md`: add `specs/005-suggestions-language/` to the features list, with its status;
  - `README.md`: add the 005 row to the documents table;
  - `docs/build-plan.md`: record the decision that the demo's mixed-language examples were dropped in favour of the switcher, and that examples are built on the server so they can be tested against the workflow.
- [X] T010 Run all the gates: `make test`, the frontend build and lint, `npm run check:ui`, and the secret scan. Confirm no file under `backend/app/workflow/`, `language/`, `llm/`, or `policy/` changed (so `make eval` is not needed and its results are unchanged, FR-508).
- [X] T011 Ask the owner before redeploying. 004 and 005 can go live together (`make deploy-azure`). After deploying, check the examples in each language on the live URL at 375 px.

---

## Dependencies and execution order

- **T001** comes first: the examples are built on the server.
- **T002 and T003** depend on T001.
- **T004** can run alongside T001-T003.
- **T005** depends on T001 and T004.
- **T006** depends on T005.
- **US2 (T007-T008)** depends on T005, since it shares `Chat.tsx`.
- **Polish (T009-T011)** comes after both stories.

```text
T001 ──► T002, T003
T004 ──┐
T001 ──┴► T005 ──► T006 ──► T007 ──► T008 ──► T009-T011
```

## Parallel opportunities

- T004 (types) alongside T001-T003 (backend).
- T009 (documentation) alongside T010's long UI run.

## Implementation strategy

1. **MVP**: T001-T006 (US1). The examples are in the app's language, which is the whole visible problem.
2. **Then**: T007-T008 (US2). Quick replies already follow the language (specs/004), so this phase adds the `lang` marking and the checks.
3. **Finish**: T009-T011, then a single redeploy covering 004 and 005, with the owner's approval.
