# Implementation Plan: Answers that react to what I ask

**Branch**: `007-reactive-replies` | **Date**: 2026-10-01 | **Spec**: [spec.md](spec.md)

## Summary

- **New intents**: three, recognised by the rules in English, Spanish, and Portuguese, and added to the model's schema:
  - `list_recent`, with an optional `count`;
  - `thanks`;
  - `help`.

  Greeting keywords gain time-of-day and "how are you?" phrasings.
- **The engine**:
  - `list_recent` calls a new read-only tool, `banking.recent_transactions(store, session customer, limit)`, then shows the movements as a candidate list (stage `choose`, progress charge/2). The reply is the new `recent_list` (basis `known`, source `tool:recent_transactions`) or `recent_none`.
  - Courtesy and help messages get their templates. At a pending question, the specs/006 re-ask leads with the courtesy (`greeting_short`, `thanks_short`, or `help`) instead of `need_answer`.
- **The demo**: examples gain "show my last movements" in each language, before the scam example.

## Technical Context

**Language/Version**: Python 3.10; TypeScript 6.0 / React 19. No new dependency.

**Testing**: pytest (rules mode), `make eval`, Playwright (`npm run check:ui`).

**Constraints**:
- no change to the guards, refusals, or the claim flow;
- the count is read before amounts, so "últimos 8" isn't an amount;
- the cap is 9 (the one-digit option reply).

## Constitution Check (v1.1.0)

| Principle | How | Result |
|---|---|---|
| I. Deterministic core | Intents by rules, with the model optional. Listing and replies are code and templates. | Pass |
| II. Permissions in the tool layer | `recent_transactions` takes the session's customer id; a customer reference in text still triggers the refusal first. | Pass |
| III. Verified facts only | Cards are records. The list statement is `known` with a tool source. A compliance-held charge in the list discloses nothing beyond a card; choosing it triggers the hold. | Pass |
| IV. No data in the repository | Nothing stored. | Pass |
| V. Evaluate before claiming | `make eval` must not drop. New tests per language. | Pass |

## Source changes

```text
backend/app/workflow/understanding.py  # RECENT, RECENT_COUNT_RE, THANKS, HELP, more GREETING; Understanding.count; intent order
backend/app/llm/claude.py              # schema: list_recent (count), thanks, help
backend/app/tools/banking.py           # recent_transactions
backend/app/workflow/engine.py         # _list_recent; courtesy branches; _reask(lead=...)
backend/app/workflow/messages.py       # recent_list, recent_none, thanks, thanks_short, greeting_short, help (en/es/pt)
backend/app/api/main.py                # EXAMPLES["recent"]
backend/tests/test_reactive.py         # US1, US2 per language
frontend/e2e/reactive.spec.ts          # the list and a courtesy reply on screen
```

## Complexity Tracking

None.
