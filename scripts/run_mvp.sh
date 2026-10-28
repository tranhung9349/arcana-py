#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
if [ ! -x .venv/bin/python ]; then
  echo 'Tạo môi trường: python3 -m venv .venv'
  echo 'Cài thư viện: .venv/bin/python -m pip install -r requirements.txt'
  exit 1
fi
exec .venv/bin/python -m uvicorn randomyst.api:app --host 127.0.0.1 --port 8765
