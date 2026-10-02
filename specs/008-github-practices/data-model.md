# Data model: GitHub practices

No application data. The "entities" are repository conventions; [contracts/conventions.md](contracts/conventions.md) has the exact patterns.

| Entity | Fields | Rules |
|---|---|---|
| Branch | name | `NNN-<feature>` or `<type>/<short-name>`. Deleted after its merge |
| Pull request | title, description, checks, merge commit | Title follows the commit convention. The description fills the template (FR-803). Merged only when `frontend`, `backend`, and `secrets` pass. Merge commit only |
| Commit | first line, body | Conventional Commits, ≤ 72 characters. The body says why and which gates passed |
| Version tag | name, target commit, message | Annotated, `vMAJOR.MINOR.PATCH`, on a deployed commit of `main`. Never moved or deleted |
| Release | tag, notes, latest flag | One per tag. Notes: features and specs, merged pull requests, Azure revision, date |

**State of a change**: branch → pull request (checks running) → checks pass → merged into `main` (branch deleted) → deployed (owner's approval) → tagged and released.
