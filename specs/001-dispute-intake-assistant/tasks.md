---
description: "Remaining work for the dispute intake assistant, with already-built work recorded for traceability"
---

# Tasks: Explain This Charge (transaction-dispute intake)

**Input**: design documents from `specs/001-dispute-intake-assistant/` (plan.md, spec.md, research.md, data-model.md, contracts/http-api.md, quickstart.md).

**Deadline**: 2026-10-05, midnight Colombia time (UTC-5). Treat 2026-10-05 as a buffer day.

**Tests**: the constitution requires a test for every safety behaviour that fails without it, so safety tasks include tests.

**Paths**: this is a web application. Backend code is in `backend/app/` and its tests in `backend/tests/`; the frontend is in `frontend/src/`; documentation is in `docs/`.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: can run in parallel (different files, no dependency on an unfinished task).
- **[Story]**: the user story from spec.md (US1-US6).

---

## Phase 0: Already built (for traceability)

These are done as of 2026-09-30 and verified by `make test` and `make eval` (see spec.md, Current Status).

- [X] T001 Scaffold the repository, docs, and Makefile in `Makefile`, `README.md`, and `CLAUDE.md`
- [X] T002 Build the Parquet warehouse with data minimization in `backend/app/data/build.py`
- [X] T003 [P] Add nine data-quality checks in `backend/app/data/quality.py`
- [X] T004 [P] Add the read-only DuckDB store in `backend/app/data/store.py`
- [X] T005 Add read-only tools scoped to the session customer in `backend/app/tools/banking.py`
- [X] T006 [P] Add country rules with ids, rights, and deadlines in `backend/app/policy/rules.py`
- [X] T007 [US1] Find and explain a charge, with sourced statements, disambiguation, and the pending state, in `backend/app/workflow/engine.py`
- [X] T008 [US1] Add rule-based understanding (amount formats, named and relative dates, ES/PT) in `backend/app/workflow/understanding.py`
- [X] T009 [US2] Add claim intake, the structured handoff, rights, and the no-promise wording in `backend/app/workflow/engine.py` and `backend/app/workflow/messages.py`
- [X] T010 [US3] Add the outbound-record check with three verdicts and urgent escalation in `backend/app/tools/banking.py` and `backend/app/workflow/engine.py`
- [X] T011 [US4] Add Portuguese templates, language detection, and quick replies in `backend/app/workflow/messages.py` and `backend/app/workflow/understanding.py`
- [X] T012 [US5] Add refusal for other customers' data, abstention, clarification, the safe fallback on outages, and session expiry in `backend/app/workflow/engine.py`
- [X] T013 [US5] Add the deterministic close guard and the misreading-model tests in `backend/app/workflow/engine.py` and `backend/tests/test_guards.py`
- [X] T014 Integrate Claude Haiku 4.5 understanding and Sonnet 5.5 phrasing with a faithfulness check in `backend/app/llm/claude.py`
- [X] T015 Add the calibrated fraud-risk estimate with MLflow tracking and a model card in `backend/app/ml/fraud.py` and `docs/model-card.md`
- [X] T016 [US6] Add the FastAPI endpoints and the chat stream (server-sent events) in `backend/app/api/main.py`
- [X] T017 [US6] Add the React chat with statement badges, trace, and quick replies, and the specialist queue, in `frontend/src/`
- [X] T018 Add the evaluation harness (generator, runner and grader, report) and write `docs/evaluation.md` from `backend/app/eval/`
- [X] T019 Ratify the constitution and write the spec, plan, research, data model, contract, and quickstart in `.specify/memory/constitution.md` and `specs/001-dispute-intake-assistant/`

---

## Phase 1: Setup for deployment

**Purpose**: package the system as a single container that serves the API and the built frontend.

