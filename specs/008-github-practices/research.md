# Research: GitHub practices

Decisions for [plan.md](plan.md).

## R1. What the checks on GitHub can run

- **Finding**: the backend tests and the evaluation read the data warehouse (`backend/data/`, git-ignored and never committed, constitution IV). Of the 8 test files, only `tests/test_config.py` runs without it. The UI checks need the API with data. The secret scan's patterns file lives outside the repository and must never be published.
- **Decision**: one workflow, `.github/workflows/ci.yml`, on every pull request into `main` and on pushes to `main`, with three jobs:
  - **`frontend`**: `npm ci`, then `npm run build` (type-check and build) and `npm run lint`.
  - **`backend`**: install the package on Python 3.10; `python -m compileall -q app` (every module parses); `pytest tests/test_config.py`.
  - **`secrets`**: a generic public secret scan (gitleaks) over the pull request's commits.
- **Why**: everything that can run without private data runs on every pull request, and its result is visible to anyone (FR-804). The rest stay local gates, stated in the pull request (FR-803).
- **Considered**:
  - **Synthetic fixture data for the backend tests in CI.** Rejected for now: three days left, and a fixture warehouse is a new data artifact to label and maintain. Recorded as future work.
  - **The private patterns in a GitHub secret.** Rejected: the patterns describe the organizers' data and bucket, and a workflow log could echo them.

## R2. Protecting `main` (owner's choice, Q1 A)

- **Decision**: classic branch protection on `main`, set with the GitHub CLI after sign-in:
  - pull request required, 0 approving reviews;
  - required status checks `frontend`, `backend`, `secrets`, strict (up to date with `main`);
  - no force pushes, no deletion;
  - enforce for admins: on (the owner's own pushes go through pull requests too, which is the point).
- **Order**: protection is turned on after this feature's own pull request merges, so the check names exist and the first pull request isn't blocked by a rule it introduces.
- **Considered**: rulesets (newer). Equivalent here; classic protection is one documented API call.

## R3. Merge method

- **Decision**: merge commits only. Squash and rebase merges are disabled in the repository settings, and branches are deleted after merge.
- **Why**: "small, frequent merges through PRs" should be visible in `main`'s history as one merge per pull request, keeping the commits inside it (spec Assumptions).

## R4. Tagging the past deployments (owner's choice, Q2 A)

- **Source of truth**: Azure's revision list (`az containerapp revision list --all`). Each revision's image tag is the deployed commit:

  | Tag | Revision | Commit |
  |---|---|---|
  | `v0.1.0` | 1 | `ab130b1` |
  | `v0.1.1` | 2 | `a229b75` |
  | `v0.2.0` | 3 | `860c486` |
  | `v0.3.0` | 4 | `360f5ad` |
  | `v0.3.1` | 5 | `aee52bd` |
  | `v0.4.0` | 6 | `c2994a6` |
  | `v0.5.0` | 7 | `aec4a64` |

- **Decision**:
  - annotated tags on those commits, each message starting "Added 2026-10-02 for a deployment of <date>";
  - one GitHub release per tag, with notes: the features and specs, the Azure revision, and the deploy date;
  - `v0.5.0` is marked latest.
- **Numbering**: MINOR for feature releases and PATCH for the two fix releases (spec FR-807). The submission is `v1.0.0`.

## R5. Commit messages and local hooks

- **Decision**: Conventional Commits (`feat`, `fix`, `docs`, `test`, `chore`, `ci`, `refactor`; optional scope; first line ≤ 72 characters). Two versioned hooks in `.githooks/`, enabled with `git config core.hooksPath .githooks`:
  - **`commit-msg`**: rejects a first line that doesn't match the convention. Merge and revert messages are let through.
  - **`pre-push`**: runs the official local secret scan on the commits being pushed when the private patterns file exists, and blocks the push on any match. Without the file (a teammate's machine) it warns and lets the push through, since the owner scans teammates' branches before merging (unchanged).
- **Why**: the convention and the scan happen without anyone remembering them.

## R6. Releasing a deployment

- **Decision**: `scripts/release.sh vX.Y.Z notes.md`. It refuses unless:
  - the current branch is `main`, clean and up to date with `origin/main`;
  - the tag is new and follows the version pattern.

  It then creates the annotated tag, pushes it, and creates the GitHub release from the notes. The deploy script gains a guard: it refuses to deploy unless it is on a clean `main` that matches `origin/main` (FR-813).
- **Order per release**: merge the pull requests → `make deploy-azure` (with approval) → the live checks → `scripts/release.sh`.

## R7. This feature's own delivery

- **Decision**: built on branch `008-github-practices`, pushed, and merged through pull request #1 with the template and checks. Then: protection on, past tags and releases pushed.
