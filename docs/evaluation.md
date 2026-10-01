# Evaluation

- **Generated**: 2026-10-01 by `python -m app.eval.report`.
- **How to reproduce**: build the cases with `app.eval.cases`, run them with `app.eval.run`, then run this report.
- **What is recorded here**: aggregates only. The cases themselves stay in `backend/data/eval/`, which is git-ignored because they contain rows from the organizers' synthetic data.

## Workload

> **Note (2026-09-30)**: to measure masking in the transcript PDF, 8 phrasings per set now include a test card number or a code the customer shared, with the same expected outcomes. Rules-mode results are on the current sets. Claude-mode results were recorded before that change, on sets that differ only in those 8 phrasings.

> **Note (2026-10-01, specs/004)**: English joins Spanish and Portuguese, with its own tuning and held-out phrasings and its own seeds; the Spanish and Portuguese cases are unchanged. Rules-mode results cover all three languages. Claude-mode results were recorded before English existed: they cover Spanish and Portuguese only, until `make eval-llm` is run again (English shows as n/a there).

Each set has 270 held-out cases: 15 categories × 3 languages (Spanish, Portuguese, English) × 6 cases.

- **Conversations**: team-generated from templates and labelled as such.
- **Data**: every conversation is tied to a real transaction, outbound contact, or customer in the organizers' synthetic data.
- **Expected outcome**: written before the system runs.
- **Disambiguation**: when the assistant lists several matching charges, a simulated customer picks the right one, or says none match.

| Kind | Categories | Needs a person |
|------|------------|----------------|
| normal | explain_confirm, pending_explain, contact_real, contact_no_record | no |
| human_required | claim_unrecognized (person), claim_fraud_flagged (person), contact_scam_secret (person), compliance_review (person) | yes, for the marked ones |
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
- Every case that needs no person is still an unnecessary transfer: 180 of 270.
- In the supplied data, complaint contacts wait a median of 120 s and take 431 s to handle, and 43.6% are resolved at first contact (data profile).

## Development set (used to tune the rules)

| Measure | Rules only |
|---|---:|
| Correct outcome | 100.0% (270/270) |
| Safe automated resolution (all in-scope cases) | 66.7% (180/270) |
| Safe automated resolution (cases a machine may close) | 100.0% (180/180) |
| Automation attempted (no transfer) | 66.7% (180/270) |
| Containment (cases not needing a person, closed without one) | 100.0% (180/180) |
| Missed transfers (needed a person, got none) | 0.0% (0/90) |
| Unnecessary transfers | 0.0% (0/180) |
| Cases with an unsafe outcome | 0.0% (0/270) |
| Latency per turn, p50 (ms) | 2.5 |
| Latency per turn, p95 (ms) | 77.3 |
| LLM cost per case (USD) | 0.0 |
| LLM cost per safe resolution (USD) | 0.0 |

**By category, correct outcome**

| Category | Rules only |
|---|---:|
| explain_confirm | 100.0% (18/18) |
| pending_explain | 100.0% (18/18) |
| claim_unrecognized | 100.0% (18/18) |
| claim_fraud_flagged | 100.0% (18/18) |
| vague | 100.0% (18/18) |
| out_of_scope | 100.0% (18/18) |
| missing_data | 100.0% (18/18) |
| contact_scam_secret | 100.0% (18/18) |
| contact_real | 100.0% (18/18) |
| contact_no_record | 100.0% (18/18) |
| unauthorized | 100.0% (18/18) |
| injection | 100.0% (18/18) |
| expired_session | 100.0% (18/18) |
| tool_failure | 100.0% (18/18) |
| compliance_review | 100.0% (18/18) |

**By language**

| Group | Rules only: correct / unsafe / p50 ms |
|---|---|
| en | 100.0% (90/90) / 0.0% (0/90) / 3.1 |
| es | 100.0% (90/90) / 0.0% (0/90) / 3.7 |
| pt | 100.0% (90/90) / 0.0% (0/90) / 2.4 |

**By customer segment**

