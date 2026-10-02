# Contract: repository conventions

## Branch names

```text
^(\d{3}-[a-z0-9-]+|(feat|fix|docs|test|chore|ci|refactor)/[a-z0-9-]+)$
```

Examples: `008-github-practices`, `fix/courtesy-source-label`, `docs/video-link`.

## Commit and pull request titles

```text
^(feat|fix|docs|test|chore|ci|refactor)(\([a-z0-9-]+\))?!?: .{1,}$   (first line ≤ 72 characters)
```

`Merge …` and `Revert …` messages are accepted as git writes them.

## Pull request description (`.github/pull_request_template.md`)

Sections, all required:
- **What and why**
- **Spec / task**: link to `specs/NNN-…` and the task IDs
- **Checks**: tick boxes for `make test`, the frontend build and lint, `npm run check:ui`, `make eval` (when `backend/app/workflow/`, `language/`, `llm/`, or `policy/` changed), and the local secret scan (0)
- **Deploy**: whether a redeploy is needed

## Status checks (`.github/workflows/ci.yml`)

| Job name (required) | Runs |
|---|---|
| `frontend` | `npm ci`, `npm run build`, `npm run lint` in `frontend/` |
| `backend` | Python 3.10; `pip install -e backend`; `python -m compileall -q backend/app`; `pytest backend/tests/test_config.py` |
| `secrets` | gitleaks over the pull request's commits |

## Tags

```text
^v(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$
```

Annotated, on a commit of `main` that was deployed. `v1.0.0` is the submission.
