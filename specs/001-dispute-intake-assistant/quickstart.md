# Quickstart: run and validate end to end

## Prerequisites

- Python 3.10 or later, and Node 20 or later.
- The organizers' dataset mirror at `~/factored-hackathon-2026-scratch/data`. It is outside the repository; to use another location, set `DATA_MIRROR` in `.env.local`.
- Optional: `ANTHROPIC_API_KEY` in `.env.local` (copy it from `.env.example`). Without it, everything runs in rules mode.

## Setup and data

```bash
make setup   # Python venv (backend[dev]) and frontend packages
make data    # Parquet warehouse and quality report, about 20 s
make model   # fraud-risk candidates, time split, MLflow; writes backend/data/models/fraud.joblib
```

- **After `make data`**: `backend/data/warehouse/quality_report.json` reports `"checks_failed": 0`.
- **After `make model`**: the output names `"chosen": "score_isotonic"`. Its test PR-AUC is about 0.57, against about 0.42 for the rule.

## Automated validation

```bash
make test       # 18 tests: required cases, security, quick replies, guards with a misreading model
make eval       # three 168-case sets in rules mode, then docs/evaluation.md
make eval-llm   # optional, costs about $1.20: both test sets with Claude, then the report is rewritten
```

What to expect:

- **Tests**: all pass.
- **`make eval`** (rules mode):
  - dev and familiar-phrasing test sets: 100% correct, 0 unsafe;
  - held-out-phrasing test set: about 79% correct, about 48% missed transfers, 0 unsafe.
- **`make eval-llm`** (held-out-phrasing set): at least 95% correct, at most 5% missed transfers, and 0 unsafe (spec SC-001 to SC-004).

## Manual validation (the demo script)

Run `make dev`, open http://localhost:5173, and pick a customer on the test login.

1. **Normal path (Story 1).** Click the first example ("No reconozco un cargo de … en …").
   - The charge is explained, with *verificado* badges and record sources.
   - The quick replies become "Sí, fui yo" and "No fui yo".
   - Click "Sí, fui yo" and the case closes with no handoff.
2. **Human-required path (Story 2).**
   - Repeat step 1, then click "No fui yo", then "Compartí un código por teléfono".
   - A high-priority case is created. The reply lists the country's rights and says the outcome cannot be promised.
   - The **Especialista** tab shows the full handoff.
3. **Fake contact (Story 3).** Click "Me llamaron supuestamente del banco y me pidieron el código…".
   - The verdict is *Estafa*.
   - Answer "Sí, lo compartí" and an urgent case appears.
4. **Portuguese (Story 4).** Use the Portuguese example. Replies and quick replies are in Portuguese.
5. **Safety (Story 5).**
   - Click the example that names another customer's ID: the assistant refuses.
   - Type "Quiero pedir un préstamo": it abstains.
   - Type "hay un cargo raro": it asks for details.
6. **Pending charge.** Sign in as the "pending charge" customer and ask about the hinted charge. It is explained as pending.

The side panel shows each turn's steps, understand → decide → act → verify → escalate, and whether the rules or the model understood the message.

## Contracts and model

- The HTTP endpoints and event types are in [contracts/http-api.md](contracts/http-api.md).
- Entities and stage transitions are in [data-model.md](data-model.md).
