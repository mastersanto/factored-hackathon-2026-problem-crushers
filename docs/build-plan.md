# Build plan

- **Status**: proposal, 2026-09-30. The decisions marked **[team]** are open.
- **Deadline**: submissions close 2026-10-05, midnight Colombia time (UTC-5). Treat 2026-10-05 as a buffer day, not a build day.
- **Deliverables**:
  - a public GitHub repository named `factored-hackathon-2026-problem-crushers`;
  - a deployed tool (it need not run 24/7);
  - a 4-6 slide deck;
  - a video of at most three minutes showing the working solution and the core architectural decisions;
  - notes on limitations, caveats, and future work.

## Principles

- **Deterministic core, AI at the edges.**
  - Finding transactions, checking the outbound record, applying country rules, computing deadlines, and enforcing permissions are code.
  - The language model understands what the customer means (intent, which transaction, language) and phrases answers **only from verified facts**.
  - A response that cites a fact the tools did not return is blocked.
- **Permissions in the tool layer, not the prompt.** The session identity decides which customer's data a tool may read. The model never receives another customer's records.
- **Every claim traceable.** Each statement to the customer carries its source (a record ID or rule ID) and is marked *known* or *guessed*.
- **Evaluate from day one.** The held-out test cases and the metrics harness exist before the assistant is feature-complete.

## Architecture (proposal)

```text
customer (web chat, ES/PT)
        |
   API service (Python, FastAPI)
        |
   workflow engine: understand -> decide -> act -> verify -> escalate   (explicit state machine)
        |                |                   |                      |
   LLM: intent,     tools (read-only):     policy service:        handoff builder:
   slots, language, find_transactions,    country rules,         request, verified facts,
   phrasing from    get_transaction,       deadlines, rights,     actions, evidence, deadline,
   verified facts   outbound_record_check, synthetic fee         open questions
                    card_status            schedule
        |
   data layer: DuckDB over Parquet built from the organizers' dataset (subset for the deployed demo)
        |
   ML: own-charge vs fraud model (tracked in MLflow), benchmarked against fraud_score >= 50
        |
   observability: structured logs and traces per turn, latency and token cost per case
```

**Agent-side view.** A handoff queue where a person sees the structured handoff. This is also the demo's human-required case.

### Mapping to the four judged pillars

| Pillar | What we show |
|--------|--------------|
| **Data engineering** | Pipeline from the S3 mirror to validated Parquet. Data-quality checks, including the known random and odd fields: response codes, SLA flags, no MXN, the two spellings of Mexico. A reproducible build of the demo subset. |
| **Data analytics** | Baseline metrics from the data: resolution time, first-contact resolution, SLA breaches, the complaint mix. An evaluation dashboard comparing the baseline and the system. |
| **Machine learning** | The fraud model with a time-based split, no leakage, and `fraud_score` as the baseline, tracked with MLflow. An intent classifier compared with a keyword baseline. |
| **AI engineering** | The workflow engine, tools, guardrails (prompt injection, unauthorized access, expired session), handoff, deployment, and tracing. |

## Open decisions **[team]**

1. **Team roster and roles.** Who covers data engineering, machine learning, the backend and agent, the frontend and deployment, and the slides and video?
2. **LLM provider and budget.** The proposed default is Anthropic Claude: a fast, low-cost model (Claude Haiku 4.5) for understanding, and a stronger one (Claude Sonnet 5.5) for phrasing. Customer records must not go to any external model beyond the minimum fields for the case; the problem statement forbids credentials or private records in external model requests. The alternative is whatever credits the team already has.
3. **Deployment target.** The organizers suggest Azure, AWS, Snowflake, or Databricks, but any host works. The proposal is one container (API plus UI) on a simple host with a small, private demo data subset loaded at startup, never committed to the public repository.
4. **UI.** Streamlit is fastest (customer chat plus agent queue in one app). A React front end looks better but costs about a day.
5. **Portuguese.** How many team-generated Portuguese cases, and who writes and labels them?
6. **Synthetic fee schedule.** Build it (stretch) or keep fee complaints as intake and handoff only.

## Day plan (proposal)

| Day | Data engineering / analytics | Machine learning | Agent / backend | Frontend / deployment / story |
|-----|------------------------------|------------------|-----------------|-------------------------------|
| **Tue 09-30** | Pipeline from the mirror to Parquet; data-quality report; demo subset selection | Label and leakage check on `is_fraud`; baseline from `fraud_score` | Repository skeleton; tool interfaces; workflow state machine | Decide stack and host; hello-world deployment |
| **Wed 10-01** | Baseline metrics; held-out case list (transactions to tie conversations to) | First fraud model; MLflow tracking | Understand step (intent, slots, language); find and explain transaction; outbound check | Chat UI connected to the API |
| **Thu 10-02** | Team-generated test conversations, ES and PT, labelled with expected outcomes | Intent classifier against keyword baseline; model card | Verify step (fact grounding); rights and deadlines; handoff builder; guardrails | Agent handoff queue; deployment with the demo subset |
| **Fri 10-03** | Evaluation harness: all outcome measures with denominators, by language and segment | Repeated-run variability; error analysis | Failure handling: bounded retries, safe fallback, expired session, injection tests | Tracing and latency/cost dashboard |
| **Sat 10-04** | Final evaluation run; limitations write-up | Final model numbers | Freeze features; fix evaluation failures | Slides (4-6), video (3 minutes max), README |
| **Sun 10-05** | Buffer: re-run the evaluation on the deployed build, check links, submit before midnight Colombia time | | | |

## Test cases (held-out workload)

Built by the team and tied to real transactions in the dataset, with the expected outcome labelled before the system is run:

- **Normal**: a recognized charge explained and confirmed; a pending charge explained as pending.
- **Ambiguous**: several matching transactions; a vague description; an out-of-scope request.
- **Human required**:
  - likely fraud;
  - a fake "fraud alert" asking for a code;
  - a fee dispute;
  - a charge under compliance review (never explained).
- **Failure cases** the organizers name:
  - incorrect or missing data;
  - an expired session;
  - an unauthorized access attempt (another customer's transaction);
  - prompt injection;
  - a tool outage.
- **Portuguese**: the same scenarios, team-generated and labelled.

## Security and data rules

- **Never commit the dataset or credentials.** The organizers' S3 keys, the bucket name, API keys, and `.env` files stay out of git. The repository is public.
- **The demo subset stays private.** It is loaded at deploy time from private storage and never committed.
- **Only minimal fields go to an external model**: the case's transaction fields, never other customers' data or identity documents.
- **Label every data source** in the submission: synthetic organizer data, team-generated cases, or synthetic policies.
