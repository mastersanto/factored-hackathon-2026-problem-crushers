# Evaluation

- **Generated**: 2026-09-30 by `python -m app.eval.report`.
- **How to reproduce**: build the cases with `app.eval.cases`, run them with `app.eval.run`, then run this report.
- **What is recorded here**: aggregates only. The cases themselves stay in `backend/data/eval/`, which is git-ignored because they contain rows from the organizers' synthetic data.

## Workload

Each set has 168 held-out cases: 14 categories × 2 languages (Spanish, Portuguese) × 6 cases.

- **Conversations**: team-generated from templates and labelled as such.
- **Data**: every conversation is tied to a real transaction, outbound contact, or customer in the organizers' synthetic data.
- **Expected outcome**: written before the system runs.
- **Disambiguation**: when the assistant lists several matching charges, a simulated customer picks the right one, or says none match.

| Kind | Categories | Needs a person |
|------|------------|----------------|
| normal | explain_confirm, pending_explain, contact_real, contact_no_record | no |
| human_required | claim_unrecognized (person), claim_fraud_flagged (person), contact_scam_secret (person) | yes, for the marked ones |
| ambiguous | vague, missing_data | no |
| unsupported | out_of_scope | no |
| security | unauthorized, injection | no |
| failure | expired_session, tool_failure (person) | yes, for the marked ones |

The three sets are built the same way with different random seeds:

- **Dev** (seed 7): used while fixing the rules.
- **Test, familiar phrasings** (seed 8): new customers and transactions, the same phrasing templates.
- **Test, held-out phrasings** (seed 9): new customers and transactions, and phrasings written after the rules were tuned and never used to tune them. This is the fair test of understanding.

**Baseline: every case goes to an agent.**

- No automation and no containment.
- Every case that needs no person is still an unnecessary transfer: 120 of 168.
- In the supplied data, complaint contacts wait a median of 120 s and take 431 s to handle, and 43.6% are resolved at first contact (data profile).

## Development set (used to tune the rules)

| Measure | Rules only |
|---|---:|
| Correct outcome | 100.0% (168/168) |
| Safe automated resolution (all in-scope cases) | 71.4% (120/168) |
| Safe automated resolution (cases a machine may close) | 100.0% (120/120) |
| Automation attempted (no transfer) | 71.4% (120/168) |
| Containment (cases not needing a person, closed without one) | 100.0% (120/120) |
| Missed transfers (needed a person, got none) | 0.0% (0/48) |
| Unnecessary transfers | 0.0% (0/120) |
| Cases with an unsafe outcome | 0.0% (0/168) |
| Latency per turn, p50 (ms) | 0.6 |
| Latency per turn, p95 (ms) | 112.4 |
| LLM cost per case (USD) | 0.0 |
| LLM cost per safe resolution (USD) | 0.0 |

**By category, correct outcome**

| Category | Rules only |
|---|---:|
| explain_confirm | 100.0% (12/12) |
| pending_explain | 100.0% (12/12) |
| claim_unrecognized | 100.0% (12/12) |
| claim_fraud_flagged | 100.0% (12/12) |
| vague | 100.0% (12/12) |
| out_of_scope | 100.0% (12/12) |
| missing_data | 100.0% (12/12) |
| contact_scam_secret | 100.0% (12/12) |
| contact_real | 100.0% (12/12) |
| contact_no_record | 100.0% (12/12) |
| unauthorized | 100.0% (12/12) |
| injection | 100.0% (12/12) |
| expired_session | 100.0% (12/12) |
| tool_failure | 100.0% (12/12) |

**By language**

| Group | Rules only: correct / unsafe / p50 ms |
|---|---|
| es | 100.0% (84/84) / 0.0% (0/84) / 0.6 |
| pt | 100.0% (84/84) / 0.0% (0/84) / 0.6 |

**By customer segment**

| Group | Rules only: correct / unsafe / p50 ms |
|---|---|
| Basic | 100.0% (105/105) / 0.0% (0/105) / 0.6 |
| Plus | 100.0% (40/40) / 0.0% (0/40) / 0.6 |
| Premium | 100.0% (16/16) / 0.0% (0/16) / 9.2 |
| Student | 100.0% (7/7) / 0.0% (0/7) / 0.5 |

## Test set: new customers and transactions, familiar phrasings

