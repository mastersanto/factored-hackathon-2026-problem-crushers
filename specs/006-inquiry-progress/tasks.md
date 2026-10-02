# Tasks: Replies and progress that follow my inquiry

**Input**: design documents in `specs/006-inquiry-progress/`: spec.md, plan.md, research.md (R1-R6), data-model.md, contracts/http-api.md, contracts/ui.md, quickstart.md

**Tests**: included.
- The spec's success criteria SC-601 to SC-605 are measured by backend tests and `make eval`.
- SC-601, SC-602, and SC-606 are also measured by UI checks ([contracts/ui.md](contracts/ui.md)).
- The constitution requires a test that fails without each new safety behaviour (the contact re-ask, R5).

**Builds on**: specs/004 and 005 (three languages, recipes, re-showing), deployed in revision 6.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: can run in parallel (different files, no dependency on an incomplete task).
- **[Story]**: US1 (progress), US2 (replies), from spec.md.
- Paths are relative to the repository root.

## Quality gates (after every task that changes code)

- `make test`: every existing test passes, unchanged unless the task says otherwise.
- `make eval` after any task touching `backend/app/workflow/` or `language/`. No metric may drop below:
  - English 100/100/93.3;
  - Spanish 100/100/85.6;
  - Portuguese 100/100/84.4;
  - 0 unsafe, switch and parity 100%.
- `cd frontend && npm run build`.
- `cd frontend && npm run check:ui`, against `SESSIONS_PER_IP_HOUR=1000 LLM_DISABLED=1 make dev`.
- The secret scan on the staged diff (zero matches).

---

## Phase 1: Foundational (blocks both stories)

**Purpose**: the inquiry record, and its way to the browser.

- [X] T001 Add the inquiry record to `backend/app/workflow/engine.py`, per data-model.md:
  - **The class**: a dataclass `Inquiry` with `path`, `stage`, `done`, `outcome`, and `case`. Quote the rules in a docstring:
    - `path` is `"charge"` | `"contact"`;
    - "1-5 for charge and 1-4 for contact. Never above the path's total";
    - "True only at the path's last stage";
    - outcome is `"recognized"` | `"specialist"` | `"urgent"` | `"genuine"` | `"no_record"` | `"warned"` | null, "Set exactly when `done` is true";
    - case: "The case number when `outcome` is `specialist` or `urgent`; null otherwise".
  - **Session**: `inquiry: Inquiry | None = None`.
  - **Constant**: `TOTALS = {"charge": 5, "contact": 4}`.
  - **Helpers on `Engine`**:
    - `_progress(s, path, stage)`: starts a new inquiry when `s.inquiry` is None or done, or when `path` differs; otherwise moves the stage;
    - `_finish(s, path, outcome, case=None)`: sets the last stage, `done=True`, the outcome, and the case;
    - `progress_view(s) -> dict | None`: returns `{path, stage, total, done, outcome, case}`.

  Both helpers assert the rules above.
- [X] T002 Carry `progress` out, per contracts/http-api.md:
  - in `Engine.handle`, add `"progress": progress_view(s)` to the `done` event;
  - in `backend/app/language/translator.py` `conversation_view`, add the top-level `"progress"` (the same function). Re-showed per-turn `done` markers get `"progress": None`;
  - check that `public_event` in `engine.py` and the transcript recorder (`backend/app/transcript/record.py`) don't record `done` content into the PDF entries. If they do, exclude `progress` there.
- [X] T003 [P] In `frontend/src/api.ts`, add `export interface Progress { path: 'charge' | 'contact'; stage: number; total: number; done: boolean; outcome: 'recognized' | 'specialist' | 'urgent' | 'genuine' | 'no_record' | 'warned' | null; case: string | null }`. Then add `progress?: Progress | null` to the `done` event type, and `progress: Progress | null` to `ConversationView`.

**Checkpoint**: the API streams `progress` (null everywhere until US1 sets it). Every existing test passes.

---

## Phase 2: User Story 1 - The step shows where my inquiry stands (Priority: P1) 🎯 MVP

**Goal**: the panel shows the inquiry's path and stage, moving only when the inquiry changes.

**Independent Test**: follow the claim path and the contact path. After each reply the panel matches data-model.md's transition table. A greeting mid-inquiry doesn't move it.

