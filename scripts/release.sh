#!/usr/bin/env bash
# Tag a deployed commit of main and publish its GitHub release (specs/008, research R6).
#   scripts/release.sh vX.Y.Z docs/releases/vX.Y.Z.md            # the current main (just deployed)
#   scripts/release.sh vX.Y.Z docs/releases/vX.Y.Z.md --at <sha> # an earlier deployed commit of main
# The notes file's first line is the release title. Tags are annotated and never moved or deleted.
set -euo pipefail
cd "$(dirname "$0")/.."
GH="${GH:-$(command -v gh || echo "$HOME/.local/bin/gh")}"
REPO_URL="https://github.com/mastersanto/factored-hackathon-2026-problem-crushers"

VERSION="${1:-}"; NOTES="${2:-}"; AT=""
[ "${3:-}" = "--at" ] && AT="${4:-}"
die() { echo "release: $*" >&2; exit 1; }

[[ "$VERSION" =~ ^v(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$ ]] || die "version must look like v1.2.3, got '$VERSION'"
[ -f "$NOTES" ] || die "notes file not found: '$NOTES'"
[ "$(git branch --show-current)" = "main" ] || die "run it on main"
[ -z "$(git status --porcelain)" ] || die "the working tree has uncommitted changes"
git fetch -q origin main --tags
[ "$(git rev-parse HEAD)" = "$(git rev-parse origin/main)" ] || die "main is not equal to origin/main (pull or push first)"
git rev-parse -q --verify "refs/tags/$VERSION" >/dev/null && die "tag $VERSION already exists"
git ls-remote --exit-code --tags origin "refs/tags/$VERSION" >/dev/null 2>&1 && die "tag $VERSION already exists on origin"

TARGET="$(git rev-parse "${AT:-HEAD}^{commit}")" || die "unknown commit '$AT'"
git merge-base --is-ancestor "$TARGET" origin/main || die "$TARGET is not on main"

git tag -a "$VERSION" "$TARGET" -F "$NOTES"
git push -q origin "refs/tags/$VERSION"
# Release notes on GitHub: links relative to docs/releases/ become links to the repository.
BODY="$(mktemp)"; trap 'rm -f "$BODY"' EXIT
tail -n +3 "$NOTES" | sed "s#](\.\./\.\./#](${REPO_URL}/blob/main/#g" > "$BODY"
"$GH" release create "$VERSION" --verify-tag --title "$(head -1 "$NOTES")" --notes-file "$BODY"
echo "release: $VERSION -> $(git rev-parse --short "$TARGET")"
