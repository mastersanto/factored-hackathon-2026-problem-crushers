# Quickstart: checking progress and replies

Rules mode is free.

## 1. Gates

```bash
make test                       # inquiry transitions, re-asks, search echoes, in en/es/pt
make eval                       # this feature touches backend/app/workflow/: no metric may drop (FR-609)
cd frontend && npm run build
```

**Expected**:
- every transition in [data-model.md](data-model.md) holds;
- the evaluation's per-language numbers equal or beat the current `docs/evaluation.md` (English 100/100/93.3, Spanish 100/100/85.6, Portuguese 100/100/84.4), with 0 unsafe answers.

## 2. UI checks

```bash
SESSIONS_PER_IP_HOUR=1000 LLM_DISABLED=1 make dev   # its own terminal
cd frontend && npm run check:ui
```

**Expected**: every existing check passes, plus `e2e/progress.spec.ts` ([contracts/ui.md](contracts/ui.md#checks-frontende2eprogressspects)).

## 3. By hand (phone width)

1. Sign in with the claim scenario. The drawer reads "Starts with your first message".
2. Tap the charge example. The drawer shows "Step 3 of 5 · You confirm if it was you".
3. Write "hello". The reply asks "was it you?" again, and the drawer doesn't move.
4. Tap "It wasn't me". It moves to step 4. Tap a statement reply: "Sent to a specialist · case …".
5. Pick **PT**. The panel shows the same state in Portuguese.
6. Write a charge with an amount that doesn't exist (for example "no reconozco un cargo de 7" in the Spanish session). The reply names the amount and asks only for the merchant or the day.