| Measure | Rules only | Claude (Haiku 4.5 understands, Sonnet 5.5 phrases) |
|---|---:|---:|
| Correct outcome | 100.0% (168/168) | 100.0% (168/168) |
| Safe automated resolution (all in-scope cases) | 71.4% (120/168) | 71.4% (120/168) |
| Safe automated resolution (cases a machine may close) | 100.0% (120/120) | 100.0% (120/120) |
| Automation attempted (no transfer) | 71.4% (120/168) | 71.4% (120/168) |
| Containment (cases not needing a person, closed without one) | 100.0% (120/120) | 100.0% (120/120) |
| Missed transfers (needed a person, got none) | 0.0% (0/48) | 0.0% (0/48) |
| Unnecessary transfers | 0.0% (0/120) | 0.0% (0/120) |
| Cases with an unsafe outcome | 0.0% (0/168) | 0.0% (0/168) |
| Latency per turn, p50 (ms) | 0.7 | 1226.4 |
| Latency per turn, p95 (ms) | 112.5 | 3818.1 |
| LLM cost per case (USD) | 0.0 | 0.00345 |
| LLM cost per safe resolution (USD) | 0.0 | 0.00483 |

**By category, correct outcome**

| Category | Rules only | Claude |
|---|---:|---:|
| explain_confirm | 100.0% (12/12) | 100.0% (12/12) |
| pending_explain | 100.0% (12/12) | 100.0% (12/12) |
| claim_unrecognized | 100.0% (12/12) | 100.0% (12/12) |
| claim_fraud_flagged | 100.0% (12/12) | 100.0% (12/12) |
| vague | 100.0% (12/12) | 100.0% (12/12) |
| out_of_scope | 100.0% (12/12) | 100.0% (12/12) |
| missing_data | 100.0% (12/12) | 100.0% (12/12) |
| contact_scam_secret | 100.0% (12/12) | 100.0% (12/12) |
| contact_real | 100.0% (12/12) | 100.0% (12/12) |
| contact_no_record | 100.0% (12/12) | 100.0% (12/12) |
| unauthorized | 100.0% (12/12) | 100.0% (12/12) |
| injection | 100.0% (12/12) | 100.0% (12/12) |
| expired_session | 100.0% (12/12) | 100.0% (12/12) |
| tool_failure | 100.0% (12/12) | 100.0% (12/12) |

**By language**

| Group | Rules only: correct / unsafe / p50 ms | Claude: correct / unsafe / p50 ms |
|---|---|---|
| es | 100.0% (84/84) / 0.0% (0/84) / 0.7 | 100.0% (84/84) / 0.0% (0/84) / 1115.2 |
| pt | 100.0% (84/84) / 0.0% (0/84) / 0.8 | 100.0% (84/84) / 0.0% (0/84) / 1312.9 |

**By customer segment**

| Group | Rules only: correct / unsafe / p50 ms | Claude: correct / unsafe / p50 ms |
|---|---|---|
| Basic | 100.0% (111/111) / 0.0% (0/111) / 0.6 | 100.0% (111/111) / 0.0% (0/111) / 1220.4 |
| Plus | 100.0% (33/33) / 0.0% (0/33) / 10.5 | 100.0% (33/33) / 0.0% (0/33) / 1224.3 |
| Premium | 100.0% (15/15) / 0.0% (0/15) / 10.9 | 100.0% (15/15) / 0.0% (0/15) / 2429.8 |
| Student | 100.0% (9/9) / 0.0% (0/9) / 0.4 | 100.0% (9/9) / 0.0% (0/9) / 1168.9 |

## Test set: new customers and transactions, held-out phrasings

| Measure | Rules only | Claude (Haiku 4.5 understands, Sonnet 5.5 phrases) |
|---|---:|---:|
| Correct outcome | 79.2% (133/168) | 95.2% (160/168) |
| Safe automated resolution (all in-scope cases) | 64.3% (108/168) | 67.3% (113/168) |
| Safe automated resolution (cases a machine may close) | 90.0% (108/120) | 94.2% (113/120) |
| Automation attempted (no transfer) | 85.1% (143/168) | 72.0% (121/168) |
| Containment (cases not needing a person, closed without one) | 100.0% (120/120) | 100.0% (120/120) |
| Missed transfers (needed a person, got none) | 47.9% (23/48) | 2.1% (1/48) |
| Unnecessary transfers | 0.0% (0/120) | 0.0% (0/120) |
| Cases with an unsafe outcome | 0.0% (0/168) | 0.0% (0/168) |
| Latency per turn, p50 (ms) | 0.6 | 1112.3 |
| Latency per turn, p95 (ms) | 116.2 | 3690.0 |
| LLM cost per case (USD) | 0.0 | 0.00334 |
| LLM cost per safe resolution (USD) | 0.0 | 0.00497 |

**By category, correct outcome**

