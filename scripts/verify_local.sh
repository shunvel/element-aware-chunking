#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

echo "==> install check"
command -v python3 >/dev/null || { echo "FAIL: python3 not found"; exit 1; }

echo "==> tests"
make test

echo "==> samples"
if ! ls data/raw/sample_*.pdf >/dev/null 2>&1; then
  make samples
fi

echo "==> eval"
make eval | head -20

if command -v docker >/dev/null 2>&1; then
  echo "==> docker: OK"
  if curl -sf "http://localhost:${QDRANT_PORT:-6343}/collections" >/dev/null 2>&1; then
    echo "==> qdrant: reachable on port ${QDRANT_PORT:-6343}"
  else
    echo "==> qdrant: not reachable (run: make qdrant)"
  fi
else
  echo "==> docker: not installed (skip Qdrant; see docs/SETUP.md)"
fi

echo "==> verify complete"
