#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

require_command() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "$1 not found." >&2
    exit 2
  fi
}

require_command git
require_command rg
require_command python3

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "security.sh must run from a Git worktree." >&2
  exit 2
fi

echo "== Secret scan (tracked and untracked files) =="
secret_patterns=(
  "BEGIN (RSA|EC|OPENSSH) PRIVATE KEY"
  "AKIA[0-9A-Z]{16}"
  "ASIA[0-9A-Z]{16}"
  "xox[baprs]-[0-9A-Za-z-]{10,}"
  "ghp_[0-9A-Za-z]{36}"
  "github_pat_[0-9A-Za-z_]{20,}"
  "glpat-[0-9A-Za-z-]{20,}"
)

matches="$(mktemp)"
files="$(mktemp)"
trap 'rm -f "$matches" "$files"' EXIT

git ls-files -z --cached --others --exclude-standard -- . >"$files"
scan_arguments=(--null --line-number --with-filename)
for pattern in "${secret_patterns[@]}"; do
  scan_arguments+=(--regexp "$pattern")
done
scan_batch() {
  local status=0
  rg "${scan_arguments[@]}" -- "$@" >>"$matches" || status=$?
  if ((status > 1)); then
    echo "Secret scanner failed (exit ${status}); scan is incomplete." >&2
    exit 2
  fi
}

batch=()
while IFS= read -r -d '' file; do
  [[ -f "$file" ]] || continue
  batch+=("$file")
  if ((${#batch[@]} >= 128)); then
    scan_batch "${batch[@]}"
    batch=()
  fi
done <"$files"
if ((${#batch[@]})); then
  scan_batch "${batch[@]}"
fi

if [[ -s "$matches" ]]; then
  while IFS= read -r -d '' file && IFS= read -r line; do
    echo "Potential secret match: ${file}:${line%%:*}"
  done <"$matches"
  echo "Secret scan failed. Remove secrets before proceeding." >&2
  exit 1
fi

echo "== Dependency and configuration sanity =="
python3 - <<'PY'
from __future__ import annotations

import sys
import json
import tomllib
from pathlib import Path

config = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))
project = config.get("project", {})
errors: list[str] = []

if project.get("requires-python") != ">=3.11":
    errors.append("pyproject.toml: project.requires-python must be >=3.11")

dependencies = project.get("dependencies", [])
if not any(isinstance(item, str) and item.startswith("defusedxml") and any(op in item for op in ("<", ">", "=", "~", "!")) for item in dependencies):
    errors.append("pyproject.toml: runtime defusedxml dependency must be version-constrained")

extras = project.get("optional-dependencies", {}).get("test", [])
for package in ("pytest", "ruff"):
    if not any(isinstance(item, str) and item.startswith(package) and any(op in item for op in ("<", ">", "=", "~", "!")) for item in extras):
        errors.append(f"pyproject.toml: test extra must contain a version-constrained {package} dependency")

toolchain = json.loads(Path("scripts/arduino-toolchain.json").read_text(encoding="utf-8"))
pins = [toolchain["core"], *toolchain["libraries"]]
if len(pins) != 6 or any(
    not isinstance(pin, str) or len(pin.split("@")) != 2 or not all(pin.split("@"))
    for pin in pins
):
    errors.append("scripts/arduino-toolchain.json: core and five libraries must be version-pinned")

if errors:
    print("\n".join(errors), file=sys.stderr)
    raise SystemExit(1)
PY

echo "== Shell syntax =="
shell_files=(scripts/*.sh)
for file in "${shell_files[@]}"; do
  bash -n "$file"
done
if command -v shellcheck >/dev/null 2>&1; then
  echo "== shellcheck =="
  shellcheck "${shell_files[@]}"
fi

echo "== Python compile =="
find src tests scripts -type f -name '*.py' -print0 | xargs -0 python3 -c '
from pathlib import Path
import sys
for filename in sys.argv[1:]:
    compile(Path(filename).read_text(encoding="utf-8"), filename, "exec")
'

echo "OK"
