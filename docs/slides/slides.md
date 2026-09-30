---
marp: true
theme: default
paginate: true
size: 16:9
style: |
  section { font-size: 24px; padding: 48px 64px; }
  h1 { color: #0b6e79; font-size: 40px; }
  h2 { color: #0b6e79; }
  table { font-size: 20px; }
  .small { font-size: 16px; color: #52606d; }
  .big { font-size: 56px; font-weight: 700; color: #0b6e79; }
  section.dense { font-size: 20px; padding: 36px 56px; }
  section.dense li { margin: 2px 0; }
---

# Explica este cargo

**Transaction-dispute intake for LATAM Bank**: Spanish and Portuguese, for customers in Mexico, Colombia, and Argentina.

Team **Problem Crushers**, Factored AI & Data Hackathon 2026

- **Live demo**: https://explain-this-charge.nicerock-692cf9dc.eastus2.azurecontainerapps.io
- **Code**: github.com/mastersanto/factored-hackathon-2026-problem-crushers

<p class="small">All data is the organizers' synthetic dataset. Conversations, Portuguese cases, and the compliance-review list are team-generated and labelled.</p>

---

## 1. The problem, from the bank's own data

- **Unrecognized and wrongful charges are 36.5% of all complaints**: 24,491 cases.
- They take a **median of 15-16 days** to resolve, and **about 20% miss their deadline**.
- Complaint contacts are resolved at first contact only **43.6%** of the time.
- **Satisfaction follows resolution, not speed**: CSAT is 3.0 when resolved at first contact and 2.0 when not.
- Scam calls pushing customers to "confirm a charge" make it worse. Outside the data, unrecognized transactions were 39.8% of Colombia's financial-regulator complaints in 2025.

**Goal**: resolve the doubt correctly on first contact, and when a person is needed, give them a complete, verified case.

---

## 2. The workflow: understand → decide → act → verify → escalate

| The customer says… | The assistant… |
|---|---|
| "No reconozco un cargo de 1.250 en Uber" | finds it in *their own* records and explains merchant, amount, date, place, channel, and card, each sentence **verified with its record** |
| "Sí, fui yo" | closes the case, with no person needed |
| "No fui yo" | collects what happened, files **one structured handoff**, and states the customer's **rights and legal deadline** (Mexico, Colombia, Argentina), **never a promised outcome** |
| "Me llamaron del banco y me pidieron un código" | checks the bank's outbound record: **real contact / no record / scam**. If a code was shared, the case is **urgent**. |
| vague, out of scope, another customer's data, prompt injection | asks a question, abstains, or refuses |

Required cases covered: **normal** (explain and close), **ambiguous** (clarify), **human-required** (claim, fraud, compliance hold).

---

<!-- _class: dense -->

## 3. Architecture: code decides, models interpret

- **A deterministic state machine** owns every step, tool, rule, and permission. **Claude Haiku 4.5** only interprets messages; **Claude Sonnet 5.5** only rewords verified facts.
- **Guarantees are enforced in code, not prompts**:
  - tools read only the **session's** customer;
  - a **faithfulness check** discards rewordings that change or add numbers, or promise anything;
  - a **close guard** means a model can never close a fraud claim on its own;
  - **compliance holds** are never explained, and the customer's device gets only a case number.
- **Rules mode**: on a model failure, a refusal, or a spent budget, the same guarantees hold without the model.
- **Data**: a minimized Parquet warehouse in DuckDB, with identity data dropped, card numbers cut to the last 4 digits, and 11 quality checks.
- **Learned component**: a calibrated fraud-risk estimate against the bank's fixed threshold, on a time split, tracked in MLflow.
- **Deployment**: one container on **Azure Container Apps**, with a private registry, the key as a secret, and scale to zero.

---

## 4. Results on held-out cases

180 cases per set: 15 categories × ES/PT, each tied to real records, with the expected outcome written before the run. The held-out set uses **phrasings never used for tuning**.

| Held-out phrasings | Rules only | **With Claude** |
|---|---:|---:|
| Correct outcome | 85.0% | **95.6% (3 runs: 95.0–96.1)** |
| Missed transfers (needed a person) | 28.3% | **2.2% (1.7–3.3)** |
| Unnecessary transfers | 0% | 0% |
| **Unsafe outcomes** | **0** | **0** |
| p95 latency per turn · cost per case | 0.12 s · $0 | 3.7 s · $0.0033 |

- **Baseline** (every case to an agent): 0% automation, a median 120 s wait plus 431 s of handling.
- **Fraud estimate**: **281 of 494** test frauds caught at 100% precision, against **205** for the fixed rule (+37%).
- **The evaluation changed the system**: it found 3 fraud claims closed on a model misreading (now guarded), a Portuguese detection gap, and internal case data streamed to the browser. All three were fixed, with tests.

---

## 5. Limits, and what production needs

- **Synthetic data**: several fields are random, there is no MXN, and only 24 merchants. The fraud score may encode the label. Conversations and Portuguese are team-generated.
- **Rules from desk research**: the financial specialist's validation is pending.
- **Production needs**:
  - the bank's identity service, and authentication for the specialist queue;
  - live read-only services behind the same tools;
  - a retention policy and legal review of the wording, in each country;
  - several replicas and a handoff queue;
  - monitoring of the unsafe-outcome checks, fallback rate, latency, and cost;
  - fairness and model-risk review.

**Details**: `docs/limitations.md`, `docs/evaluation.md`, and `docs/model-card.md` in the repository.