- [X] T004 [US1] In `backend/tests/test_progress.py` (new), write the transition tests first, using `conftest.py`'s rules mode and the helpers already in `backend/tests/test_language.py` / `test_workflow.py` for sessions and events. For each language in `("en", "es", "pt")`:
  - **Charge path**:
    - a dispute without details gives `charge/1`;
    - a search with no match or too many gives `charge/2`;
    - candidates give `charge/2`, and choosing one gives `charge/3`;
    - an explained charge gives `charge/3`;
    - "It wasn't me" gives `charge/4`;
    - the statement gives `charge/5`, done, `specialist`, with the case equal to the handoff event's case id.
  - **Recognized**: "Yes, it was me" gives done and `recognized`, with no case.
  - **Compliance hold**: done and `specialist`, with the case. The progress has no other field set.
  - **Contact**:
    - a genuine contact gives `contact/4`, done, `genuine`;
    - no record gives done, `no_record`;
    - a scam that asked for a secret gives `contact/3`;
    - then "yes" gives done, `urgent`, with the case;
    - then "no" (in a fresh session) gives done, `warned`.
  - **No move** (SC-602): at `charge/3`, a greeting, an out-of-scope message, an other-customer request, and an injection attempt each leave `progress` equal to before.
  - **New inquiry**: after a done claim, a new charge search restarts at `charge/2` or `charge/3`. After a done charge, a contact check gives `contact/…`.
  - **Re-show parity**: `conversation_view(s, other_lang)["progress"]` equals the last `done.progress`.
  - **Technical fallback**: make a tool raise, via monkeypatch. The result is done and `specialist`, with the case.
- [X] T005 [US1] Set the inquiry in `backend/app/workflow/engine.py` at each branch of data-model.md's transition tables, so T004 passes:
  - **`_turn`**:
    - `need_details`: `charge/1`, but only when there's no inquiry or it's done (research R3); otherwise leave it;
    - `explain_candidate` goes through `_explain`;
    - `close_recognized`: `_finish(..., "recognized")`;
    - `collect_statement`: `charge/4`.
  - **`_find`**: `charge/2` before the no-match, too-many, and choose replies.
  - **`_explain`**: `charge/3`.
  - **`_compliance_hold`** and **`_file_claim`**: `_finish(..., "specialist", case)`.
  - **`_check_contact`**:
    - bank contact: `_finish(contact, "genuine")`;
    - no record: `_finish(contact, "no_record")`;
    - scam, shared None: `contact/3`;
    - scam, shared False: `_finish(contact, "warned")`.
  - **`_escalate_contact`**: `_finish(contact, "urgent", case)`.
  - **`_contact_followup`**, "no": `_finish(contact, "warned")`.
  - **Technical fallback** in `handle`: `_finish(s.inquiry.path if s.inquiry else "charge", "specialist", case)`.
  - **Unchanged**: greeting, out of scope, and refusals don't touch the inquiry.

  Run `make eval`: the numbers must be unchanged, since only state is added.
- [X] T006 [P] [US1] In `frontend/src/i18n.ts`, replace `steps.names`, `steps.lines`, and `steps.progress` in all three `TextSet`s (the type at the top, plus en, es, and pt):
  - **The lists**: `charge: { names: string[5]; lines: string[5] }` and `contact: { names: string[4]; lines: string[4] }`, with research R2's names. Each line is one sentence, for example "Write what you see on your statement: amount, merchant, or day."
  - **`outcomes`**: `Record<'recognized' | 'specialist' | 'urgent' | 'genuine' | 'no_record' | 'warned', (c: string | null) => string>`. For example:
    - "Closed · you recognized the charge";
    - "Sent to a specialist · case {case}";
    - "Urgent: sent to a specialist · case {case}";
    - "The contact was the bank's";
    - "No record of that contact from the bank";
    - "Closed · not the bank; keep your codes private".
  - **`progress`**: `progress: (n: number, total: number, name: string) => string`.
  - **Unchanged**: `title`, `subtitle`, `done`, `now`, `notStarted`, and `technical`.

  Spanish uses "usted", the same as the rest of the app's Spanish. Portuguese uses "você".
- [X] T007 [US1] Show progress in the browser:
  - **`frontend/src/useChat.ts`**: keep `progress` state, setting it from `done.progress` on each reply and from `view.progress` on each re-show. Reset it to null in `reset`. Leave it unchanged on `error` events. Return it. Remove `stepProgress` and `STEP_ORDER`.
  - **`frontend/src/components/StepsPanel.tsx`**: take `progress: Progress | null`, and render per contracts/ui.md:
    - the path's list (charge when null);
    - the states done, current (`aria-current="step"`), and todo;
    - when `done`, every stage done and the outcome line under the list.

    The drawer summary is `notStarted`, `progress(n, total, name)`, or the outcome line. The technical trace is unchanged.
  - **`frontend/src/Chat.tsx`**: pass `progress` from `useChat` to both `StepsPanel`s.
