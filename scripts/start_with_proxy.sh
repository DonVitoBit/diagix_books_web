#!/bin/sh
# Запуск Streamlit с опциональным прокси (исходящие API).
# На сервере создайте scripts/proxy.env по образцу scripts/proxy.env.example (файл в .gitignore).

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [ -f "$ROOT/scripts/proxy.env" ]; then
  set -a
  # shellcheck source=/dev/null
  . "$ROOT/scripts/proxy.env"
  set +a
fi

exec ./venv/bin/python run_web_app.py --host 0.0.0.0 --port 8501 "$@"