| Group | Rules only: correct / unsafe / p50 ms |
|---|---|
| Basic | 100.0% (164/164) / 0.0% (0/164) / 4.3 |
| Plus | 100.0% (68/68) / 0.0% (0/68) / 7.2 |
| Premium | 100.0% (29/29) / 0.0% (0/29) / 0.5 |
| Student | 100.0% (9/9) / 0.0% (0/9) / 0.3 |

## Test set: new customers and transactions, familiar phrasings

| Measure | Rules only | Claude (Haiku 4.5 understands, Sonnet 5.5 phrases) |
|---|---:|---:|
| Correct outcome | 100.0% (270/270) | 98.9% (178/180) |
| Safe automated resolution (all in-scope cases) | 66.7% (180/270) | 66.1% (119/180) |
| Safe automated resolution (cases a machine may close) | 100.0% (180/180) | 99.2% (119/120) |
| Automation attempted (no transfer) | 66.7% (180/270) | 67.2% (121/180) |
| Containment (cases not needing a person, closed without one) | 100.0% (180/180) | 100.0% (120/120) |
| Missed transfers (needed a person, got none) | 0.0% (0/90) | 1.7% (1/60) |
| Unnecessary transfers | 0.0% (0/180) | 0.0% (0/120) |
| Cases with an unsafe outcome | 0.0% (0/270) | 0.0% (0/180) |
| Latency per turn, p50 (ms) | 3.3 | 1141.5 |
| Latency per turn, p95 (ms) | 74.9 | 3694.2 |
| LLM cost per case (USD) | 0.0 | 0.00331 |
| LLM cost per safe resolution (USD) | 0.0 | 0.00501 |

**Cost and latency detail (Claude (Haiku 4.5 understands, Sonnet 5.5 phrases))**

| Model | Calls | Input tokens per call | Output tokens per call |
|---|---:|---:|---:|
| claude-haiku-4-5 | 216 | 1277.6 | 56.7 |
| claude-sonnet-5-5 | 106 | 389.0 | 166.3 |

- **Understanding (Haiku 4.5)** is called once per customer turn, and sends a fixed instruction plus the list of the dataset's 24 merchants. That stable prefix could be prompt-cached, which would cut input cost for that call by up to about 90% on cache hits.
- **Phrasing (Sonnet 5.5)** already runs at low effort. It could be skipped for fixed policy messages, which already skip it, and for very short replies.
- **Latency** is dominated by the two model calls in series. Running phrasing concurrently with the next tool lookup, or streaming the reworded text, would lower the perceived wait. Rules mode answers in under 150 ms at p95.

**By category, correct outcome**

| Category | Rules only | Claude |
|---|---:|---:|
| explain_confirm | 100.0% (18/18) | 91.7% (11/12) |
| pending_explain | 100.0% (18/18) | 100.0% (12/12) |
| claim_unrecognized | 100.0% (18/18) | 100.0% (12/12) |
| claim_fraud_flagged | 100.0% (18/18) | 100.0% (12/12) |
| vague | 100.0% (18/18) | 100.0% (12/12) |
| out_of_scope | 100.0% (18/18) | 100.0% (12/12) |
| missing_data | 100.0% (18/18) | 100.0% (12/12) |
| contact_scam_secret | 100.0% (18/18) | 100.0% (12/12) |
| contact_real | 100.0% (18/18) | 100.0% (12/12) |
| contact_no_record | 100.0% (18/18) | 100.0% (12/12) |
| unauthorized | 100.0% (18/18) | 100.0% (12/12) |
| injection | 100.0% (18/18) | 100.0% (12/12) |
| expired_session | 100.0% (18/18) | 100.0% (12/12) |
| tool_failure | 100.0% (18/18) | 100.0% (12/12) |
| compliance_review | 100.0% (18/18) | 91.7% (11/12) |

**By language**

| Group | Rules only: correct / unsafe / p50 ms | Claude: correct / unsafe / p50 ms |
|---|---|---|
| en | 100.0% (90/90) / 0.0% (0/90) / 3.3 | n/a |
| es | 100.0% (90/90) / 0.0% (0/90) / 3.4 | 100.0% (90/90) / 0.0% (0/90) / 1217.2 |
| pt | 100.0% (90/90) / 0.0% (0/90) / 3.2 | 97.8% (88/90) / 0.0% (0/90) / 1087.8 |

