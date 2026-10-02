# Tasks: GitHub practices: branches, pull requests, tagged versions

**Input**: design documents in `specs/008-github-practices/`: spec.md, plan.md, research.md (R1-R7), data-model.md, contracts/conventions.md, quickstart.md

**Tests**: no automated tests requested. Each story is checked by the quickstart steps: a refused bad commit message, green checks on pull request #1, a refused direct push, and the tag and release listings.

**Prerequisites (done 2026-10-02)**: the GitHub CLI is signed in as `mastersanto`, with `repo` and `workflow` scopes and admin on the repository.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: can run in parallel (different files, no dependency on an incomplete task).
- **[Story]**: US1 (branches and pull requests), US2 (tagged versions), US3 (commit messages).

## Gates (before every commit on this feature)

- `make test` and the frontend build: unchanged app, so both must still pass.
- The local secret scan on the staged diff (0).
- No app file changes: only `.github/`, `.githooks/`, `scripts/`, `docs/`, `specs/008…`, `CONTRIBUTING.md`, `CLAUDE.md`, `README.md`, and the constitution.

---

## Phase 1: Setup

- [X] T001 Create branch `008-github-practices` from an up-to-date `main` (`git switch -c 008-github-practices`). Every commit for this feature goes on it (FR-801).

---

## Phase 2: Foundational (blocks US1's pull request)

- [X] T002 [P] Create `.github/workflows/ci.yml`, per contracts/conventions.md "Status checks" and research R1:
  - **Triggers**: `pull_request` into `main`, and `push` to `main`.
  - **Permissions**: `contents: read`.
  - **`frontend`**: Node 22, `npm ci`, `npm run build`, and `npm run lint` in `frontend/`, using the npm cache.
  - **`backend`**: Python 3.10; `pip install -e backend` (plus `pytest`); `python -m compileall -q backend/app`; `cd backend && LLM_DISABLED=1 pytest -q tests/test_config.py`.
  - **`secrets`**: `actions/checkout` with `fetch-depth: 0`, then `gitleaks/gitleaks-action@v2` with `GITHUB_TOKEN`.

  Job names must be exactly `frontend`, `backend`, and `secrets`, the required checks of T009.
- [X] T003 [P] Create `.github/pull_request_template.md` with the sections of contracts/conventions.md: **What and why**, **Spec / task**, **Checks** (tick boxes for `make test`, build and lint, `npm run check:ui`, `make eval` with its "required when" note, and the local secret scan (0)), and **Deploy**.

**Checkpoint**: the checks and the template exist on the branch.

---

## Phase 3: User Story 1 - Every change goes through a feature branch and a pull request (P1) 🎯 MVP

**Goal**: `main` receives only pull request merges, with green checks.

**Independent Test**: pull request #1 shows the template and three green checks, and merges with a merge commit. Afterwards, a direct push to `main` is refused.

- [X] T004 [US1] Create `CONTRIBUTING.md`, covering:
  - **Branches**: the naming pattern from contracts/conventions.md, with examples.
  - **The pull request flow**: branch → local gates → push → pull request using the template → green checks → merge commit → branch deleted.
  - **Commits**: the convention (US3).
  - **The hooks**: `git config core.hooksPath .githooks` once per clone.
  - **Releases**: US2, `scripts/release.sh`.
  - **Teammates' branches**: the owner runs the private secret scan, the tests, the build, and the UI checks on `git diff main...<branch>` before merging (from `CLAUDE.md`).
  - **What can't run on GitHub and why**: no data or private patterns in CI.
- [X] T005 [US1] Amend `.specify/memory/constitution.md` to 1.2.0 (Last Amended 2026-10-02). In "Development Workflow and Quality Gates":
  - changes reach `main` only through a pull request whose GitHub checks (`frontend`, `backend`, `secrets`) pass and whose description records the local gates;
  - each deployment is tagged `vX.Y.Z` and released;
  - published history is never rewritten.

  Keep the three local gates. Add a Sync Impact note at the top, as earlier amendments did.
- [X] T006 [US1] Update `CLAUDE.md`:
  - **Collaboration**: replace "The owner's own work has gone straight to `main`…" with the branch and pull request flow, and note that the GitHub CLI is now signed in (so pull requests are opened with `~/.local/bin/gh pr create`, not compare links);
  - **Spec Kit**: add 008;
  - **Commands**: add `scripts/release.sh`;
  - **Deployment**: deploy only a clean `main` equal to `origin/main`, then tag.

  Also update the owner-preferences memory, since direct commits to `main` no longer apply.