| Category | Rules only | Claude |
|---|---:|---:|
| explain_confirm | 58.3% (7/12) | 58.3% (7/12) |
| pending_explain | 100.0% (12/12) | 91.7% (11/12) |
| claim_unrecognized | 16.7% (2/12) | 100.0% (12/12) |
| claim_fraud_flagged | 41.7% (5/12) | 91.7% (11/12) |
| vague | 41.7% (5/12) | 91.7% (11/12) |
| out_of_scope | 100.0% (12/12) | 100.0% (12/12) |
| missing_data | 100.0% (12/12) | 100.0% (12/12) |
| contact_scam_secret | 50.0% (6/12) | 100.0% (12/12) |
| contact_real | 100.0% (12/12) | 100.0% (12/12) |
| contact_no_record | 100.0% (12/12) | 100.0% (12/12) |
| unauthorized | 100.0% (12/12) | 100.0% (12/12) |
| injection | 100.0% (12/12) | 100.0% (12/12) |
| expired_session | 100.0% (12/12) | 100.0% (12/12) |
| tool_failure | 100.0% (12/12) | 100.0% (12/12) |

**By language**

| Group | Rules only: correct / unsafe / p50 ms | Claude: correct / unsafe / p50 ms |
|---|---|---|
| es | 84.5% (71/84) / 0.0% (0/84) / 0.6 | 95.2% (80/84) / 0.0% (0/84) / 1135.8 |
| pt | 73.8% (62/84) / 0.0% (0/84) / 0.6 | 95.2% (80/84) / 0.0% (0/84) / 1097.9 |

**By customer segment**

| Group | Rules only: correct / unsafe / p50 ms | Claude: correct / unsafe / p50 ms |
|---|---|---|
| Basic | 81.5% (88/108) / 0.0% (0/108) / 0.6 | 95.4% (103/108) / 0.0% (0/108) / 1101.3 |
| Plus | 75.7% (28/37) / 0.0% (0/37) / 0.7 | 94.6% (35/37) / 0.0% (0/37) / 1117.6 |
| Premium | 72.2% (13/18) / 0.0% (0/18) / 0.4 | 100.0% (18/18) / 0.0% (0/18) / 1116.8 |
| Student | 80.0% (4/5) / 0.0% (0/5) / 42.0 | 80.0% (4/5) / 0.0% (0/5) / 2583.8 |

## What the evaluation changed

The harness found real defects. Each fix is general, not tied to one case. After the fixes, the test sets were rebuilt with new seeds, or the model runs were repeated, before the numbers above were recorded.

1. **Rules on the first dev run (79% correct, 54% missed transfers).**
   - Month-name dates ("11 de junio") were not parsed, and the day was read as the amount.
   - A plain "no" at the confirmation step did not file the claim.
   - Vague complaints about a card were treated as out of scope.
   - The data-outage fallback created a handoff without announcing it.

   All four were fixed in the rules and the engine. The same rules then scored 100% on a fresh test set with familiar phrasings, and 79% on held-out phrasings: the gap is wording the rules have never seen.

2. **First Claude run.**
   - On the familiar-phrasings set, 1.8% (3/168) of cases had an unsafe outcome (claim_closed_without_person 3).
   - Haiku 4.5 sometimes read "no, no lo reconozco" as "it was mine", and the possible fraud claim was closed without a person.
   - **Fix (a deterministic guard in the engine):** at the confirmation step, a negation detected by the rules always files the claim. Closing a case as "mine" needs the rules and the model to agree; otherwise the assistant asks again.
   - A regression test with a deliberately misreading model covers it (`backend/tests/test_guards.py`). The numbers above come from the rerun after the fix.

## Definitions

- **Correct outcome**: the category's expected result.
  - The right transaction explained and closed (normal cases).
  - A clarifying question or abstention, with no transaction asserted (ambiguous or unsupported cases).
  - A structured handoff carrying the right transaction, the country's rules, and the right priority (cases needing a person).
  - The right verdict for a claimed bank contact.
  - A refusal for another customer's data.
  - A session-expired error.
  - A safe handoff on a data outage.
- **Safe automated resolution**: correct, closed without a person, and with no unsafe outcome. It is reported over all in-scope cases, and over the cases a machine may close.
- **Unsafe outcomes**, checked on every case:
  - a transaction asserted that is not the customer's;
  - a transaction asserted with no basis;
  - another customer's data disclosed;
  - an outcome promised;
  - a code or password requested;
  - a fake contact confirmed as genuine;
  - a claim closed without a person;
  - a reply containing a number that is not in its verified statements.
- **Latency**: wall-clock time per turn in the engine. HTTP is excluded. LLM calls are included in Claude mode.
- **Cost**: Anthropic list prices per token (Haiku 4.5: $1 / $5 per million tokens in and out; Sonnet 5.5: $2 / $10).

## Limits of this evaluation

- **The conversations are team-generated from templates.** Real customers are messier. The held-out phrasings are the closest proxy here.
- **The supplied data has no customer messages about disputes to test against**: every transcript in it is a balance inquiry.
- **Portuguese cases are team-written**, since the dataset has no Portuguese.
- **Only one run is reported per mode.** LLM outputs can vary between runs, so repeated runs (`--repeats`) are needed to measure that variability.
- **The simulated customer always answers the assistant's questions cooperatively.**
