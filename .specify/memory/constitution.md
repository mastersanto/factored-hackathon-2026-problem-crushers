<!--
Sync impact report (1.1.0 -> 1.2.0, MINOR: Development Workflow expanded)
- Development Workflow: changes reach main only through a pull request with passing GitHub checks; each deployment is tagged and released; published history is never rewritten (specs/008).
- Templates: no change. CLAUDE.md "Collaboration", README.md, and CONTRIBUTING.md updated.
-->
<!--
Sync impact report (1.0.0 -> 1.1.0, MINOR: a supported language added, Principles I and III expanded)
- Hackathon Constraints: English added as a supported language and as the base language.
- Principle I: models may also translate the customer's words for display (marked); understanding never goes through a translation.
- Principle III: the faithfulness check covers every supported language; the safety checks run in code on the original words.
- Templates: plan, spec, and tasks templates need no change. CLAUDE.md updated. README.md describes what is built and changes when feature 004 ships.
-->
# Explain This Charge Constitution

## Core Principles

### I. Deterministic Core, AI at the Edges

- **Code owns every decision in the workflow**: understand → decide → act → verify → escalate.
  - That covers finding transactions, checking the outbound record, applying country rules, computing deadlines, choosing the next step, and escalating.
  - This logic is explicit, readable code, not model reasoning.
- **Models are used only to interpret the customer's message, to reword facts the tools already verified, and to translate the customer's own words for display.**
  - Understanding: Claude Haiku 4.5. Phrasing: Claude Sonnet 5.5.
  - Understanding goes straight from the customer's language to the common, language-neutral form (English names), never through a model's translation of the customer's text.
  - A translation of the customer's words is always marked as one, and the original words stay the record.
  - A model MUST NOT pick tools, compute amounts or dates, or decide an outcome.
- **The system MUST keep working safely without any model**: rules and templates take over on any model failure, refusal, or missing credentials.

Rationale: the organizers score controlled automation and technical rationale. Deterministic steps can be tested, audited, and explained, and they fail predictably.

### II. Permissions in the Tool Layer

- **Every data-reading tool takes the session's customer.** A customer ID or reference found in chat text never selects whose data is read.
- **Reaching another customer's data MUST raise an authorization error**, and the refusal is logged as a security flag.
- **Identity comes from a trusted session** (in the demo, a login standing in for an identity service), never from a national ID or customer number typed by the customer.
- **Sessions expire**, and an expired session gets no data.

Rationale: the problem statement requires permissions enforced in code, not in model prose. Prompt injection must be unable to widen access.

### III. Verified Facts Only (Safety over Autonomy)

- **Every statement shown to the customer MUST carry a basis and a source**:
  - **known**: from a record, citing its ID;
  - **guessed**: an estimate, labelled as such;
  - **rule**: a policy or legal rule, citing its ID.
- **A known statement without a source is removed before it reaches the customer.**
- **A model's rewording is shown only if it passes a faithfulness check**: the same numbers, no new ones, and no promises, in every supported language. Otherwise the template text is used.
- **The safety checks run in code on the customer's original words**, in every supported language: requests for codes, PINs, or passwords; references to another customer; attempts to override the instructions; and the negation that files a claim. No translation or model interpretation can drop them.
- **The system MUST NOT**:
  - promise a claim's outcome, a refund, or approval;
  - ask for codes, PINs, passwords, or card data;
  - explain or discuss a charge under a suspicious-activity report or open investigation (anti-money-laundering review).
- **Closing a case as "it was mine" needs a deterministic affirmative.** A negation detected by the rules always files the claim.
- **Cases the system cannot resolve safely go to a person** with a structured handoff: the request, verified facts, actions taken, evidence, rights and deadlines, and open questions.

Rationale: a wrong answer about money or fraud harms the customer. Escalating is always safer than guessing.

### IV. No Data or Secrets in the Repository

- **The repository is public.** The following MUST NOT be committed:
  - the organizers' dataset, extracts, or customer and transaction rows;
  - evaluation case files (they contain data rows);
  - model artifacts trained on the data;
  - `.env` files, API keys, the organizers' S3 keys, or the bucket name.
- **Only aggregates reach tracked files.**
- **The data pipeline minimizes data.** Identity documents, contact details, addresses, income, and credit scores are dropped at build time. Account and card numbers keep only their last four digits.
- **Only the fields a turn needs are sent to an external model.** Other customers' data never is.
- **Every commit MUST pass the local secret scan** (the patterns file kept outside the repository, plus the bucket name) with zero matches.

