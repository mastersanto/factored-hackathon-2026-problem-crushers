# Quickstart: checking suggestions per language

Rules mode, free.

## 1. Gates

```bash
make test                       # includes the example-understanding test (research R5)
cd frontend && npm run build
```

**Expected**: every example in every language is understood like its Spanish counterpart, and `done.lang` equals the example's language.

## 2. UI checks

```bash
SESSIONS_PER_IP_HOUR=1000 LLM_DISABLED=1 make dev   # its own terminal
cd frontend && npm run check:ui
```

**Expected**: every existing check passes, plus `e2e/suggestions.spec.ts` ([contracts/ui.md](contracts/ui.md#checks-frontende2esuggestionsspects)).

## 3. By hand

1. Open http://localhost:5173 with the browser in English and sign in. Every example button is in English.
2. Pick **ES** in the header: every example turns Spanish at once. Pick **PT**: Portuguese.
3. Tap the charge example in Portuguese: the reply is in Portuguese, with the quick replies "Sim, fui eu" / "Não fui eu". Before answering, pick **ES**: the quick replies change to "Sí, fui yo" / "No fui yo".

## 4. Evaluation

`make eval` is not needed: nothing under `backend/app/workflow/`, `language/`, `llm/`, or `policy/` changes. If an implementation task touches them after all, run it: the results must be unchanged.
