#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

if ! command -v ruff >/dev/null 2>&1; then
  echo "ruff not found. Install test dependencies first (see requirements-test.txt)." >&2
  exit 2
fi

if ! command -v pytest >/dev/null 2>&1; then
  echo "pytest not found. Install test dependencies first (see requirements-test.txt)." >&2
  exit 2
fi

echo "== Ruff =="
ruff check .
ruff format --check .

echo
echo "== Pytest =="
pytest

echo
echo "== XML + phyphox validation =="
bash scripts/validate-xml.sh

echo
echo "== Rebuild generated experiments =="
bash scripts/build-phyphox.sh
bash scripts/check-generated-clean.sh

echo
echo "== Arduino compile =="
bash scripts/compile-arduino.sh

echo
echo "== Security baseline =="
bash scripts/secret-scan.sh
bash scripts/deps-scan.sh
bash scripts/sast-minimal.sh

echo
echo "OK"
