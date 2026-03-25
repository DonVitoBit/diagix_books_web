#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if [[ ! -f "requirements.txt" ]]; then
  echo "requirements.txt not found; run from project root."
  exit 2
fi

PY="${PYTHON:-python3}"

if [[ ! -d ".venv" ]]; then
  "$PY" -m venv .venv
fi

# shellcheck disable=SC1091
source .venv/bin/activate

python -m pip install -U pip
python -m pip install -r requirements.txt

exec python run_web_app.py "$@"
