# Tasks: Answers that react to what I ask

**Input**: spec.md, plan.md in `specs/007-reactive-replies/`. Tests included (SC-701, SC-702 by backend tests; SC-703 by `make eval`).

Gates after code changes: `make test`, `make eval` (no metric drops), `npm run build` and lint, `npm run check:ui` (rules mode, high session limit, no stale dev server), and the secret scan.

## Phase 1: User Story 1 - My last movements (P1) 🎯 MVP

- [X] T001 [US1] In `backend/tests/test_reactive.py`, write the tests first (rules mode, en/es/pt):
  - each listed phrasing gives a candidates event with 5 items, newest first, equal to the session customer's 5 most recent charge-type movements;
  - "últimos 8" / "last 8" / "últimas 8" gives 8, and 12 gives 9;
  - choosing "2" explains the second card (charge/3);
  - progress is charge/2 after the list;
  - "my last movements at {merchant}" is a charge search;
  - another customer's movements are refused.
- [X] T002 [US1] In `backend/app/tools/banking.py`, add `recent_transactions(store, customer_id, limit=5)`: the session customer's most recent charge-type movements of the lookback window, newest first, `limit` clamped to 1-9.
- [X] T003 [US1] In `backend/app/workflow/understanding.py`:
  - add `count: int | None` to `Understanding`;
  - add `RECENT` (en/es/pt phrasings) and `RECENT_COUNT_RE` (a number right after "últimos/últimas/last/recent", read as the count and kept out of the amount);
  - give intent `list_recent` when RECENT matches and there's no amount, merchant, or date, checked before CLAIM and charge words.
- [X] T004 [US1] In `backend/app/workflow/engine.py`, add `_list_recent`:
  - the tool step;
  - `_progress(charge, 2)`;
  - stage `choose` with the cards (as in `_find`);
  - `recent_list` with `n`, `asked`, and `cap` params, or `recent_none`.

  Then route `list_recent` in `_turn` at any stage except `statement`, the same as a search. Add the templates in `backend/app/workflow/messages.py`.
- [X] T005 [P] [US1] In `backend/app/llm/claude.py`, add `list_recent` (with `count`), `thanks`, and `help` to the understanding schema and prompt.
- [X] T006 [P] [US1] In `backend/app/api/main.py`, add `EXAMPLES["recent"]` in en/es/pt and put it in `_examples` before the scam example (FR-707).

## Phase 2: User Story 2 - Courtesy and help (P1)

- [X] T007 [US2] In `backend/tests/test_reactive.py`, add the tests: each greeting, thanks, and help phrasing, in en/es/pt, with and without a pending question; no out-of-scope action. Update the specs/006 re-ask test that expects `need_answer` for a greeting.
- [X] T008 [US2] In `understanding.py`:
  - add `THANKS` and `HELP` and more GREETING phrasings ("boa tarde", "boa noite", "good evening", "how are you", "cómo está", "tudo bem");
  - set the intents after the charge checks and before out of scope.
- [X] T009 [US2] In `engine.py`:
  - `_reask(s, question, lead=...)`;
  - route greeting, thanks, and help: at choose, confirm, or contact_shared, the courtesy lead plus the question; otherwise the full reply (`greeting`, `thanks`, `help`).

  `contact_shared` keeps its order (a clear yes/no first). Courtesy is treated as unclear there and re-asked with its lead.

## Phase 3: Polish

- [X] T010 [P] Add `frontend/e2e/reactive.spec.ts`: ask for the last movements (5 cards) and pick one; "gracias" gets "De nada". Also adjust any 005 check that counts example chips.
- [X] T011 Update the docs: `CLAUDE.md` (feature list), `README.md` (documents table), `docs/build-plan.md` (decision), and the evaluation report's change list if the evaluation finds something.
- [X] T012 Run every gate and commit to main. Redeploy only with the owner's approval.
