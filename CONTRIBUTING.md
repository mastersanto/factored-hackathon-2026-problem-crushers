# Contributing

How the team works on this repository (specs/008-github-practices). `main` is protected: every change reaches it through a pull request whose checks pass.

## Once per clone

```bash
git config core.hooksPath .githooks   # commit-message check, and the secret scan before each push
```

## Branches

One change per branch, named for what it does:

| Kind | Pattern | Example |
|---|---|---|
| A Spec Kit feature | `NNN-<feature>` | `008-github-practices` |
| A fix, docs, tests, chores, CI | `<type>/<short-name>` | `fix/courtesy-source-label`, `docs/video-link` |

Start from an up-to-date `main`: `git switch main && git pull && git switch -c fix/…`.

## Commits

[Conventional Commits](https://www.conventionalcommits.org/): `<type>(<scope>): <summary>`, a first line of at most 72 characters. The types are `feat`, `fix`, `docs`, `test`, `chore`, `ci`, and `refactor`. The body says why, and which gates passed. The `commit-msg` hook checks the first line.

## Pull requests

1. **Run the local gates.** They need the private data, so GitHub can't run them:
   - `make test`;
   - `cd frontend && npm run build && npm run lint`;
   - `npm run check:ui` against `SESSIONS_PER_IP_HOUR=1000 LLM_DISABLED=1 make dev`;
   - `make eval` when the workflow, understanding, models, or policy changed;
   - the local secret scan (0).
2. **Push and open the pull request**: `git push -u origin <branch>`, then `gh pr create --base main`. Fill in the template: what and why, the spec or task, the checks, and whether a redeploy is needed.
3. **Wait for the checks**: `frontend` (build and lint), `backend` (every module compiles, plus the tests that need no data), and `secrets` (gitleaks) must pass. `gh pr checks --watch`.
4. **Merge** with a merge commit (`gh pr merge --merge --delete-branch`). Keep pull requests small, and merge them as soon as they're green.

**Teammates' branches**: the owner runs the private secret scan on `git diff main...<branch>`, the tests, the build, and the UI checks before merging. Never commit the dataset, extracts, keys, the bucket name, `.env*`, generated PDFs, or anything under `backend/data/` (see the constitution, Principle IV).

## Releases

Each deployment is a version, `vMAJOR.MINOR.PATCH`: MINOR for features and PATCH for fixes, `v0.x` until the submission, which is `v1.0.0`.

1. Merge the pull requests, then deploy from a clean `main` equal to `origin/main` (`make deploy-azure`, with the owner's approval). The deploy script refuses otherwise.
2. After the live checks, write `docs/releases/vX.Y.Z.md`: its title line, what the version added with spec links, and the Azure revision. Merge it through a pull request.
3. Tag and publish: `scripts/release.sh vX.Y.Z docs/releases/vX.Y.Z.md` (on `main`). Tags are never moved or deleted.

The Releases page lists every deployment since the first, `v0.1.0`.

## After the submission: `main` frozen, new work on `next`

Judges evaluate the repository and the live demo from the submission (2026-10-05, midnight Colombia time) until finalists are announced (2026-10-15), and awards follow on 2026-10-16. What they see must stay what was submitted.

- **`v1.0.0` marks the submitted commit**: its tag and GitHub release are the fixed reference, and the submission email links them alongside the repository.
- **`main` is frozen until 2026-10-16**: only fixes the owner approves, each released as `v1.0.x`, and nothing that changes behaviour.
- **New work goes to `next`**: branch from `next` (`git switch next && git pull && git switch -c <branch>`), and open pull requests with `gh pr create --base next`. The same gates and checks apply.
- **The live demo stays on the submitted revision.** Trying `next` online needs a separate container app, never the one in the README, and the owner's approval.
- **After 2026-10-16**, `next` merges into `main` through one pull request, and releases continue as `v1.1.0` and later.
