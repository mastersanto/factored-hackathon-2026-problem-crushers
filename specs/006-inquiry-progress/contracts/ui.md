# UI contract: the progress panel and replies

## The panel ("How we review your case")

- **Lists**: one ordered list for the path in `progress.path` (research R2), or the charge list when `progress` is null. Names and descriptions come from `TEXT[lang].steps`:
  - `charge.names` and `charge.lines` (5 each);
  - `contact.names` and `contact.lines` (4 each);
  - `outcomes[outcome]`: the closing line, with `{case}` filled in when there is a case.
- **Each stage**:
  - `done` (check icon) when below `progress.stage`, or when `progress.done`;
  - `current` (`aria-current="step"`) at `progress.stage` when not done;
  - `todo` otherwise.
- **The phone drawer's summary**:
  - no progress: `notStarted`;
  - in progress: `progress(n, total, name)`, for example "Step 3 of 5 · You confirm if it was you";
  - done: the outcome line, for example "Sent to a specialist · case CASO-EF06E0".
- **The technical trace**: the internal step events of the latest reply, unchanged.
- **Languages**: every text in en, es, and pt. The panel re-words at once on a language switch, and the stage is unchanged.

## Replies

- **Wording**: the new search replies name the details searched for (data-model.md, recipe keys), in the conversation's language.
- **A re-asked question**: two sentences in one message, "To continue I need your answer to this question." and then the question. The quick replies for that question stay on screen.

## Checks (`frontend/e2e/progress.spec.ts`)

| Check | Steps | Expected |
|---|---|---|
| Not started | sign in | summary `notStarted`; no `aria-current` |
| Claim path | Spanish charge example → "No fui yo" → statement quick reply | after each reply, `aria-current` on stage 3, then 4; at the end all 5 done and the summary shows the case number from the handoff card |
| Recognized | charge example → "Sí, fui yo" | all done, outcome "recognized" line |
| No move | at "was it you?", send a greeting | the same `aria-current` stage; the reply ends with the "was it you?" question; the quick replies are still on screen |
| Contact path | contact example | the contact list (4 stages), done with the "genuine" or "no record" outcome, matching the verdict |
| Scam, unclear answer | scam example → "hmm" | stage 3 of 4 stays current; the reply asks again whether anything was shared |
| Switch | mid-claim, pick PT | the same stage number, Portuguese names |
| New inquiry | after a closed claim, send another charge | the panel restarts at the charge list, stage 2 or 3 |
| Phone | 375 px, drawer | summary matches the table above; no sideways scroll |
| axe | each state above | no violations |