- [X] T020 Serve the built frontend from the API: mount `frontend/dist` as static files at `/`, keeping `/api/*` routes first, in `backend/app/api/main.py`. Skip the mount when the folder is missing (development).
- [X] T021 [P] Make the demo-subset build write to its own folder: `python -m app.data.build --customers 500 --out backend/data/demo-warehouse`. Check that `quality_report.json` has `checks_failed: 0`, and that the demo customers still cover every path (at least one each for pending, flagged fraud score, México debit within 48 hours, and a recent SMS or WhatsApp contact). Record the check in `backend/app/data/build.py`, and adjust the selection if a path is missing.
- [X] T022 [P] Write a multi-stage `Dockerfile`:
  - a Node stage builds `frontend/`;
  - a Python 3.10 slim stage installs `backend` (runtime dependencies only, no MLflow), copies `backend/data/demo-warehouse` to `/app/data/warehouse` and `backend/data/models/fraud.joblib`, and runs uvicorn on port 8080 with `WAREHOUSE_DIR=/app/data/warehouse`.
- [X] T023 [P] Write `.dockerignore` excluding `backend/.venv`, `frontend/node_modules`, `backend/data/warehouse` (the full warehouse), `backend/data/eval`, `backend/data/mlartifacts`, `backend/data/mlflow.db`, and `.env*`. Keep only the demo warehouse and the model.
- [X] T024 Add `make demo-data` and `make docker` targets, and a local run command (`docker run -p 8080:8080 --env-file .env.local …`), to `Makefile`. Verify the container on http://localhost:8080 with the quickstart's demo script.

---

## Phase 2: Deployment (blocks the submission link)

**Purpose**: a public URL for the tool, with the data and key kept private (research §10).

- [ ] T025 Get the owner's hosting account (Fly.io proposed) and a signed-in CLI. The owner runs the sign-in step (`! fly auth login`). Record the decision in `docs/build-plan.md`.
- [ ] T026 Create the app config: `internal_port 8080`, scale to zero when idle, one small machine, and region `bog` (or the nearest available), in `fly.toml`.
- [ ] T027 Set the key through the host's secret store (`fly secrets set ANTHROPIC_API_KEY=…`, run by the owner), never in files. Document the step, without the value, in `README.md`.
- [ ] T028 Deploy from the local working copy (`fly deploy`), so the git-ignored demo data goes only to the host's private registry. Then check `/api/health` returns `llm_enabled: true`.
- [ ] T029 Run the quickstart demo script against the public URL and fix anything that differs from local. Record the URL in `README.md`.

---

## Phase 3: User Story 5 - Stay safe (Priority: P1)

**Goal**: demonstrate FR-018 (charges under anti-money-laundering review are never explained), which the supplied data cannot exercise.

**Independent Test**: ask about a charge on the synthetic review list. The assistant states no facts about it, says a specialist will review it, and creates a handoff of type `compliance_review` that shows the customer no reason.

- [X] T030 [US5] Write the failing test first: a transaction on the review list produces no `known` statement about it, no reason given to the customer, and one `compliance_review` handoff, in `backend/tests/test_guards.py`.
- [X] T031 [US5] Add a synthetic compliance-review list, labelled synthetic: a seeded sample of 0.05% of transactions written to `compliance_reviews.parquet` by `backend/app/data/build.py`. Add a check to `backend/app/data/quality.py`.
- [X] T032 [US5] Add a `under_compliance_review(store, customer_id, transaction_id)` tool in `backend/app/tools/banking.py`. Before explaining a charge, `backend/app/workflow/engine.py` checks it and, if the charge is under review, emits the neutral message plus the handoff instead. Add the ES/PT wording to `backend/app/workflow/messages.py`.
- [X] T033 [US5] Add a `compliance_review` category to the evaluation cases in `backend/app/eval/cases.py`, with a grader check in `backend/app/eval/run.py`. Re-run `make eval` and confirm 0 unsafe outcomes.

---

## Phase 4: User Story 2 - Claims with validated rules (Priority: P1)

**Goal**: replace desk-research assumptions with the financial specialist's validated rules when they arrive.

**Independent Test**: a claim in each country shows rights and deadlines that match the specialist's answers.

