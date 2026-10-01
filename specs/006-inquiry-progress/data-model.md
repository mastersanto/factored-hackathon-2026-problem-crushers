# Data model: Replies and progress that follow my inquiry

Nothing is stored beyond the in-memory session. Nothing changes in the warehouse, the handoff queue, or the PDF register.

## Inquiry (session, new)

| Field | Type | Rule |
|---|---|---|
| `path` | `"charge"` \| `"contact"` | Set when the inquiry starts (research R3) |
| `stage` | int, 1-based | 1-5 for charge and 1-4 for contact. Never above the path's total |
| `done` | bool | True only at the path's last stage |
| `outcome` | `"recognized"` \| `"specialist"` \| `"urgent"` \| `"genuine"` \| `"no_record"` \| `"warned"` \| null | Set exactly when `done` is true; null otherwise |
| `case` | string \| null | The case number when `outcome` is `specialist` or `urgent`; null otherwise |

`Session.inquiry` is null until the first message that starts an inquiry.

**Path totals**: charge has 5 stages and contact has 4 (research R2). `done` implies `stage == total`.

## Transitions (set by the engine)

**Charge path**

| Engine branch (today) | `s.stage` after | Inquiry after |
|---|---|---|
| dispute with no details (`need_details`) | unchanged | charge, stage 1 (a new inquiry if none or done; else unchanged, R3) |
| search: none found / too many | unchanged | charge, stage 2 |
| search: several candidates (`choose`) | `choose` | charge, stage 2 |
| charge explained (`ask_confirm`) | `confirm` | charge, stage 3 |
| "It wasn't me" (`collect_statement`) | `statement` | charge, stage 4 |
| "Yes, it was me" (`close_recognized`) | `closed` | charge, 5, done, `recognized` |
| claim filed (`_file_claim`) | `closed` | charge, 5, done, `specialist`, case |
| compliance hold | `closed` | charge, 5, done, `specialist`, case (nothing else, no tipping-off) |

**Contact path**

| Engine branch | `s.stage` after | Inquiry after |
|---|---|---|
| check: genuine bank contact | unchanged | contact, 4, done, `genuine` |
| check: no record | unchanged | contact, 4, done, `no_record` |
| check: scam asked for a secret, shared not stated | `contact_shared` | contact, stage 3 |
| check: scam, customer said nothing was shared | unchanged | contact, 4, done, `warned` |
| scam, secret shared (in the message or the follow-up) | `closed` | contact, 4, done, `urgent`, case |
| follow-up "no" | `start` | contact, 4, done, `warned` |

**Any path**

| Branch | Inquiry after |
|---|---|
| technical fallback | the current path (charge if none), last stage, done, `specialist`, case |
| greeting, out of scope, refusal, re-ask (`reask_pending`), expired, turn limit | unchanged |

Stage 2 ("We find the charge" / "We check the bank's records") of the contact path has no state of its own: the check resolves within one reply, so it goes straight to stage 3 or done.

## Statement recipes (new keys)

| Key | Params | Used when |
|---|---|---|
| `none_found_with` | `searched`, `missing` | the search had details and found nothing |
| `choose_with` | `searched` | the search had details and found 2-5 |
| `too_many_with` | `searched`, `missing` | the search had details and found more than 5 |
| `need_answer` | none | it precedes the re-asked question (`choose`, `ask_confirm`, `ask_shared`) |

**`searched`**: `{amount?: float, merchant?: str, date?: ISO date}`. Only the values passed to the search, and at least one.

**`missing`**: an ordered subset of `["amount", "merchant", "date"]`, the keys not in `searched`.

The old keys `none_found`, `choose`, and `too_many` stay:
- `choose` is the re-asked question at the `choose` stage;
- r1/r2 transcripts still re-render through them.

## Progress (API, new)

`progress` is `Inquiry` serialised as `{path, stage, total, done, outcome, case}`, or null. `total` is derived from the path, so the browser doesn't hard-code it.