- [X] T007 [P] [US1] In `README.md`, add a short "How we work" section (branches, pull requests, checks, versions, with a link to `CONTRIBUTING.md` and to the Releases page) and the 008 row in the documents table. In `docs/build-plan.md`, record the decisions:
  - pull requests with checks, and protection including admins;
  - merge commits;
  - the past deployments tagged from Azure's revision list;
  - what CI can't run and why.
- [X] T008 [US1] Commit everything so far on the branch (Conventional Commits; the local scan at 0), push with `git push -u origin 008-github-practices`, and open pull request #1 with `gh pr create --base main` and a body filled from the template. Wait for `frontend`, `backend`, and `secrets` to pass (`gh pr checks --watch`). If one fails, fix it on the branch and push again. Then merge with `gh pr merge --merge --delete-branch`, and update the local `main`.
- [X] T009 [US1] Turn on the protection for `main` (research R2):
  - with `gh api -X PUT repos/mastersanto/factored-hackathon-2026-problem-crushers/branches/main/protection`: required status checks `frontend`, `backend`, `secrets` (strict), `enforce_admins: true`, `required_pull_request_reviews` with `required_approving_review_count: 0`, `allow_force_pushes: false`, `allow_deletions: false`;
  - in the repository settings (`gh api -X PATCH repos/...`): `allow_merge_commit: true`, `allow_squash_merge: false`, `allow_rebase_merge: false`, `delete_branch_on_merge: true`.

  Check: a direct `git push origin main` of a throwaway local commit is refused. Then drop that commit with `git reset --hard origin/main`, after confirming it is the only difference.
- [X] T010 [US1] Delete the merged remote branch `003-ui-improvements` (`git push origin --delete 003-ui-improvements`, after confirming `git branch -r --merged origin/main` lists it) and its local copy.

**Checkpoint**: `main` is protected, and its history shows pull request #1 as a merge.

---

## Phase 4: User Story 2 - Tagged versions show the project's progress (P1)

**Goal**: every deployment, past and future, has a tag and a release.

**Independent Test**: `git tag -n1` and the Releases page list `v0.1.0` … `v0.5.0` on the commits of research R4, with `v0.5.0` as latest.