- [ ] T034 [US2] When the specialist's answers arrive, record them in the ideation repository with `/review-idea` (in `~/personal/factored-idea`). Then update the rule texts and ids in `backend/app/policy/rules.py`. This is blocked on external input; skip it if nothing arrives by 2026-10-04.
- [ ] T035 [US2] If a police report turns out to be required in a country, add it to the handoff's open questions for that country only, in `backend/app/workflow/engine.py`. Keep the rule that a report never blocks taking the claim.

---

## Phase 5: Measurement

**Purpose**: report run-to-run variability, as the organizers require.

- [ ] T036 [P] Run `python -m app.eval.run --mode llm --cases test-heldout --repeats 3` (about $1.70). Extend `backend/app/eval/report.py` to report the mean and range of the main measures across repeats, and regenerate `docs/evaluation.md`.
- [ ] T037 [P] Add a short cost and latency note: tokens per turn by model, and what would change with prompt caching or at lower effort, to `docs/evaluation.md`.

---

## Phase 6: Polish and submission

- [ ] T038 [P] Write the limitations and future-work notes in `docs/limitations.md`, and link them from `README.md`. Cover:
  - synthetic data quirks: random fields, no MXN, 24 merchants;
  - team-generated conversations and Portuguese;
  - the fraud-score leakage caveat;
  - rules awaiting validation;
  - the outbound record lacks alerts and collections;
  - no real identity service;
  - demo-scale deployment;
  - what production would need (authentication, audit log retention, monitoring, fairness review, human-in-the-loop SLAs).
- [ ] T039 [P] Polish `README.md`: a one-paragraph pitch, a screenshot, the architecture diagram (understand → decide → act → verify → escalate), results in three numbers, the deployed link, and how to reproduce.
- [ ] T040 [P] Write the 4-6 slide deck with sources in `docs/slides/`:
  1. the problem, from the data;
  2. the workflow and its guarantees;
  3. the architecture (where AI and where code, and why);
  4. results, rules versus Claude, and the fraud model;
  5. limitations and what production needs.
- [ ] T041 [P] Write the three-minute video script and shot list in `docs/video-script.md`. It follows the quickstart demo (normal case, claim with handoff, fake contact, Portuguese, a safety refusal) and closes with the key architectural decisions.
- [ ] T042 Record the video (the owner) and add its link to `README.md`.
- [ ] T043 Run the final checks and record them in `docs/submission-checklist.md`:
  - `make test`;
  - the frontend build;
  - the secret scan over the full history (`git log -p --all` against the local patterns file and the bucket name);
  - no data files tracked (`git ls-files | grep -E '\.(csv|parquet|jsonl|joblib|db)$'` is empty);
  - the public repository created by the owner and pushed;
  - the deployed URL, slides, and video links in `README.md`.
- [ ] T044 Submit the repository link, deployed URL, slides, and video through the organizers' form before 2026-10-05, 23:59 Colombia time (the owner).

---

## Dependencies and execution order

- **Phase 1 → Phase 2**: deployment needs the container.
- **Phase 3, Phase 5, T038, T040, and T041** are independent of deployment and can run alongside Phases 1-2.
- **Phase 4** is blocked on the specialist's answers. It does not block the submission.
- **T039, T042, T043, and T044** need the deployed URL (T029). T044 is last.

**Suggested order by day**:

| Day | Work |
|-----|------|
| 10-01 | T020-T024, T030-T033 |
| 10-02 | T025-T029, T036-T037 |
| 10-03 | T038-T041 |
| 10-04 | T042, T043, T034-T035 if the answers arrived |
| 10-05 | T044, buffer |

## Parallel examples

- In Phase 1, T021, T022, and T023 touch different files and can be written together, then verified by T024.
- T036 (a paid evaluation run in the background) can run while T038 and T040 are written.

## Implementation strategy

- **Minimum viable submission**: Phases 1-2 (a deployed link) plus T038, T040, T041, T042, T043, and T044. The system is already feature-complete for the required cases.
- **Then add, in order**:
  1. Phase 3 (FR-018 demonstrated);
  2. Phase 5 (variability);
  3. Phase 4 (validated rules), if time and input allow.
- **After every change**: pass `make test`, the frontend build, and the secret scan (constitution, quality gates). Workflow changes also re-run `make eval`.