Rationale: the organizers forbid credentials and private records in submissions and external requests. A leaked key or data row cannot be recalled.

### V. Evaluate Before Claiming

- **No metric is claimed without a reproducible run on held-out cases.**
- **Held-out sets are separate from the cases used to tune the system**: new seeds, and held-out phrasings the rules never saw. Their expected outcomes are written before the system runs.
- **Reports cover the organizers' outcome measures, with counts and denominators**:
  - safe automated resolution, and the share of cases where automation was attempted;
  - containment;
  - missed and unnecessary transfers;
  - unsafe outcomes by type;
  - p50/p95 latency and cost;
  - breakdowns by language and segment.
- **The learned component is compared against a baseline** on a time split, with no leakage, and tracked in MLflow.
- **Every input is labelled**: organizer synthetic data, team-generated, or synthetic policy.
- **Limitations are reported plainly**, including negative results and trade-offs.
- **A defect found by evaluation gets a general fix and a regression test**, never a case-specific patch.

Rationale: judges assess measured quality and honesty about what is missing. Numbers tuned on their own test set are not evidence.

## Hackathon Constraints

- **Workflow**: one customer-service workflow, transaction-dispute intake, in English, Spanish, and Portuguese, for customers in Mexico, Colombia, and Argentina.
  - English is the base language: the common form and the source wording are in English, so a new language adds only its understanding and its wording.
  - Every supported language works in rules mode, with fixed wording and rule-based understanding, and has its own evaluation cases.
  - English and Portuguese run on team-generated cases, since the dataset is Spanish only.
- **Required cases**: a normal path, an ambiguous or unsupported request, and a human-required case.
- **Scope limits**: no money movement, refunds, claim decisions, merchant blocking, or live lending decisions.
- **Stack**:
  - backend: Python (FastAPI, DuckDB over a Parquet warehouse, scikit-learn, MLflow);
  - frontend: React (Vite, TypeScript, TanStack Query);
  - models: the Anthropic Python SDK.

  Development is local first. Deployment is needed only for the submission link.
- **Deadline**: submissions close **2026-10-05 at midnight, Colombia time (UTC-5)**.
- **Deliverables**:
  - the public repository `factored-hackathon-2026-problem-crushers`;
  - a deployed tool;
  - 4-6 slides;
  - a video of at most three minutes;
  - notes on limitations and future work.
- **Source of the idea**: the ideation repository `~/personal/factored-idea` (`.specify/assessments/explain-this-charge/`). Its latest dated sections win on questions of scope and evidence.

## Development Workflow and Quality Gates

- **Each change passes three gates before it is committed**:
  - `make test` (workflow, guard, and security tests);
  - the frontend type-check and build;
  - the secret scan.
- **Changes reach `main` only through a pull request** from a feature branch (`CONTRIBUTING.md`). It is merged with a merge commit once the GitHub checks (`frontend`, `backend`, `secrets`) pass, and its description records the local gates that need private data. `main` is protected so that this holds for everyone, the owner included.
- **Each deployment is a version**: an annotated `vMAJOR.MINOR.PATCH` tag on the deployed commit of `main`, with a GitHub release whose notes name its features and its live revision. Tags are never moved, and published history is never rewritten.
- **Workflow or understanding changes also require `make eval`** (rules mode, free). Claude-mode evaluation (`make eval-llm`, which costs money) is run before any reported number changes.
- **A new behaviour that affects safety adds a test that fails without it.** Tests use a deliberately wrong fake model where the guard must hold regardless of the model.
- **Where decisions are recorded**:
  - `docs/build-plan.md`: decisions and their reasons;
  - `docs/evaluation.md` and `docs/model-card.md`: regenerated or updated whenever results change.
- **Spec Kit artifacts** under `specs/` describe what is built and what remains. The spec and plan are updated when scope or architecture changes, and tasks are checked off as work lands.

## Governance

- **Precedence**: this constitution overrides conflicting guidance in other documents. `CLAUDE.md` holds runtime guidance for Claude Code and MUST stay consistent with it.
- **Amendments**: made by editing this file, with a version bump and an updated Last Amended date.
  - **MAJOR**: a principle is removed or redefined.
  - **MINOR**: a principle or section is added or materially expanded.
  - **PATCH**: clarifications.
- **Reviews**: every plan (`/speckit-plan`) runs its constitution check against Principles I-V. Any violation must be justified in the plan's complexity tracking, or removed.
- **Owner**: the team owner approves amendments. Today that is the team's only builder.

**Version**: 1.2.0 | **Ratified**: 2026-09-30 | **Last Amended**: 2026-10-02
