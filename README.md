# Explain this charge

**Team Problem Crushers**, Factored AI & Data Hackathon 2026.

An AI customer-service system for one banking workflow: **transaction-dispute intake**. A customer who does not recognize a charge, or thinks it is wrong, gets it explained from the bank's own records. The system also checks whether a "message from the bank" really came from the bank. The customer can then confirm the charge or file a complete claim, and likely fraud reaches a person with a structured handoff. The system works in Spanish and Portuguese, for customers in Mexico, Colombia, and Argentina.

> Status: build starting (2026-09-30). Submissions close 2026-10-05, midnight Colombia time.

## Run it locally

Needs Python 3.10+, Node 20+, and the organizers' dataset mirror at `~/factored-hackathon-2026-scratch/data` (or set `DATA_MIRROR`).

```bash
make setup   # Python venv + frontend packages
make data    # build the Parquet warehouse and data-quality report (about 20 s)
make model   # train the fraud risk estimate (MLflow), about 10 s
make eval    # build held-out case sets, evaluate in rules mode, write docs/evaluation.md
make test    # workflow tests, one per required case (rules only, no LLM calls)
make dev     # API on :8000 and web app on http://localhost:5173
```

The demo also runs as a single container: API, built frontend, a 500-customer demo subset, and the fraud model.

```bash
make docker       # builds the demo subset, then the image (no secrets or full data inside)
make docker-run   # http://localhost:8080; the key is read from .env.local at runtime
```

Settings live in `.env.local` (git-ignored; copy `.env.example`). Without `ANTHROPIC_API_KEY` the assistant runs in rules mode, understanding with rules and answering from templates. With the key set, Claude Haiku 4.5 understands requests and Claude Sonnet 5.5 phrases answers, and every rewording is checked against the verified facts before it is shown.

## How it works

The workflow runs `understand -> decide -> act -> verify -> escalate` as an explicit state machine (`backend/app/workflow/engine.py`).

- **Understand.** Models are used here and when rewording, and nowhere else.
- **Decide and act.** Transaction lookups, the outbound-record check, card status, and country rules are deterministic, read-only tools (`backend/app/tools/banking.py`, `backend/app/policy/rules.py`). They take the session's customer, never an ID typed in the chat.
- **Verify.** Every statement to the customer is tagged *known* (with its source record), *guessed*, or *rule*.
- **Escalate.** Cases that need a person become structured handoffs in the specialist view.

## Documents

- [`docs/idea-brief.md`](docs/idea-brief.md): the problem, the workflow, the required cases, the metrics, and the data limits.
- [`docs/evaluation.md`](docs/evaluation.md): the held-out evaluation, rules against Claude, with the organizers' outcome measures.
- [`docs/model-card.md`](docs/model-card.md): the fraud risk estimate, the learned component, against the existing detector.
- [`docs/build-plan.md`](docs/build-plan.md): architecture, open team decisions, the day plan, the test cases, and the security rules.

## Data

The organizers' synthetic LATAM Bank dataset (13 tables, June 2023 to June 2026). **It is not in this repository and must never be committed.** Test conversations, Portuguese cases, and any fee schedule are team-generated or synthetic, and are labelled as such.

## Limitations, caveats, and future work

To be written as the build progresses. The data's known limits are listed in [`docs/idea-brief.md`](docs/idea-brief.md#what-the-data-cannot-do-report-these-honestly).
