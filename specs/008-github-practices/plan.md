# Implementation Plan: GitHub practices: branches, pull requests, tagged versions

**Branch**: `008-github-practices` | **Date**: 2026-10-02 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/008-github-practices/spec.md`

## Summary

- **Branches and pull requests**:
  - every change goes on a branch and reaches `main` only through a pull request, with a description template and three checks on GitHub (`frontend`, `backend`, `secrets`; [research.md](research.md) R1);
  - after this feature's own pull request merges, GitHub branch protection on `main` requires a pull request and passing checks, with no approval and admins included (R2);
  - merge commits only (R3).
- **Versions**:
  - the seven past deployments get annotated tags `v0.1.0` … `v0.5.0` on their deployed commits, from Azure's revision list, with GitHub releases (R4);
  - from now on, `scripts/release.sh` tags and releases each deployment;
  - the deploy script deploys only a clean, up-to-date `main` (R6).
- **Commits**: Conventional Commits, checked by a versioned `commit-msg` hook. A `pre-push` hook runs the private secret scan on what is pushed (R5).
- **Rules**: the constitution's Development Workflow (amendment 1.2.0), `CLAUDE.md` "Collaboration", the README, and a new `CONTRIBUTING.md` describe the way of working.

## Technical Context

**Language/Version**: GitHub Actions YAML; POSIX shell for hooks and scripts; the existing Python 3.10 and Node toolchains in CI.

**Primary Dependencies**: the GitHub CLI (signed in by the owner), and `actions/checkout`, `actions/setup-node`, `actions/setup-python`, and `gitleaks/gitleaks-action` on GitHub.

**Storage**: none

**Testing**: the hooks are checked by hand (quickstart). CI runs on the feature's own pull request. The protection is checked by a refused push.

**Target Platform**: github.com (a public repository under the owner's account), and the owner's WSL machine.

**Project Type**: repository workflow (no app change)

**Constraints**:
- nothing private in CI (the warehouse, the scan patterns, keys);
- published history is never rewritten;
- the app and its gates are unchanged;
- three days to the deadline.

**Scale/Scope**: about 8 files added or changed, 7 tags, 7 releases, 1 protection rule.

## Constitution Check

*GATE: checked before Phase 0, and again after design (v1.1.0 → 1.2.0).*

| Principle | How this plan meets it | Result |
|---|---|---|
| I-III (workflow, permissions, facts) | No app change. | Pass |
| IV. No data or secrets in the repository | CI needs no data or private patterns. The pre-push hook adds a guard against publishing secrets. Release notes contain no data. | Pass |
| V. Evaluate before claiming | No metric changes. CI results are public evidence for what it covers, and the pull request states the rest. | Pass |
| Development Workflow | **Amended**: "committed" becomes "merged into `main` through a pull request". The three local gates are unchanged, plus the GitHub checks. MINOR bump (1.2.0): a section materially expanded, no principle redefined. | Pass (with amendment) |

**Post-design re-check**: still passes. The amendment is part of this feature (spec FR-810).

## Project Structure

### Documentation (this feature)

```text
specs/008-github-practices/
├── spec.md
├── plan.md
├── research.md          # R1-R7
├── data-model.md
├── quickstart.md
├── contracts/conventions.md
├── checklists/requirements.md
└── tasks.md             # /speckit-tasks
```

### Repository files

```text
.github/workflows/ci.yml            # frontend, backend, secrets jobs
.github/pull_request_template.md    # FR-803
.githooks/commit-msg                # Conventional Commits
.githooks/pre-push                  # local secret scan on pushed commits
scripts/release.sh                  # tag + GitHub release for a deployed commit of main
scripts/deploy-azure.sh             # guard: clean main, equal to origin/main
docs/releases/                      # release notes per version (v0.1.0.md … v0.5.0.md)
CONTRIBUTING.md                     # branches, pull requests, commits, releases
.specify/memory/constitution.md     # 1.2.0
CLAUDE.md, README.md, docs/build-plan.md
```

**Structure Decision**: GitHub's standard locations (`.github/`). Hooks live in the repository so teammates get them with one `git config` line. Release notes live in `docs/releases/` so they're also readable in git.

## Complexity Tracking

| Item | Why | Simpler alternative rejected because |
|---|---|---|
| Admins included in the protection | The owner is the only admin and the main committer; excluding admins would leave the main path unprotected | A convention-only rule was option B, which the owner declined |
