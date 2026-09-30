# Implementation Plan: Explain This Charge (transaction-dispute intake)

**Branch**: `main` (the feature folder is `001-dispute-intake-assistant`) | **Date**: 2026-09-30 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/001-dispute-intake-assistant/spec.md`

This plan records the architecture **as built**. It is not a redesign. Decisions and the alternatives considered are in [research.md](research.md).

## Summary

The assistant handles transaction-dispute intake for LATAM Bank customers in Mexico, Colombia, and Argentina, in Spanish and Portuguese. It:

- explains a disputed charge from the bank's own records, with every statement sourced;
- checks claimed bank contacts against the outbound record;
- files complete claims to a specialist through a structured handoff;
- tells customers their rights, without ever promising an outcome.

The technical approach is a deterministic core with the language model at the edges:

- **Code** owns the workflow (understand → decide → act → verify → escalate), the read-only tools scoped to the session customer, the country rules, and a close guard.
- **Claude Haiku 4.5** interprets messages.
- **Claude Sonnet 5.5** rewords verified facts, and a faithfulness check decides whether that rewording is shown.
- **A calibrated fraud-risk estimate** sets the handoff's priority.
- **A held-out evaluation harness** measures the organizers' outcome measures against the all-to-agent baseline.

## Technical Context

- **Language/Version**: Python 3.10 (backend); TypeScript ~6.0 with React 19 (frontend).
- **Primary Dependencies**:
  - backend: FastAPI with uvicorn, DuckDB, Pydantic 2, the Anthropic Python SDK (1.9 or later), scikit-learn, joblib, MLflow (development);
  - frontend: Vite 8 and TanStack Query 5.
- **Storage**:
  - a Parquet warehouse (5 tables), built from the organizers' dataset mirror outside the repository and git-ignored;
  - handoffs as JSON lines;
  - MLflow runs in SQLite.

  All of it lives under the git-ignored `backend/data/`.
- **Testing**: pytest with 18 workflow, guard, and security tests, plus the evaluation harness (`app.eval`) on 3 × 168 held-out cases.
- **Target Platform**:
  - local development on Linux or WSL (API on :8000, Vite on :5173);
  - the demo as a single Linux container on a host that builds privately from the local working copy (research §10).
- **Project Type**: web application (a Python API streaming server-sent events, and a React single-page app).
- **Performance Goals**: p95 under 5 s per turn with the models, and under 150 ms in rules mode. Measured: p95 3.7 s and 116 ms.
- **Constraints**:
  - no data or secrets in the public repository;
  - only a turn's minimal fields go to a model;
  - under $0.01 per case (measured: $0.0033);
  - a demo subset for deployment (500 customers).
- **Scale/Scope**:
  - one workflow;
  - 4.4 million transactions and 150,000 customers locally;
  - demo traffic only (judges and the team); the deployment does not need to run 24/7.

## Constitution Check

*GATE: must pass before Phase 0 research and be re-checked after Phase 1 design.*

| Principle | How the design meets it | Status |
|-----------|-------------------------|--------|
| **I. Deterministic Core, AI at the Edges** | The state machine in the engine decides every step. Models only return a validated `Understanding` or reworded text. Rules and templates run when no key is set or on any failure. | Pass |
| **II. Permissions in the Tool Layer** | Every tool takes the session's `customer_id`. `get_transaction` and `card_status` raise `Unauthorized` for other owners. Customer IDs typed in chat are flagged and refused. Sessions expire after 30 minutes. | Pass |
| **III. Verified Facts Only** | `Statement(basis, source)` on every sentence; known statements without a source are removed. The faithfulness check compares numbers and scans for promises. The close guard applies at confirmation. AML-review charges are never explained, but this is not exercised by the data (spec, Current Status). | Pass, with one item to demonstrate |
| **IV. No Data or Secrets in the Repository** | `.gitignore` covers `backend/data/`, data file types, and `.env*`. The build step minimizes data. The secret scan runs before every commit. Evaluation cases and results stay git-ignored; only aggregates reach `docs/`. | Pass |
| **V. Evaluate Before Claiming** | Dev and test sets use separate seeds, plus held-out phrasings. The organizers' measures are reported with denominators, by language and segment. The fraud model is compared against its baseline on a time split and tracked in MLflow. The report includes a record of what the evaluation changed. | Pass (repeated model runs still to do) |

Re-check after design: no violations. See Complexity Tracking for the one deliberate addition.

## Project Structure

### Documentation (this feature)

```text
specs/001-dispute-intake-assistant/
├── spec.md              # what the system does, and its current status
├── plan.md              # this file
├── research.md          # decisions, rationale, alternatives
├── data-model.md        # entities, fields, state machine
├── quickstart.md        # how to run and validate end to end
├── contracts/
│   └── http-api.md      # HTTP endpoints and the server-sent event protocol
├── checklists/
│   └── requirements.md  # spec quality checklist
└── tasks.md             # remaining work (/speckit-tasks)
```

### Source Code (repository root)

```text
backend/
├── app/
│   ├── config.py            # settings from the environment and .env.local
│   ├── data/                # build.py (mirror -> Parquet), quality.py (checks), store.py (DuckDB)
│   ├── tools/banking.py     # read-only tools scoped to the session customer
│   ├── policy/rules.py      # country rules with ids, rights, answer deadlines
│   ├── workflow/            # engine.py (state machine, guards, handoff), understanding.py (rules), messages.py (ES/PT)
│   ├── llm/claude.py        # Haiku understanding, Sonnet phrasing, faithfulness check, usage and cost log
│   ├── ml/fraud.py          # candidates, time split, MLflow, FraudRisk inference
│   ├── eval/                # cases.py (generator), run.py (runner and grader), report.py (docs/evaluation.md)
│   └── api/main.py          # FastAPI: health, demo login, session, chat (server-sent events), handoffs, metrics
├── tests/                   # test_workflow.py (required cases and security), test_guards.py (misreading-model guards)
└── data/                    # git-ignored: warehouse/, models/, eval/, mlflow.db, handoffs.jsonl

frontend/
└── src/                     # api.ts (types and the server-sent events parser), useChat.ts, App.tsx (demo login), Chat.tsx, AgentQueue.tsx

docs/                        # idea-brief, build-plan, model-card, evaluation (aggregates only)
Makefile                     # setup, data, model, eval, eval-llm, test, api, web, dev
```

**Structure Decision**: a web application with separate `backend/` and `frontend/` folders.

- In development, the Vite dev server proxies `/api` to the backend.
- In deployment, one container serves both: the frontend is built to static files and served by the API (to be done, see tasks).

## Complexity Tracking

| Addition | Why needed | Simpler alternative rejected because |
|----------|------------|--------------------------------------|
| Two model roles (understanding and phrasing) plus a rules fallback | Understanding must generalize to unseen wording (+16 points on held-out phrasings). Phrasing must read naturally in two languages. Both must be optional. | A single model for both steps costs more per turn or reads worse. Having no model misses 48% of the transfers needed on held-out phrasings. |
| MLflow as a development dependency | The organizers judge "model selection, optimization, and tracking". | Logging runs by hand is not a tracking system judges recognize. It is kept out of the runtime dependencies. |
