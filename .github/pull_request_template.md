## What and why

<!-- One or two sentences: what changes for the customer, the specialist, or the team, and why. -->

## Spec / task

<!-- specs/NNN-…/ and task IDs, e.g. specs/008-github-practices T008. "None" for a small fix. -->

## Checks

GitHub runs `frontend`, `backend`, and `secrets` on this pull request. The local gates need private data, so tick them here:

- [ ] `make test` (backend tests, rules mode)
- [ ] `cd frontend && npm run build && npm run lint`
- [ ] `cd frontend && npm run check:ui` (against `SESSIONS_PER_IP_HOUR=1000 LLM_DISABLED=1 make dev`)
- [ ] `make eval`, required when `backend/app/workflow/`, `language/`, `llm/`, or `policy/` changed (no metric may drop)
- [ ] Local secret scan on the diff: 0 matches

## Deploy

<!-- Needs a redeploy? If so, the owner approves it; after deploying, tag and release with scripts/release.sh. -->
