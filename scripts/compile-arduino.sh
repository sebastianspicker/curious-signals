#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

if ! command -v arduino-cli >/dev/null 2>&1; then
  echo "arduino-cli not found. Install it first (see README.md)." >&2
  exit 1
fi

python3 scripts/arduino_toolchain.py verify
fqbn="$(python3 scripts/arduino_toolchain.py fqbn)"
arduino-cli compile --fqbn "$fqbn" arduino/phyphox_ble_sense

echo "OK"