- [X] T008 [US1] Create `frontend/e2e/progress.spec.ts` with the contracts/ui.md rows for US1:
  - Not started;
  - Claim path (the case number matches the handoff card's);
  - Recognized;
  - Contact path;
  - Switch (mid-claim, pick PT: same stage number, Portuguese names);
  - New inquiry;
  - Phone (375 px drawer summary, no sideways scroll);
  - axe in each state.

  Use the helpers in `frontend/e2e/helpers.ts` (`signIn`, `send`, `reply`, `claimPath`, `noSideScroll`). If a fixed-text leak check (`fixedTexts`, `otherThan`) flags the new panel texts, extend those helpers rather than skipping the check.

**Checkpoint**: US1 complete. The panel reflects the inquiry. Replies are unchanged so far.

---

## Phase 3: User Story 2 - Replies answer what I wrote (Priority: P1)

**Goal**: search replies name what was searched for, and pending questions are asked again instead of being dropped.

**Independent Test**: in rules mode, send each FR-605 message at its stage. Each reply names the given details, asks only for missing ones, and at a pending question asks it again.

- [X] T009 [US2] Add the wordings to `backend/app/workflow/messages.py`, in en, es, and pt (Spanish "usted", the same as the existing templates):
  - **`none_found_with`**: "I didn't find a charge {searched} in the last 90 days. Can you tell me {missing}?"
  - **`choose_with`**: "I found several charges {searched} that could be it. Which one is it? Reply with the number."
  - **`too_many_with`**: "More charges {searched} match than I can show. Can you tell me {missing} to narrow it down?"
  - **`need_answer`**: "To continue I need your answer to this question."
  - **Phrase builders** (research R4):
    - `searched_phrase(searched: dict, lang)`: "of {n} at {merchant} on {day}", only the parts present, in that order. The amount uses `money`'s number format without the currency, the same as the 005 examples in `backend/app/api/main.py`, so reuse or move that helper. The day uses `day(dt, lang)`.
    - `missing_phrase(missing: list, lang)`: "the merchant or the day". An empty list gives "the exact amount, the merchant, or the day".
- [X] T010 [US2] In `backend/app/language/translator.py` `render_text`, format the `searched` param with `M.searched_phrase` (date ISO string → datetime) and the `missing` param with `M.missing_phrase`, so recipes re-word in any language (specs/004).
- [X] T011 [US2] In `backend/tests/test_progress.py`, add the reply tests first. Use English, Spanish, and Portuguese phrasings; each must fail before T012/T013:
  - **Echo** (SC-603):
    - a merchant-only search with several matches: the reply contains the merchant;
    - an amount-only search with no match: the reply contains the amount in the language's format, and asks for the merchant and the day, not the amount;
    - too many: names what was given;
    - no details: unchanged `need_details`.
  - **Recipes**: the message's statements carry key `none_found_with` (in the session transcript recipes), and `conversation_view` in another language re-words the echo with that language's separators.
  - **Nothing invented** (FR-606): the echoed merchant is one from the engine's merchant list, and no currency code appears in the echo.
  - **Re-ask** (SC-604):
    - at `confirm`, a greeting and "what time is it?" get action `reask_pending`, with the reply's last statement `ask_confirm` and quick replies still `QUICK_REPLIES["confirm"]`;
    - the same at `choose`, with the last statement `choose`;
    - at `contact_shared`, "hmm" gets `reask_pending` with `ask_shared`, the stage stays `contact_shared`, and no handoff is made.
  - **Safety regression** (constitution III; it must fail against today's engine):
    - at `contact_shared`, "hmm, maybe" no longer gives the freeze hint and closes;
    - "les di el código" escalates as urgent (via `_yes_no_shared`).
  - **New inquiry at a pending question**: at `confirm`, "actually it's a different charge of {amount} at {merchant}" searches again (spec US2 scenario 6).
  - **Refusals unchanged**: at `confirm`, an other-customer request still gets `refuse_unauthorized`.
- [X] T012 [US2] Echo the search in `backend/app/workflow/engine.py` `_find`:
  - build `searched` from `u.amount`, `u.merchant`, and `u.date` (only the non-None ones, the date as an ISO string) and `missing` in the order amount, merchant, date;
  - use `none_found_with`, `too_many_with` (both with `missing`), and `choose_with`, keeping each one's current source (`tool:find_transactions`, `flow`).

  Keep `need_details` unchanged. Keep the plain `choose` key for the invalid-option reply, which is a re-ask.
- [X] T013 [US2] Re-ask pending questions in `backend/app/workflow/engine.py` (research R5):
  - **At `confirm` and `choose`**: in `_turn`, before the generic greeting and out-of-scope branches, when `s.stage` is one of them and the intent is `greeting` or `out_of_scope`, yield `self._step("decide", action="reask_pending", question=s.stage)`, then `_say` `[need_answer, ask_confirm | choose]` with `verify=False`. Leave the stage and the inquiry unchanged.
  - **At `contact_shared`**: move the check so a `check_contact` intent, or a `dispute_charge` with an amount, merchant, or date, falls through to the normal branches. That starts a new inquiry and clears `pending_contact`.
  - **`_contact_followup`**: `shared = _yes_no(text)`, and if None, `_yes_no_shared(text)`. True escalates (as today). False gives the freeze hint and `_finish(contact, "warned")`. None gives `reask_pending` with `[need_answer, ask_shared]`, keeping the stage.
  - **Afterwards**: run `make eval`. If a number drops, look at what changed in the failing cases:
    - fix the engine generally (constitution V);
    - if the grader in `backend/app/eval/run.py` doesn't recognise `reask_pending` where it should, update the grader and say why in the report's "What the evaluation changed".
- [X] T014 [US2] Add the US2 rows to `frontend/e2e/progress.spec.ts`:
  - **No move**: at "was it you?", send "hola". The reply ends with the question, the quick replies stay, and the panel doesn't move.
  - **Scam, unclear answer**: stage 3 of 4 stays current, and the question is asked again.
  - **Echo**: in a Spanish session, send "no reconozco un cargo de 7". The last reply contains "7" and doesn't ask for the "monto".

**Checkpoint**: US2 complete. Replies follow the message, and the panel follows the inquiry.

---

## Phase 4: Polish

- [X] T015 [P] Update the documentation:
  - `CLAUDE.md`: add `specs/006-inquiry-progress/` to the feature list, with its status;
  - `README.md`: the 006 row in the documents table;
  - `docs/build-plan.md`: record the decisions:
    - the panel shows customer stages per path (option A) set by the engine, not the internal steps;
    - an unclear "did you share?" is asked again rather than read as "no";
  - `docs/limitations.md`: the contact path's stage 2 has no state of its own, since the check resolves in one reply.
- [X] T016 Run every gate: `make test`, `make eval` (compare `docs/evaluation.md` with the last committed numbers), the frontend build and lint, `npm run check:ui`, and the secret scan. If `docs/evaluation.md` changed, commit it with the code.
- [X] T017 Ask the owner before redeploying (`make deploy-azure`). After deploying:
  - wait for 100% traffic;
  - check the claim path and the scam path at 375 px on the live URL in ES, then switch to PT;
  - record the revision in CLAUDE.md and the build-status memory.

---

## Dependencies and execution order

- **T001 → T002**: the record before it's streamed.
- **T003** can run alongside T001-T002.
- **US1**: T004 (tests) → T005 (engine) → T006 [P] → T007 → T008.
  - T006 can start any time after T003.
  - T007 needs T003 and T006.
- **US2**: T009 → T010; T011 (tests) → T012 → T013 → T014.
  - T012 needs T009 and T010.
  - T013 uses `_finish`, so it needs T005.
  - T014 needs T008's spec file.
- **Polish**: T015 [P] any time after T013; T016 and T017 come last.

```text
T001 ──► T002 ──► T004 ──► T005 ──┬──────────────► T013 ──► T014 ──► T016 ──► T017
T003 ──► T006 ──► T007 ──► T008 ──┘                  ▲
T009 ──► T010 ──► T011 ──► T012 ─────────────────────┘
```

## Parallel opportunities

- T003 (types) and T006 (panel texts) alongside the backend work, T001-T005.
- T009-T010 (wordings and formatters) alongside US1.
- T015 (documentation) alongside T016's long UI run.

## Implementation strategy

1. **MVP**: T001-T008 (US1). The panel is the visible problem in the request and in the demo.
2. **Then**: T009-T014 (US2), the replies.
3. **Finish**: T015-T017, then one redeploy with the owner's approval.
