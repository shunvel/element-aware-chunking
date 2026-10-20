#!/usr/bin/env bash
# Create GitHub repo element-aware-chunking and push (requires GitHub CLI: brew install gh)
set -euo pipefail
cd "$(dirname "$0")/.."

REPO_OWNER="shunvel"
REPO_NAME="element-aware-chunking"
DESC="Element-aware chunking design patterns for RAG — text, tables & images, Qdrant, visual diffs, eval."

if ! command -v gh >/dev/null; then
  echo "Install GitHub CLI: brew install gh && gh auth login"
  exit 1
fi

if git remote get-url origin >/dev/null 2>&1; then
  echo "origin already set: $(git remote get-url origin)"
else
  gh repo create "$REPO_OWNER/$REPO_NAME" --public --description "$DESC" --source=. --remote=origin --push
fi

while read -r topic; do
  [[ -z "$topic" || "$topic" =~ ^# ]] && continue
  gh repo edit "$REPO_OWNER/$REPO_NAME" --add-topic "$topic"
done < .github/TOPICS.txt

echo "Done: https://github.com/$REPO_OWNER/$REPO_NAME"
