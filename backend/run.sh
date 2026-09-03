#!/usr/bin/env bash
# Start the Music Key Changer backend (serves frontend/ on /).
# Uses backend/.venv if present, else the current python.
set -euo pipefail
cd "$(dirname "$0")"

if [ -d .venv ]; then
  VENV_BIN=".venv/bin"
else
  if command -v python3 >/dev/null 2>&1; then
    VENV_BIN=""
  else
    echo "No .venv found and python3 not available." >&2
    exit 1
  fi
fi

exec "${VENV_BIN}/python" -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
