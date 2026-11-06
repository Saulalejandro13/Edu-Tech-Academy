#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
if [ ! -x .venv/bin/python ]; then python3 -m venv .venv; fi
.venv/bin/python -m pip install -r requirements-dev.txt
export PYTHONPATH=src DEMO_SEED=1 DEMO_PASSWORD='DemoSegura2026!'
export DATABASE_URL=sqlite:///./edutech.db
.venv/bin/python -m uvicorn edutech.api.main:app --host 127.0.0.1 --port 8000