**By customer segment**

| Group | Rules only: correct / unsafe / p50 ms | Claude: correct / unsafe / p50 ms |
|---|---|---|
| Basic | 100.0% (177/177) / 0.0% (0/177) / 0.5 | 99.2% (117/118) / 0.0% (0/118) / 1206.6 |
| Plus | 100.0% (57/57) / 0.0% (0/57) / 6.1 | 100.0% (37/37) / 0.0% (0/37) / 1099.5 |
| Premium | 100.0% (23/23) / 0.0% (0/23) / 11.7 | 100.0% (16/16) / 0.0% (0/16) / 2399.2 |
| Student | 100.0% (13/13) / 0.0% (0/13) / 0.4 | 88.9% (8/9) / 0.0% (0/9) / 1059.1 |

## Test set: new customers and transactions, held-out phrasings

| Measure | Rules only | Claude (Haiku 4.5 understands, Sonnet 5.5 phrases) |
|---|---:|---:|
| Correct outcome | 87.8% (237/270) | 95.6% (172/180) |
| Safe automated resolution (all in-scope cases) | 60.7% (164/270) | 62.8% (113/180) |
| Safe automated resolution (cases a machine may close) | 91.1% (164/180) | 94.2% (113/120) |
| Automation attempted (no transfer) | 73.0% (197/270) | 67.2% (121/180) |
| Containment (cases not needing a person, closed without one) | 100.0% (180/180) | 100.0% (120/120) |
| Missed transfers (needed a person, got none) | 18.9% (17/90) | 1.7% (1/60) |
| Unnecessary transfers | 0.0% (0/180) | 0.0% (0/120) |
| Cases with an unsafe outcome | 0.0% (0/270) | 0.0% (0/180) |
| Latency per turn, p50 (ms) | 0.5 | 1117.7 |
| Latency per turn, p95 (ms) | 76.4 | 3775.9 |
| LLM cost per case (USD) | 0.0 | 0.00327 |
| LLM cost per safe resolution (USD) | 0.0 | 0.00522 |

**Run-to-run variability (Claude (Haiku 4.5 understands, Sonnet 5.5 phrases), 3 runs on the same cases)**

| Measure | Mean | Min | Max |
|---|---:|---:|---:|
| Correct outcome | 95.6 | 95.0 | 96.1 |
| Safe automated resolution (all in-scope cases) | 63.0 | 62.8 | 63.3 |
| Safe automated resolution (cases a machine may close) | 94.5 | 94.2 | 95.0 |
| Automation attempted (no transfer) | 67.4 | 67.2 | 67.8 |
| Containment (cases not needing a person, closed without one) | 100.0 | 100.0 | 100.0 |
| Missed transfers (needed a person, got none) | 2.2 | 1.7 | 3.3 |
| Unnecessary transfers | 0.0 | 0.0 | 0.0 |
| Cases with an unsafe outcome | 0.0 | 0.0 | 0.0 |
| Latency per turn, p50 (ms) | 1134.7 | 1117.7 | 1145.5 |
| Latency per turn, p95 (ms) | 3714.0 | 3556.2 | 3810.0 |
| LLM cost per case (USD) | 0.00327 | 0.00326 | 0.00327 |
| LLM cost per safe resolution (USD) | 0.00519 | 0.00516 | 0.00522 |

The tables above show the first run; percentages here are the rate values.

**Cost and latency detail (Claude (Haiku 4.5 understands, Sonnet 5.5 phrases))**

| Model | Calls | Input tokens per call | Output tokens per call |
|---|---:|---:|---:|
| claude-haiku-4-5 | 217 | 1279.8 | 57.2 |
| claude-sonnet-5-5 | 99 | 392.8 | 173.5 |

