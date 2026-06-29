#!/usr/bin/env bash
set -euo pipefail

REPO_NAME="${1:-universal-rag-evaluator}"
VISIBILITY="${2:-public}"

if ! command -v gh >/dev/null 2>&1; then
  echo "GitHub CLI (gh) is required: https://cli.github.com/" >&2
  exit 1
fi

gh auth status >/dev/null
if [[ ! -d .git ]]; then
  git init -b main
fi

git add .
if ! git diff --cached --quiet; then
  git commit -m "feat: initial universal RAG evaluator"
fi

gh repo create "$REPO_NAME" --"$VISIBILITY" --source=. --remote=origin --push
