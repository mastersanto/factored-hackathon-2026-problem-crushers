# Research: Explain This Charge

The decisions behind the architecture as built. Most were made and tested between 2026-09-30 and now; each records what else was considered. One decision, the deployment target, was open when the plan was written and is resolved here.

## 1. Workflow control: explicit state machine, not an agent loop

- **Decision**: a hand-written state machine drives the workflow: understand → decide → act → verify → escalate.
  - Stages: start, choose, confirm, statement, contact_shared, closed.
  - The model never chooses tools or next steps.
- **Rationale**:
  - The workflow is known in advance, and each transition must be auditable.
  - The organizers require permissions and policy enforced outside model prose.
  - Every path is testable without a model.
- **Alternatives considered**:
  - An agent with tool calling: flexible, but it makes permissions and "never promise" depend on the prompt, and it is harder to evaluate.
  - A graph-orchestration framework: adds a dependency without adding control.

## 2. Language models at the edges only

- **Decision**:
  - **Understanding**: Claude Haiku 4.5 extracts intent, amount, merchant, date, channel, and whether a secret was asked for or shared. It uses structured output validated against a schema; merchants outside the data are dropped.
  - **Phrasing**: Claude Sonnet 5.5 rewords only statements the tools verified, at low effort, with the server-side refusal fallback enabled. The Anthropic Python SDK is used throughout.
  - **Faithfulness check**: a rewording is shown only if it keeps every number, adds none, and makes no promise.
  - **Deterministic fallback**: rules and templates replace both models on any failure.
- **Rationale**:
  - Held-out evaluation shows the rules generalize to new data, but not to new wording: 79.2% correct and 47.9% missed transfers on held-out phrasings.
  - With Haiku, the same set reaches 95.2% correct and 2.1% missed transfers, at $0.0033 per case.
  - Sonnet makes replies natural, and the check keeps it honest.
- **Alternatives considered**:
  - One model for both steps: simpler, but costlier per turn or weaker in wording.
  - Model-only understanding: the first evaluation run showed three fraud claims closed on a model misreading.

## 3. Deterministic close guard

- **Decision**: at the confirmation step, a negation detected by the rules always files the claim. Closing as "it was mine" requires the rules and the model to agree; otherwise the assistant asks again.
- **Rationale**: the first model-assisted run closed 3 of 168 fraud claims without a person, because "no, no lo reconozco" was misread. After the guard, unsafe outcomes are 0 of 168 on both test sets. The cost is some re-asking on casual affirmatives: correct outcomes fell from 98.2% to 95.2% on held-out phrasings.
- **Alternatives considered**:
  - Prompt changes alone: they do not guarantee the property.
  - Always re-asking: safe, but tedious for clear answers.

## 4. Data: Parquet warehouse over DuckDB, minimized at build time

- **Decision**: a build step turns the organizers' CSV mirror into five Parquet tables: customers, products, transactions, outbound contacts, and complaints.
  - Only the fields the workflow needs are kept; identity documents, contact details, addresses, income, and credit scores are dropped.
  - Card and account numbers keep only their last four digits.
  - The two spellings of Mexico are normalized.
  - The data is queried read-only through DuckDB.
- **Rationale**: 4.4 million transactions build in about 20 seconds, and queries run in milliseconds. There is no database server to run or secure. Minimization makes data protection structural rather than procedural.
- **Alternatives considered**:
  - Querying the CSV mirror directly: slow.
  - PostgreSQL: more to operate, with no benefit at this scale.

## 5. Data-quality checks as expectations

- **Decision**: every build runs nine checks and records them in `quality_report.json`:
  - unique transaction IDs;
  - transactions linked to products;
  - no missing amounts or dates;
  - normalized country spelling;
  - the known quirks: no MXN, 24 merchants, a pending share of about 2%, a fraud rate of about 0.1%;
  - the outbound record present.
- **Rationale**: several fields in the synthetic data are random or odd. Stating them as expectations turns a silent change in the organizers' data into a visible failure.

## 6. Fraud risk: calibrated existing score, not a behavioural model