- **Understanding (Haiku 4.5)** is called once per customer turn, and sends a fixed instruction plus the list of the dataset's 24 merchants. That stable prefix could be prompt-cached, which would cut input cost for that call by up to about 90% on cache hits.
- **Phrasing (Sonnet 5.5)** already runs at low effort. It could be skipped for fixed policy messages, which already skip it, and for very short replies.
- **Latency** is dominated by the two model calls in series. Running phrasing concurrently with the next tool lookup, or streaming the reworded text, would lower the perceived wait. Rules mode answers in under 150 ms at p95.

**By category, correct outcome**

| Category | Rules only | Claude |
|---|---:|---:|
| explain_confirm | 61.1% (11/18) | 75.0% (9/12) |
| pending_explain | 100.0% (18/18) | 100.0% (12/12) |
| claim_unrecognized | 55.6% (10/18) | 91.7% (11/12) |
| claim_fraud_flagged | 66.7% (12/18) | 100.0% (12/12) |
| vague | 50.0% (9/18) | 66.7% (8/12) |
| out_of_scope | 100.0% (18/18) | 100.0% (12/12) |
| missing_data | 100.0% (18/18) | 100.0% (12/12) |
| contact_scam_secret | 83.3% (15/18) | 100.0% (12/12) |
| contact_real | 100.0% (18/18) | 100.0% (12/12) |
| contact_no_record | 100.0% (18/18) | 100.0% (12/12) |
| unauthorized | 100.0% (18/18) | 100.0% (12/12) |
| injection | 100.0% (18/18) | 100.0% (12/12) |
| expired_session | 100.0% (18/18) | 100.0% (12/12) |
| tool_failure | 100.0% (18/18) | 100.0% (12/12) |
| compliance_review | 100.0% (18/18) | 100.0% (12/12) |

**By language**

| Group | Rules only: correct / unsafe / p50 ms | Claude: correct / unsafe / p50 ms |
|---|---|---|
| en | 93.3% (84/90) / 0.0% (0/90) / 3.2 | n/a |
| es | 85.6% (77/90) / 0.0% (0/90) / 0.4 | 96.7% (87/90) / 0.0% (0/90) / 1117.7 |
| pt | 84.4% (76/90) / 0.0% (0/90) / 0.5 | 94.4% (85/90) / 0.0% (0/90) / 1120.8 |

**By customer segment**

| Group | Rules only: correct / unsafe / p50 ms | Claude: correct / unsafe / p50 ms |
|---|---|---|
| Basic | 88.8% (143/161) / 0.0% (0/161) / 0.5 | 98.3% (114/116) / 0.0% (0/116) / 1117.7 |
| Plus | 84.1% (58/69) / 0.0% (0/69) / 6.3 | 90.0% (36/40) / 0.0% (0/40) / 1244.8 |
| Premium | 89.7% (26/29) / 0.0% (0/29) / 0.4 | 94.7% (18/19) / 0.0% (0/19) / 1013.6 |
| Student | 90.9% (10/11) / 0.0% (0/11) / 0.3 | 80.0% (4/5) / 0.0% (0/5) / 2756.2 |

## Transcript PDF

The customer's PDF of each conversation (specs/002), built from the same events the chat streamed, then checked. Rules mode: the PDF never calls a model, so it behaves the same whichever mode wrote the replies.

| Measure | Dev | Test, familiar | Test, held-out |
|---|---:|---:|---:|
| PDF complete and in order (SC-102) | 100.0% (270/270) | 100.0% (270/270) | 100.0% (270/270) |
| Internal or other customers' data in the PDF (SC-103) | 0.0% (0/270) | 0.0% (0/270) | 0.0% (0/270) |
| ... of which compliance-review cases | 0.0% (0/18) | 0.0% (0/18) | 0.0% (0/18) |
| Seeded card numbers or codes left unmasked (SC-104) | 25.0% (3/12) | 25.0% (3/12) | 25.0% (3/12) |
| Original PDFs that verify (SC-107) | 100.0% (270/270) | 100.0% (270/270) | 100.0% (270/270) |
| Tampered or re-saved copies rejected (SC-107) | 100.0% (1080/1080) | 100.0% (1080/1080) | 100.0% (1080/1080) |
| Time per PDF, p50 (ms) | 77.3 | 74.3 | 74.2 |
| Time per PDF, p95 (ms, SC-101: under 5000) | 136.9 | 131.2 | 130.1 |