- [X] T011 [P] [US2] Write release notes `docs/releases/v0.1.0.md` … `v0.5.0.md` (7 files), one per row of research R4. Each has:
  - what the version added, with spec links;
  - the Azure revision and the deploy date (`az containerapp revision list --all` created time);
  - the deployed commit;
  - the line "Tag added on 2026-10-02 to the commit Azure deployed".

  Rows:

  | Tag | Commit | Notes |
  |---|---|---|
  | `v0.1.0` | `ab130b1` | 001: dispute intake assistant, first public deployment |
  | `v0.1.1` | `a229b75` | demo picks skip charges under compliance review; deploy script |
  | `v0.2.0` | `860c486` | 002: conversation PDF with a check code |
  | `v0.3.0` | `360f5ad` | 003: UI improvements (merge of the teammate's branch) |
  | `v0.3.1` | `aee52bd` | sign-in explains 429s; session limit keyed on the proxy address |
  | `v0.4.0` | `c2994a6` | 004 + 005: English, Spanish, and Portuguese; switcher; suggestions per language |
  | `v0.5.0` | `aec4a64` | 006 + 007: inquiry progress, replies that follow the message, last movements, courtesy |
- [X] T012 [P] [US2] Create `scripts/release.sh VERSION NOTES_FILE` (research R6). It refuses unless:
  - the version matches `^v(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$`;
  - the tag doesn't exist locally or on `origin`;
  - the current branch is `main`, with no uncommitted changes, and `HEAD` equals `origin/main`;
  - the notes file exists.

  Then it runs `git tag -a VERSION -F NOTES_FILE`, `git push origin VERSION`, and `gh release create VERSION --verify-tag --notes-file NOTES_FILE --title VERSION`. Add an optional `--at <commit>` for tagging an earlier deployed commit of `main` (used once by T014), which checks that the commit is an ancestor of `origin/main`.
- [X] T013 [P] [US2] Add a guard at the top of `scripts/deploy-azure.sh`, before any Azure call: refuse unless on branch `main`, with a clean tree (`git status --porcelain` empty), after `git fetch origin main` and with `HEAD` equal to `origin/main`. Print the reason. Allow an explicit `ALLOW_UNRELEASED=1` override for emergencies, printing a warning.
- [X] T014 [US2] After T008-T009 (the notes and script reach `main` through a pull request, see T016), tag and release the past deployments from `main`: `scripts/release.sh vX.Y.Z docs/releases/vX.Y.Z.md --at <commit>`, in order `v0.1.0` → `v0.5.0`. Then make sure `v0.5.0` is marked latest (`gh release edit v0.5.0 --latest`). Check: `git rev-list -n1 v0.5.0` starts with `aec4a64`.

---

## Phase 5: User Story 3 - Clear commits (P2)

**Goal**: every new commit follows the convention, checked automatically.

**Independent Test**: with the hooks enabled, `git commit -m "bad message"` is refused and `git commit -m "docs: x"` is accepted.

- [X] T015 [P] [US3] Create `.githooks/commit-msg` and `.githooks/pre-push` (executable, POSIX `sh`), per research R5:
  - **`commit-msg`**: accept a first line matching contracts/conventions.md's pattern, at most 72 characters, or one starting with `Merge ` or `Revert `. Otherwise print the expected format with an example and exit 1.
  - **`pre-push`**: for each pushed ref, scan the diff of the commits being pushed (`git diff <remote_sha>..<local_sha>`, or against `origin/main` for a new branch) with `grep -E -c -f ~/.aws/factored-datathon-scan-patterns -e "$(cat ~/.aws/factored-datathon-bucket)"`. Block the push on a count above 0, printing only the count, never the match. If either private file is missing, print a warning and allow the push.

  Enable them in this clone (`git config core.hooksPath .githooks`). Note: the hooks apply from the commit after they're added. T008's commits already follow the convention by hand.

---

## Phase 6: Polish

- [X] T016 Open pull request #2, `chore/releases`, with T011-T013 if they weren't in pull request #1. It must pass the checks and merge through protection: the first pull request under the new rule. Then run T014.
- [X] T017 Run the quickstart end to end and record the results here:
  - hooks;
  - the pull request with green checks;
  - a refused direct push;
  - tags and releases;
  - a refused deploy from a branch.
- [X] T018 Update the build-status memory: protection on, tags `v0.1.0`-`v0.5.0`, the next release is `v0.6.0` or `v1.0.0` at submission, and every change now goes through a pull request.

---

## Results (2026-10-02)

| Check | Result |
|---|---|
| Hooks | `git commit -m "bad message"` refused by `commit-msg`; `chore: hook check` accepted. `pre-push` ran on every push: 0 matches |
| Pull request #1 | `frontend` (15 s), `backend` (36 s), `secrets` (8 s) green; merged as a merge commit (`82e3c0f`), branch deleted |
| Protection | `main`: checks `frontend`, `backend`, `secrets` (strict), admins included, 0 approvals, no force pushes or deletions. A direct `git push origin main` was refused (GH006). Squash and rebase merges are off; branches are deleted on merge |
| Old branch | `003-ui-improvements` (merged) deleted on GitHub and locally |
| Tags and releases | `v0.1.0` … `v0.5.0` on `ab130b1`, `a229b75`, `860c486`, `360f5ad`, `aee52bd`, `c2994a6`, `aec4a64`; seven GitHub releases, `v0.5.0` latest |
| Deploy guard | `scripts/deploy-azure.sh` from a branch: "deploy: switch to main first", before building |
| Pull request #2 | this record, merged under protection |

## Dependencies and execution order

- **T001** comes first.
- **T002-T007** can run in any order on the branch (T002, T003, T007, T011-T013, and T015 touch different files).
- **T008** needs T002-T007, plus any of T011-T013 and T015 that should ride in pull request #1.
- **T009** comes after T008's merge. **T010** can come any time after T008.
- **T014** needs the notes and the script on `main`, via T008 or T016, plus T009.
- **T017-T018** come last.

```text
T001 ─► T002,T003,T004..T007,(T011,T012,T013,T015) ─► T008 (PR #1) ─► T009 (protect) ─► T016 (PR #2 if needed) ─► T014 (tags) ─► T017, T018
```

## Parallel opportunities

- T002, T003, T007, T011, T012, T013, and T015: separate files.
- T011's seven notes files are written together.

## Implementation strategy

1. **MVP (US1)**: T001-T010. `main` is protected, and the history shows pull requests from now on. This is the biggest signal in the evaluation.
2. **Then US2**: T011-T014. Seven releases make the progress readable.
3. **Then US3**: T015. The hooks keep commits clean without anyone remembering.
4. **Preferred packaging**: put T011-T013 and T015 in pull request #1 too, so one pull request lands the whole practice and pull request #2 isn't needed. T016 then only checks that a second small pull request merges under protection. The pending courtesy source-label fix is a good candidate.
