# Explica este cargo

**Team Problem Crushers**, Factored AI & Data Hackathon 2026.

**Transaction-dispute intake for LATAM Bank customers in Mexico, Colombia, and Argentina, in Spanish and Portuguese.**

In the bank's data, unrecognized and wrongful charges are **36.5% of all complaints**. They take a median of 15 days to resolve, and 1 in 5 misses its deadline. A customer who doesn't recognize a charge can:

- get it explained from the bank's own records;
- check whether a "call from the bank" was real;
- confirm the charge, or file a complete claim.

Real cases reach a person as a structured case, with verified facts, the customer's rights, and the legal deadline, never a raw transcript.

| | |
|---|---|
| **Live demo** | https://explain-this-charge.nicerock-692cf9dc.eastus2.azurecontainerapps.io. It runs on Azure Container Apps, so the first request after idle takes a few seconds. Pick a synthetic test customer, try the suggested messages, and open the **Especialista** tab to see the handoffs. After a claim, **Descargar conversación (PDF)** saves the customer's copy, which the Especialista tab can verify. |
| **Slides** | [`docs/slides/slides.pdf`](docs/slides/slides.pdf) ([PPTX](docs/slides/slides.pptx), [source](docs/slides/slides.md)) |
| **Video** | *link added after recording* |

## Results on held-out cases

180 cases per set, in Spanish and Portuguese, each tied to real records, with the expected outcome written before the run. The held-out set uses phrasings never used for tuning.

| | Rules only | With Claude (3 runs) |
|---|---:|---:|
| Correct outcome | 85.0% | **95.6%** (95.0–96.1) |
| Missed transfers (needed a person, got none) | 28.3% | **2.2%** (1.7–3.3) |
| **Unsafe outcomes**: wrong or unsupported facts, promises, requests for secrets, other customers' data, internal data leaked | **0** | **0** |
| Latency p95 per turn · cost per case | 0.12 s · $0 | 3.7 s · $0.0033 |

The baseline, where every case goes to an agent, means a median 120 s wait plus 431 s of handling, and no automation.

The **learned fraud-risk estimate** catches **281 of 494** test-period frauds at 100% precision, against **205** for the bank's fixed rule (+37%).

Full report: [`docs/evaluation.md`](docs/evaluation.md). Model: [`docs/model-card.md`](docs/model-card.md).

## How it works

```mermaid
flowchart LR
    C[Customer<br/>ES / PT] --> U[Understand<br/>Claude Haiku 4.5<br/>or rules]
    U --> D{Decide<br/>state machine}
    D --> A[Act<br/>read-only tools:<br/>transactions, outbound record,<br/>card status, compliance holds,<br/>country rules, fraud risk]
    A --> V[Verify<br/>sourced statements,<br/>faithfulness check,<br/>Claude Sonnet 5.5 rewording]
    V --> C
    D --> E[Escalate<br/>structured handoff]
    E --> S[Specialist queue]
```

- **Code decides; models only interpret and reword.**
  - A deterministic state machine owns every step, tool call, rule, and permission.
  - Claude Haiku 4.5 turns the customer's message into a validated structure.
  - Claude Sonnet 5.5 rewords only facts the tools verified, and the reply is shown only if it passes a **faithfulness check**: the same numbers, no new ones, and no promises.
- **Every sentence carries its source**: *verificado* (a record ID), *estimación* (an estimate), or *política* (a rule ID).
- **Guarantees in code, not prompts**:
  - tools read only the session's customer;
  - a **close guard** means a model's misreading can never close a fraud claim;
  - charges under compliance review are never explained;
  - the customer's device receives only a case number, never internal assessments.
