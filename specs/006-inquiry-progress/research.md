# Research: Replies and progress that follow my inquiry

Decisions for [plan.md](plan.md).

## R1. Where the inquiry's progress lives: on the session, set by the engine

- **Decision**:
  - `Session` gains `inquiry: Inquiry | None`, with path (`charge` | `contact`), current stage (1-based), `done`, `outcome`, and `case`.
  - The engine sets it at the exact points where it already changes `s.stage` or files a case (data-model.md, transition table).
  - Every `done` event and every conversation view (`GET /api/session/conversation`, `POST /api/session/language`) carry it as `progress`.
- **Why**:
  - FR-603: the stage must come from the same state that decides the next question. The engine is the only place that knows it.
  - A re-show must show the same stage (specs/004). The view is built from the session, so it can't drift.
  - The browser only displays it, so there's no frontend logic to keep in step with the workflow.
- **Considered**:
  - **Derive it in the browser** from `done.stage` and the events. Rejected:
    - `stage` alone can't tell "recognized" from "sent to a specialist" (both `closed`);
    - the contact path's verdicts have no stage;
    - the logic would duplicate the engine's.
  - **Reuse `s.stage`.** Rejected: it's the workflow's input state (what the next message means), not the customer's progress. "closed" covers four outcomes, and contact checks without a follow-up never leave "start".

## R2. The stage lists (owner's choice, option A)

One ordered list per path, in plain words (spec FR-602). Names and one-line descriptions live in the frontend's `TextSet` (UI wording, like today's step names), keyed by path and stage number. The outcome line is chosen by `outcome`.

| # | Charge | Contact check |
|---|---|---|
| 1 | Tell us what happened | Tell us about the contact |
| 2 | We find the charge | We check the bank's records |
| 3 | You confirm if it was you | You tell us if you shared anything |
| 4 | You give your account | Done, or sent to a specialist |
| 5 | Case closed or sent to a specialist | — |

- **Before any inquiry**: the panel shows the charge list, nothing started (the summary is "Starts with your first message", as today). Most visitors come to dispute a charge.
- **The contact path**: it has 4 stages, so the drawer summary reads "Step N of 4". The total comes from the path.

## R3. Which messages leave the progress unchanged (FR-604)

- **Unchanged**: greeting, out of scope, refused (other customer, injection), a re-asked pending question (R5), session expired, and turn limit. The engine doesn't touch `inquiry` on those branches.
- **A new inquiry**:
  - a charge search with details, a dispute without details, or a contact check, **when there is no inquiry or the current one is done**;
  - or, while an inquiry is pending, a message that clearly starts another one: a search with details, or a contact check (spec US2 scenario 6, unchanged behaviour).

  A dispute without details while an inquiry is pending gets "need details" and leaves the inquiry where it is. Example: "I don't recognize a charge" at "was it you?" is a `file_claim` there, not a new inquiry.
- **Technical fallback**: the inquiry becomes done with outcome `specialist` and its case. With no inquiry yet, it opens a charge inquiry, already done.

## R4. Replies that name what was searched (FR-605, FR-606)

- **Decision**: three new templates, `none_found_with`, `choose_with`, and `too_many_with`. They're used whenever the search had at least one detail, which is always the case, since a search without details stops at `need_details`. Each takes two params:
  - `searched`: `{amount?, merchant?, date?}`, the understood values actually passed to `find_transactions`;
  - `missing`: the subset of `["amount", "merchant", "date"]` not given.

  `render_text` gains two param formatters:
  - **`searched`**: a phrase per language, for example "of 250.00 at Cinépolis on June 12, 2026" / "de 250,00 en Cinépolis el 12 de junio de 2026" / "de 250,00 em Cinépolis em 12 de junho de 2026";
  - **`missing`**: "the merchant or the day" / "el comercio o el día" / "a loja ou o dia". With nothing missing it falls back to "the exact amount, the merchant, or the day".
- **Amount formatting**: the number with the language's separators and no currency, the same as the 005 example messages. The customer wrote no currency, so none is invented (FR-606).
- **Merchant**: the understanding's merchant, which is already matched to a merchant name in the records. Never free text.
- **Date**: `M.day`, the same as other dates.
- **Why recipes**: the params are stored in the statement recipe (specs/004), so a re-show in another language re-words them like every other reply. The PDF records them like any other message.
- **Statement source**: `flow` with basis `rule`, the same as today's wordings. The repeated details are the customer's own, not record facts.
- **Considered**: having the model phrase the echo. Rejected: rules mode must do it (FR-607), and these replies are `verify=False` templates today.

## R5. Asking a pending question again (FR-605, FR-608)

- **Pending questions**: `choose` ("which one?"), `confirm` ("was it you?"), and `contact_shared` ("did you share anything?").
  - `statement` is not included: any text there *is* the customer's account, as today.
- **At `choose` and `confirm`**: a message whose intent is `greeting` or `out_of_scope` gets a re-ask.
  - The reply is the new `need_answer` template ("To continue I need your answer to this question.") followed by the stage's own question template: `choose` or `ask_confirm`.
  - The step action is `reask_pending`.
  - The stage and quick replies are unchanged.
- **At `contact_shared`**: today every message goes to the follow-up, and anything not clearly "yes" counts as "no". New order:
  1. a contact check or a charge search with details starts a new inquiry (R3);
  2. otherwise `shared = _yes_no(text)`, then if that's unclear, `_yes_no_shared(text)`;
  3. `True` escalates and `False` gives the freeze hint (as today);
  4. `None` is re-asked with `need_answer` + `ask_shared`.
  - **Safety**: an unclear answer no longer closes the check as "nothing shared". Asking again is the safer reading (constitution III). Any explicit "shared" in either parser escalates.
- **Unchanged**: refusals (other customer, injection). Those quick replies stay, since the stage is unchanged.
- **Eval impact**: the evaluation's out-of-scope cases start fresh (stage `start`), so `abstain_out_of_scope` is unchanged. The contact cases answer with explicit `SHARED_YES` phrasings. `make eval` confirms both (FR-609).

## R6. The panel component

- **Decision**: `StepsPanel` takes `progress` (the server's object or null) instead of the index from `stepProgress`.
  - It renders the path's list (R2), with stages before the current one done, the current one marked `aria-current="step"`, and when `done`, all done plus the outcome line (with the case number when there is one).
  - `stepProgress` and `STEP_ORDER` are removed.
  - The technical trace (`details.technical`) is unchanged.
- **Source in the browser**: `useChat` keeps `progress` from each `done` and each re-show, the same way it keeps `stage` and `replies`.
- **Accessibility**: the stage list stays an ordered list. When the stage changes, the drawer summary is announced by the existing polite live region with the reply. No extra announcements.
