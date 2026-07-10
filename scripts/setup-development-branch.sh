#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "Not inside a Git repository: $ROOT" >&2
  exit 1
fi

if [ -n "$(git status --porcelain)" ]; then
  echo "Working tree is not clean. Commit or stash changes before creating develop." >&2
  exit 1
fi

git fetch origin

if git show-ref --verify --quiet refs/heads/develop; then
  git switch develop
elif git show-ref --verify --quiet refs/remotes/origin/develop; then
  git switch --track origin/develop
else
  git switch main
  git pull --ff-only origin main
  git switch -c develop
  git push -u origin develop
fi

cat <<'MSG'
Development branch is ready.

Recommended GitHub branch protection:
  main: require pull request and passing CI; block force pushes.
  develop: require passing CI; block force pushes.
MSG
