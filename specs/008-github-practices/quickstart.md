# Quickstart: checking the GitHub practices

Prerequisite: the GitHub CLI is signed in (`~/.local/bin/gh auth status`).

1. **Hooks**: `git config core.hooksPath .githooks`. Then:
   - `git commit --allow-empty -m "bad message"` is rejected;
   - `git commit --allow-empty -m "chore: hook check"` passes (undo it with `git reset HEAD~1`).
2. **Pull request**: on `008-github-practices`, the pull request into `main` shows the template's sections and the `frontend`, `backend`, and `secrets` checks, all green.
3. **Protection**: after the merge, `git push origin main` with a local commit is refused. `gh api repos/mastersanto/factored-hackathon-2026-problem-crushers/branches/main/protection` shows the required checks and `enforce_admins: true`.
4. **Tags**: `git tag -n1` lists `v0.1.0` … `v0.5.0`, and `git rev-list -n1 v0.5.0` is `aec4a64…`. The repository's Releases page shows seven releases, with `v0.5.0` as latest.
5. **Deploy guard**: `make deploy-azure` from a branch other than `main`, or from a dirty tree, refuses before building.
