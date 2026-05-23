#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BACKEND="$ROOT/apps/backend"
VENV_PY="$BACKEND/.venv/bin/python"

if [[ ! -x "$VENV_PY" ]]; then
  python3 -m venv "$BACKEND/.venv"
  "$VENV_PY" -m pip install -q -r "$BACKEND/requirements.txt" -r "$BACKEND/requirements-dev.txt"
fi

cd "$BACKEND"
exec "$VENV_PY" -m pytest tests/ -v "$@"