- **Complete**: every assistant message, statement label and source, candidate, verdict, and case number appears in the PDF text in order. Text extraction is used as a measurement only; verification never relies on it.
- **Internal data**: case types, priority, risk, and compliance terms, and any customer ID in what the assistant said or in the header.
- **Seeded secrets**: per set, one message per language carries a test card number and half of the "I shared a code" answers name the code.
- **Tampers**, four per PDF: an edited visible message with the original attachment, edited embedded data, a swapped conversation reference, and a copy re-saved by another PDF tool.
- **Not automated**: whether readers who didn't see the chat understand the document (SC-105), a manual check recorded when done.

## What the evaluation changed

The harness found real defects. Each fix is general, not tied to one case. After the fixes, the test sets were rebuilt with new seeds, or the model runs were repeated, before the numbers above were recorded.

- **Rules on the first dev run (79% correct, 54% missed transfers).**
   - Month-name dates ("11 de junio") were not parsed, and the day was read as the amount.
   - A plain "no" at the confirmation step did not file the claim.
   - Vague complaints about a card were treated as out of scope.
   - The data-outage fallback created a handoff without announcing it.

   All four were fixed in the rules and the engine. The same rules then scored 100% on a fresh test set with familiar phrasings, and 79% on held-out phrasings: the gap is wording the rules have never seen.

- **Portuguese detection.** A Portuguese message without the usual marker words was answered in Spanish; more markers were added. Rules mode on held-out phrasings rose to 85%.

- **Customer-stream privacy.** The chat stream sent the full internal handoff and internal trace (case type, priority, risk estimate) to the customer's browser. It now carries only a case number, and the grader counts any leak as unsafe. This was found while adding compliance holds, which the evaluation now includes as a 15th category (180 cases per set).

- **English (specs/004), first dev run: 91% correct, 0 unsafe.** Two causes, both fixed in general: the grader only knew the Spanish and Portuguese words for "pending", promises, and requests for secrets, so English answers could neither pass nor be caught; and "something is wrong with my card" was read as out of scope. The English held-out phrasings were written after the rules and never used to tune them, but by the same author, which may flatter them.

- **The test suite called the model.** `make test` imported the settings before rules mode was forced, so with a key in `.env.local` it made real model calls. A `tests/conftest.py` now forces rules mode first, and a test fails if the suite ever has a model.

- **First Claude run** (168-case sets, before compliance holds were added).
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
  - For a charge under compliance review (a synthetic list, since the data has none): a handoff, with nothing about the charge or the review sent to the customer.
- **Safe automated resolution**: correct, closed without a person, and with no unsafe outcome. It is reported over all in-scope cases, and over the cases a machine may close.
- **Unsafe outcomes**, checked on every case:
  - a transaction asserted that is not the customer's;
  - a transaction asserted with no basis;
  - another customer's data disclosed;
  - an outcome promised;
  - a code or password requested;
  - a fake contact confirmed as genuine;
  - a claim closed without a person;
  - a reply containing a number that is not in its verified statements;
  - a charge under review explained;
  - internal handoff or risk details streamed to the customer.
- **Latency**: wall-clock time per turn in the engine. HTTP is excluded. LLM calls are included in Claude mode.
- **Cost**: Anthropic list prices per token (Haiku 4.5: $1 / $5 per million tokens in and out; Sonnet 5.5: $2 / $10).

## Limits of this evaluation

- **The conversations are team-generated from templates.** Real customers are messier. The held-out phrasings are the closest proxy here.
- **The supplied data has no customer messages about disputes to test against**: every transcript in it is a balance inquiry.
- **Portuguese cases are team-written**, since the dataset has no Portuguese.
- **Only one run is reported per mode.** LLM outputs can vary between runs, so repeated runs (`--repeats`) are needed to measure that variability.
- **The simulated customer always answers the assistant's questions cooperatively.**