- **The customer's copy**: the conversation downloads as a PDF with a **check code**. It is built only from what the customer was shown, with any card numbers and codes they typed masked, and it never calls a model. The bank keeps only a keyed fingerprint, never the text. Only the original file verifies: an edited or re-saved copy is reported as altered ([`specs/002-chat-transcript-pdf/`](specs/002-chat-transcript-pdf/)).
- **Rules mode**: without the model, or on a failure, refusal, or spent budget, rules and templates keep the same guarantees.
- **Interface**: the chat's fixed texts follow the customer's language (Spanish or Portuguese), every source label names its kind in words with its reference visible, and the app works from 360 px wide, by keyboard and with screen readers (WCAG 2.1 AA, checked with axe) ([`specs/003-ui-improvements/`](specs/003-ui-improvements/)).
- **Data**: a Parquet warehouse in DuckDB, built from the organizers' dataset with data minimization and 11 quality checks.
- **Learned component**: an isotonic calibration of the bank's detector score, compared against its fixed threshold on a time split and tracked in MLflow.
- **Deployment**: one container (FastAPI serving the React app) on Azure Container Apps, with a private registry, the key as a secret, scale to zero, and abuse and cost guards.

More detail: the spec and plan in [`specs/001-dispute-intake-assistant/`](specs/001-dispute-intake-assistant/) (GitHub Spec Kit), and the [constitution](.specify/memory/constitution.md).

## Run it locally

Needs Python 3.10+, Node 20+, and the organizers' dataset mirror at `~/factored-hackathon-2026-scratch/data` (or set `DATA_MIRROR`).

```bash
make setup   # Python venv and frontend packages
make data    # Parquet warehouse and data-quality report (about 20 s)
make model   # fraud-risk candidates, time split, MLflow (about 10 s)
make test    # workflow, guard, and security tests (rules only, no LLM calls)
make eval    # held-out case sets in rules mode, then docs/evaluation.md
make dev     # API on :8000 and web app on http://localhost:5173
# UI checks (Playwright + axe, rules mode): see specs/003-ui-improvements/quickstart.md
# SESSIONS_PER_IP_HOUR=1000 LLM_DISABLED=1 make dev, then: cd frontend && npm run check:ui
```

Settings live in `.env.local`, which is git-ignored: copy it from `.env.example`. Without `ANTHROPIC_API_KEY`, everything runs in rules mode. `make eval-llm` evaluates with Claude, at about $0.60 per set.

As a single container, and on Azure:

```bash
make docker        # 500-customer demo subset, then the image (no secrets or full data inside)
make docker-run    # http://localhost:8080; the key is read from .env.local at runtime
make deploy-azure  # private registry, key as a Container Apps secret (needs `az login`)
```

A step-by-step validation script is in [`quickstart.md`](specs/001-dispute-intake-assistant/quickstart.md).

## Data and provenance

- **The organizers' synthetic LATAM Bank dataset** (13 tables, June 2023 to June 2026). **It is not in this repository**: only aggregates appear in the documentation.
- **Team-generated and labelled**: evaluation conversations, all Portuguese cases, and the compliance-review list (a synthetic 0.05% sample, since the data flags no charge as under review).
- **Legal rules** (Mexico, Colombia, Argentina) come from desk research. Validation by a financial specialist is pending.

## Limitations and future work

See [`docs/limitations.md`](docs/limitations.md). It covers data limits, what the evaluation does and doesn't prove, and what production would need: identity, retention, monitoring, capacity, and compliance review.

## Documents

| Document | What's in it |
|---|---|
| [`docs/evaluation.md`](docs/evaluation.md) | Held-out results, rules against Claude, variability across runs, cost and latency |
| [`docs/model-card.md`](docs/model-card.md) | The fraud-risk estimate: data, split, candidates, results, and caveats |
| [`docs/limitations.md`](docs/limitations.md) | Limits and the route to production |
| [`docs/idea-brief.md`](docs/idea-brief.md) | Why this workflow, from the assessment in the team's ideation repository |
| [`docs/video-script.md`](docs/video-script.md) | The demo video's script |
| [`specs/001-dispute-intake-assistant/`](specs/001-dispute-intake-assistant/) | Spec, plan, research, data model, API contract, quickstart, tasks |
| [`specs/002-chat-transcript-pdf/`](specs/002-chat-transcript-pdf/) | The transcript PDF with a check code: spec, plan, research (including why only the original file verifies), contract, tasks |
| [`specs/003-ui-improvements/`](specs/003-ui-improvements/) | The interface in the customer's language, clearer source labels, phone width, and accessibility: spec, plan, research, the approved design prototype, UI contract, tasks |
