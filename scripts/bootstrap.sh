#!/bin/sh
# Make a private Python environment with everything family-ops needs. Idempotent and quiet when ready.
# The system python3 in cloud sessions can lack pdfplumber or ship a broken `cryptography`, so never rely on it.
set -e
cd "$(dirname "$0")/.."
PY=.venv/bin/python
if [ -x "$PY" ] && "$PY" -c "import pdfplumber, yaml, dateutil, requests, playwright, pytest" 2>/dev/null; then
  exit 0
fi
python3 -m venv .venv
.venv/bin/pip install -q --disable-pip-version-check -r requirements.txt
"$PY" -c "import pdfplumber, yaml, dateutil, requests, playwright, pytest"
echo "family-ops: Python environment ready (.venv)" >&2
