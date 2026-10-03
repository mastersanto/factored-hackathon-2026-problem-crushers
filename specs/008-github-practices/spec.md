# Feature Specification: GitHub practices: branches, pull requests, tagged versions

**Feature Branch**: `008-github-practices`

**Created**: 2026-10-02

**Status**: Draft

## Clarifications

### Session 2026-10-02

- Q: Should GitHub block direct pushes to `main`? → A: yes, enforced by GitHub now: `main` accepts changes only through a pull request with passing checks, with no required approval (one builder).
- Q: Tag the past deployments? → A: yes, all seven now on the exact commits Azure deployed (`v0.1.0` to `v0.5.0`: MINOR for feature releases, PATCH for the two fix releases), with release notes saying they were added on 2026-10-02.

**Input**: User description: "as members of the team, we want to implement these best practices for the project: Good GitHub practices are one of the easiest ways to stand out: Branching: work in feature branches, not straight on main. Merging: small, frequent merges through PRs beat one big bulk release at the end. Versioning: clear commits and tagged versions so your progress is easy to follow. It costs you almost nothing and it shows up clearly in the best-practices evaluation."

## Context

The repository's history as of 2026-10-02 (`d620569`):

- **Commits**: 44 on `main`. 43 are by the owner, committed straight to `main` (the agreed way of working until now, recorded in `CLAUDE.md`, "Collaboration").
- **Branches**: one feature branch, `003-ui-improvements` (a teammate's). It was merged locally with `--no-ff`; it never went through a pull request on GitHub.
- **Pull requests**: none. The GitHub CLI on the owner's machine is not signed in.
- **Tags**: none, so no version marks any of the seven deployments (Azure revisions 1 to 7).
- **Commit messages**: already descriptive ("Feature 006: progress and replies that follow the inquiry"), but with no common prefix convention.
- **Checks**: no automated checks on GitHub. The gates (tests, build, UI checks, evaluation, secret scan) run on the owner's machine.
  - The backend tests and evaluation need the local data warehouse, which is never committed (constitution IV).

The organizers' best-practices evaluation looks at exactly these signals. The deadline is 2026-10-05.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Every change goes through a feature branch and a pull request (Priority: P1)

A team member starts a change on its own branch, named after the feature or fix. They open a pull request into `main` that describes the change, how it was checked, and its spec. It is merged once its checks pass. `main` only receives merges.

**Why this priority**: it's the most visible signal in the evaluation, and it applies to every change still to come before the deadline (fixes, documentation, the video link, the submission).

**Independent Test**: make one small change (for example, the pending source-label fix on courtesy lines) end to end. Branch, commit, push, open the pull request, see the checks, merge. The change appears on `main` as a merge of a pull request, with its description.

**Acceptance Scenarios**:

1. **Given** a new change, **When** a member starts it, **Then** it happens on a branch named `<type>/<short-name>` or `NNN-<feature>` for a Spec Kit feature, never on `main`.
2. **Given** a branch ready to merge, **Then** a pull request into `main` describes:
   - what changed and why;
   - the spec or task it belongs to;
   - how it was checked (tests, build, UI checks, evaluation if the workflow changed, secret scan).
3. **Given** a pull request, **When** it is merged, **Then** `main` shows it as one merge of that pull request, and the branch is deleted afterwards.
4. **Given** a direct push to `main`, **Then** GitHub refuses it: `main` accepts changes only through a pull request whose checks pass. No approving review is required.
5. **Given** a teammate's branch, **Then** it goes through the same pull request, with the existing safety review: the secret scan on the branch's diff, the tests, the build, and the UI checks, done by the owner (`CLAUDE.md`, "Teammates' branches").

---

### User Story 2 - Tagged versions show the project's progress (Priority: P1)

Each version the judges can see (every deployment) has a tag with a version number and release notes: what it added, its spec, and its live revision. Anyone can follow the progress from the first deployment to the submission.

**Why this priority**: tags turn 44 commits into a readable story of releases, at almost no cost.

**Independent Test**: list the repository's tags and releases. Each deployment has one, in order, with notes naming its features and its live revision.

**Acceptance Scenarios**:

1. **Given** the deployments so far, **Then** each has a version tag on the commit that was deployed, added on 2026-10-02 and saying so in its release notes. From Azure's revision list:

   | Tag | Revision | Commit | What it shipped |
   |---|---|---|---|
   | `v0.1.0` | 1 | `ab130b1` | the first deployment, feature 001 |
   | `v0.1.1` | 2 | `a229b75` | the demo picks fix |
   | `v0.2.0` | 3 | `860c486` | 002, the transcript PDF |
   | `v0.3.0` | 4 | `360f5ad` | 003, the UI improvements |
   | `v0.3.1` | 5 | `aee52bd` | the sign-in fixes |
   | `v0.4.0` | 6 | `c2994a6` | 004 and 005 |
   | `v0.5.0` | 7 | `aec4a64` | 006 and 007 |
2. **Given** a new deployment, **Then** it gets the next version tag, and its release notes list the merged pull requests.
3. **Given** the version numbers, **Then** they follow semantic versioning:
   - `0.MINOR.PATCH`, with MINOR per feature release and PATCH per fix release;
   - the submitted version is the next `0.MINOR.0` release, titled as the hackathon submission (amended 2026-10-02);
   - `1.0.0` is reserved for the first release the team declares stable.
4. **Given** a tag, **Then** it is never moved or deleted once pushed.

---

### User Story 3 - Clear commits (Priority: P2)

Each commit message says what changed in one line, with a conventional type prefix (`feat`, `fix`, `docs`, `test`, `chore`, `ci`). The body says why and how it was checked.

**Why this priority**: messages are already clear, so a prefix convention is a small, visible improvement.

**Independent Test**: read the commits since this feature. Each starts with a type prefix and a one-line summary of at most 72 characters.

**Acceptance Scenarios**:

1. **Given** a new commit, **Then** its first line is `<type>(<optional scope>): <summary>`, 72 characters or fewer.
2. **Given** a commit that changes code, **Then** the gates have passed, and its body or its pull request says so.
3. **Given** the existing history, **Then** it is not rewritten (published commits and the public repository stay as they are).

---

### Edge Cases

- **The secret scan**: its patterns file is private, outside the repository, so it can't run on GitHub. It stays a local gate before every push, recorded in each pull request. A public generic secret check on GitHub may be added, but it doesn't replace the local scan.
- **Checks on GitHub**: the backend tests and the evaluation need the data warehouse, which is never committed, so they can't run there. Automated checks on GitHub cover what can run without data (for example, the frontend build and lint). The rest are reported in the pull request.
- **A hotfix during judging**: still a branch and a pull request, possibly merged within minutes. It gets a PATCH tag when deployed.
- **The `003-ui-improvements` branch**: already merged. It stays as history, or is deleted after this feature.
- **A teammate without the local scan or Docker** (memory, teammate notes): their branch is reviewed and scanned by the owner before the merge, as today.
- **Spec Kit commands**: they keep working on a branch. `.specify/feature.json` points at the feature, not the branch.

## Requirements *(mandatory)*

### Functional Requirements

**Branching and merging (US1)**

- **FR-801**: All new work MUST happen on a branch, named `NNN-<feature>` (Spec Kit features) or `<type>/<short-name>` (fixes, documentation, chores).
- **FR-802**: Changes MUST reach `main` only through a pull request into `main`, merged with a merge commit so each pull request stays visible in the history.
- **FR-803**: Each pull request description MUST state:
  - what changed and why;
  - the spec or task it belongs to;
  - the gates that passed;
  - whether a redeploy is needed.

  A template MUST prompt for these.
- **FR-804**: Automated checks MUST run on each pull request for everything that can run without the private data: at least the frontend build and lint, and a generic secret check. Their result MUST be visible on the pull request.
- **FR-805**: Direct pushes to `main` MUST be refused by GitHub (branch protection). Merges MUST require a pull request with passing checks, and no approving review.
- **FR-806**: Pull requests SHOULD stay small (one feature, fix, or documentation change each) and be merged as soon as their checks pass.

**Versioning (US2, US3)**

- **FR-807**: Each deployment MUST have an annotated version tag on its deployed commit, following semantic versioning (`v0.MINOR.PATCH`; the submission is the next `v0.MINOR.0`, and `v1.0.0` is reserved for a release the team declares stable; amended 2026-10-02). It MUST have release notes naming its features, specs, merged pull requests, and live revision.
- **FR-808**: Tags MUST NOT be moved or deleted once pushed.
- **FR-809**: Commit messages from now on MUST follow `<type>(<scope>): <summary>`, with types `feat`, `fix`, `docs`, `test`, `chore`, `ci`, `refactor`, a first line of 72 characters or fewer, and a body saying why and how it was checked.
- **FR-810**: The way of working MUST be written down where the team reads it: `CLAUDE.md` "Collaboration" (which today says the owner's work goes straight to `main`), the README, and a short contributing guide. The constitution's "Development Workflow" MUST name the pull request as the path to `main` (an amendment, with a version bump).

**Unchanged**

- **FR-811**: The local gates, the secret scan before every push, and the owner's review of teammates' branches stay as they are.
- **FR-812**: Published history is never rewritten.
- **FR-813**: Deployments still need the owner's approval, and they deploy only commits on `main`.

### Key Entities

- **Feature branch**: one change, named per FR-801, deleted after its merge.
- **Pull request**: the only path to `main`. It carries the description (FR-803) and the check results (FR-804).
- **Version tag**: an annotated tag `vX.Y.Z` on a deployed commit, with release notes.
- **Release notes**: per tag, what the version added and where it is live.

## Success Criteria *(mandatory)*

- **SC-801**: From this feature on, 100% of changes on `main` arrive as merges of pull requests. Direct commits: 0.
- **SC-802**: Every deployment, past and future, has a version tag and release notes, so a reader can tell in under a minute what each deployed version added. (The seven past deployments are tagged `v0.1.0` to `v0.5.0`, the live one.)
- **SC-803**: 100% of pull requests show automated check results, and their description states the local gates that passed.
- **SC-804**: 100% of commits from now on follow the message convention.
- **SC-805**: The submission at the deadline is tagged with the next `v0.MINOR.0` (`v0.6.0` unless another release comes first), titled as the hackathon submission, with release notes covering every feature (amended 2026-10-02).

## Assumptions

- **GitHub access**: the owner signs in to GitHub on this machine (the GitHub CLI is installed but not signed in), so pull requests, checks, and releases can be created from the terminal. Otherwise the owner does those steps on the website from the links given.
- **Merging**: pull requests merge with a merge commit, not squash or rebase, so the history shows each pull request and its commits.
- **Review**: one builder does most of the work. A required approving review would block the owner's own pull requests, so the checks passing is the bar, plus the owner's review for teammates.
- **Versions**: the first tag numbers follow the order of deployments (`v0.1.0` for the first deployment). The live revision number stays an Azure detail, recorded in the release notes.
- **Scope**: the GitHub workflow only. No change to the app.

## Amendment 2026-10-02: the submission is not `1.0.0`

The owner pointed out that `1.0.0` signals a stable release, and the submission is a prototype on synthetic data with documented gaps before production (`docs/limitations.md`). The submission is therefore the next `0.MINOR.0` release, titled "hackathon submission". `1.0.0` is reserved for the first release the team declares stable, which cannot come before the production gaps in `docs/limitations.md` are closed. Fixes during the judging freeze are `0.MINOR.PATCH` (`CONTRIBUTING.md`, "After the submission"). FR-807, SC-805, and User Story 2's scenario 3 are amended accordingly.