- **Decision**: an isotonic calibration of the dataset's `fraud_score` (with a missing-score flag), chosen on validation, with the alert threshold set on validation at precision of at least 0.9.
  - The split is by time: train before October 2025, validate October 2025 to January 2026, test from February 2026.
  - All four candidates (including the rule baseline) are tracked in MLflow with a SQLite backend.
- **Rationale**:
  - The label is random with respect to every behavioural feature: a behavioural-only model scores PR-AUC 0.001, which is chance.
  - The calibrated score catches 281 of 494 test frauds at 100% precision, against 205 for the fixed rule `>= 50`.
  - Adding behavioural features to the score makes it worse.
- **Alternatives considered**: gradient boosting on the score plus behavioural features (0.42 PR-AUC, 83% precision) and on behavioural features alone. The leakage caveat is documented in `docs/model-card.md`.

## 7. Streaming protocol: server-sent events with our own event types

- **Decision**: each chat turn is a POST that streams server-sent events. The event types are:
  - step: the workflow trace;
  - message: text plus sourced statements;
  - candidates;
  - verdict;
  - handoff;
  - error;
  - done: the stage and quick replies.

  The React client parses them with a small hook.
- **Rationale**: replies are structured, not plain chat text. The trace is part of the demo, and a small parser avoids a pre-1.0 dependency.
- **Alternatives considered**: TanStack AI's chat client, at version 0.63 with breaking changes between releases and its value on the TypeScript server side. WebSockets are more than a request/response chat needs.

## 8. Frontend: React, Vite, TypeScript, TanStack Query

- **Decision**: a single-page app with two views, the customer chat and the specialist queue. The queue is polled every 3 seconds.
- **Rationale**: this was the owner's choice (React). TanStack Query covers data fetching and polling, and Vite gives a fast dev server with an API proxy.

## 9. Evaluation harness

- **Decision**:
  - **Case generator**: 14 categories × 2 languages × 6 cases. Every case is tied to real records, and its expected outcome is written before the run.
  - **Sets**: dev (seed 7), test with familiar phrasings (seed 8), and test with held-out phrasings (seed 9).
  - **Runner**: drives the real engine, with a simulated customer who picks the right option from a list.
  - **Grader**: computes the organizers' outcome measures and eight unsafe-outcome checks.
  - **Report**: writes aggregates only.
- **Rationale**: the organizers require baseline-versus-system comparisons on the same held-out workload, by language and segment. Separate held-out phrasings keep the numbers honest after the rules were tuned.

## 10. Deployment target (resolved)

- **Constraints**:
  - The repository is public, so the demo data must never be committed or pushed anywhere public.
  - The Anthropic key must live in the host's secret store.
  - The tool does not need to run 24/7.
  - One person operates it.
- **Decision (updated 2026-09-30, the owner's choice): Azure Container Apps**, one of the hosts the organizers suggest (Azure, AWS, Snowflake, Databricks). The design below is unchanged. Only the host moves from Fly.io to Azure:
  - the image is built locally and pushed to a private Azure Container Registry;
  - the app scales to zero with at most one replica;
  - the key is stored as a Container Apps secret;
  - `scripts/deploy-azure.sh` runs all of it.

  Before the link is public, three abuse and cost guards cap exposure: a total model-spend cap (`MAX_LLM_USD`, default $5), after which the app runs in rules mode; 40 turns per conversation; and 30 new sessions per visitor per hour.
- **Original decision**: a single container serves the API and the built frontend as static files.
  - The container holds a demo subset of the warehouse (`python -m app.data.build --customers 500`), built locally.
  - It is built and deployed from the local working copy, where the git-ignored data is available, with a CLI that uploads the build context privately. Fly.io (`fly deploy`) fits.
  - The image goes to the host's private registry. The key is set with the host's secret command.
- **Rationale**:
  - The data never passes through git or a public registry.
  - One container keeps setup reproducible.
  - It can scale to zero when idle.
- **Alternatives considered**:
  - Hosts that build from a git repository (Render, Railway from GitHub): the data would have to be in the repository, which is ruled out.
  - Azure Container Apps or AWS App Runner (suggested by the organizers): workable with a private registry, but slower to set up alone.
  - Hugging Face Spaces: public by default.
- **Open item**: this needs the owner's Fly.io account (or another host with a private local build). It is tracked in tasks.
