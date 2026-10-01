# Limitations, caveats, and future work

What this prototype does not do, what its numbers do not prove, and what a bank would need before running it. This follows the organizers' request for "an honest account of the work required before deployment".

## 1. Data

| Limitation | Consequence | How we handled it |
|---|---|---|
| The dataset is **synthetic**, and several fields are random with respect to the facts: decline response codes (only 7.3% match the facts), SLA flags, credit repayment, app-error timing. | Explanations built on those fields would be wrong. | The assistant explains only fields that behave consistently: merchant, amount, date, place, channel, card, status. It never explains a response code. |
| **Currency follows the product, not the purchase.** There are no MXN transactions, and 52.8% of domestic purchases are in a foreign currency. | Exchange-rate explanations are impossible. | The recorded currency is reported as is. Exchange-rate and installment explanations are out of scope. |
| **Only 24 merchant names.** | "You've paid this merchant before" carries little weight. | The history is stated as a known fact, not as proof. |
| **No customer messages about disputes, and no Portuguese.** Every transcript in the data is a balance inquiry. | Understanding cannot be trained or tested on real dispute wording. | The evaluation conversations are team-generated, in Spanish and Portuguese, and labelled as such. A separate set of held-out phrasings tests generalization. |
| **No link from a complaint to a transaction**, and complaint descriptions are templates. | Claims cannot be matched to past outcomes. | Handoffs carry the verified transaction instead. |
| **The fraud label is random with respect to every behavioural feature.** The detector score separates about half the frauds perfectly, and may be derived from the label. | A behavioural model scores at chance. The learned component mostly recovers the generator's boundary. | This is documented in `docs/model-card.md`. The estimate only sets priority and adds one hedged sentence; a "no fui yo" always reaches a person. |
| **No charge is flagged as under anti-money-laundering review.** | The "never explain" rule (FR-018) could not be exercised. | A labelled synthetic review list (0.05% of transactions) demonstrates it. |
| **The outbound record lacks transactional alerts and collections.** | "No record" is not proof of a scam. | The verdict is worded as "no record, treat as a possible scam". A contact that asked for a code is always a scam, whatever the record says. |
| **Amounts have no customer-level money measure of service cost.** | Value is measured in time and follow-ups, not money. | Baselines come from the data: median wait and handle time, first-contact resolution, and SLA breaches. |

## 2. Evaluation

- **The conversations are templated.** Real customers are messier: typos, several requests in one message, anger, long stories. The held-out phrasings are a proxy, not a substitute.
- **The simulated customer is cooperative.** It always answers the assistant's question and picks the right option. Real customers drop off, change their minds, or answer something else.
- **The legal rules come from desk research**, not from a lawyer's or the financial specialist's validation (still pending). They cover Mexico, Colombia, and Argentina only.
- **Model outputs vary between runs.** Repeated runs are reported in `docs/evaluation.md`, but three runs give a range, not a confidence interval.
- **Fairness has not been measured.** No outcome is broken down by country, segment, or accent beyond the correct-outcome and unsafe rates, and the fraud estimate is not audited for disparate impact. Its only input is the transaction's detector score.

## 3. Product scope

- **One workflow only**: dispute intake. The assistant does not decide claims, refund, block merchants, or move money, and it cannot cancel a recurring charge itself. It hands those requests to a person.
- **The synthetic fee schedule was not built.** For the bank's own charges (fees, interest), the assistant files a complete claim but does not explain the fee.
- **No real channels.** It is web chat only; there is no WhatsApp, phone, or email integration.

## 4. Transcript PDF and check codes

The customer can download the conversation as a PDF with a check code (`specs/002-chat-transcript-pdf/`). What it does not do:

- **A check code is not a legal electronic signature.** It is a keyed hash (HMAC) that only the bank can compute and check. A court or regulator would expect a signed PDF (PAdES) with a bank certificate. That is future work, and whether a regulator in Mexico, Colombia, or Argentina accepts either is not claimed.
- **Only the original file verifies.** Verification re-renders the conversation and compares the whole file, since comparing page content alone misses edits (a finding recorded in the research). A copy re-saved by another tool, such as "print to PDF", reports *altered* even if it looks the same. The PDF tells the customer to keep the original.
- **Verification is unauthenticated in the demo**, like the specialist queue. It returns only match or altered, the time, and the case numbers, which are already printed on the PDF its caller holds. Production would put it behind staff authentication and offer it to regulators through the bank's own channels.
- **The register is not durable in the demo.** The fingerprint register is a file in the container, lost when the app scales to zero, like the handoffs. A PDF still verifies after that, because the check recomputes the code with the key (kept as a secret). Only "registered" turns false.
- **Masking is pattern-based.** Card numbers (13 to 19 digits) and codes near words such as *código*, *clave*, *PIN*, or *senha* are masked. A secret written in words, or a number far from any keyword, would not be. The masking applies to the PDF only: the handoff still records the customer's statement as typed.
- **The renderer is pinned.** Byte-identical output depends on the fpdf2 version. A PDF from an earlier renderer reports *unknown version* rather than a result.

## 5. What production would need

| Area | In the prototype | Needed before a real deployment |
|---|---|---|
| **Identity and access** | A demo login picks a synthetic customer; sessions are random tokens held in memory and expire after 30 minutes. | The bank's identity service (strong authentication, step-up for sensitive actions); sessions in a shared store; staff authentication and role-based access to the specialist queue, which has **no authentication in the demo**. |
| **Data access** | A read-only local warehouse built from a data dump, minimized at build time. | Live, read-only services for transactions, cards, contacts, and compliance holds, behind the same tool interfaces, with per-field access control. |
| **Data retention and privacy** | Handoffs in a local JSON-lines file; no conversation log; minimal fields sent to the model provider. | A retention policy per country (LFPDPPP in Mexico, Law 1581 in Colombia, Law 25.326 in Argentina); encrypted case storage; a data-processing agreement and zero-retention settings with the model provider; subject-access and deletion procedures. |
| **Reliability** | Bounded retries on model calls (2); a rules fallback on any model failure or refusal; a safe handoff on a data-service failure. One replica, scaling to zero. | Several replicas with health-based routing; timeouts per dependency; a circuit breaker on the model provider; a queue for handoffs, so none are lost if the specialist system is down. |
| **Capacity** | Tested at demo scale. DuckDB serves a 1 MB demo subset in memory. The main latency is the two model calls (p95 about 4 s). | Load testing; a production database or service for records; prompt caching; concurrency limits sized to the model provider's rate limits. |
| **Monitoring** | Structured logs; a per-turn trace (understand, decide, act, verify, escalate) with internal steps kept server-side; model spend and a spend cap. | Metrics and alerts on unsafe-outcome checks, fallback rate, escalation rate, latency, and cost; sampled human review of conversations; drift checks on understanding accuracy and fraud-estimate calibration. |
| **Abuse and cost** | Spend cap ($5, then rules mode); 40 turns per conversation; 30 sessions per visitor per hour, keyed by the address the hosting proxy saw (the last `X-Forwarded-For` entry), so a forged header cannot reset it. Visitors behind one shared network address share the allowance. | Per-customer rate limits, bot protection, and budget alerts on the cloud account. |
| **Compliance** | A "never explain" rule for compliance holds; nothing internal streamed to the customer; no promises and no requests for secrets, enforced in code and tested. | A legal review of all customer-facing wording in both languages; an audit log of every decision and its sources; a model-risk review of the fraud estimate. |
| **Human side** | A specialist queue that shows structured handoffs. | SLAs by case type and country deadline; integration with the bank's case-management system; feedback from specialists to improve handoffs. |

## 6. Future improvements

- **Validated rules**: fold in the financial specialist's answers on police reports, recurring-charge cancellation, and fee values.
- **Synthetic fee schedule**: explain the bank's own charges against published rules.
- **Richer understanding tests**: real (anonymized) customer messages, multi-intent messages, and adversarial prompts in both languages.
- **Signed transcripts**: a PAdES signature with a bank certificate, so anyone can verify a transcript offline, and a durable register.
- **Proactive "is this really my bank?" check**: before a customer shares a code, the bank's app could confirm whether a contact is genuine.
- **Follow-up stage**: let the customer check the status and deadline of a filed claim, the natural next workflow (`complaint-status-tracker` in the ideation repository).
