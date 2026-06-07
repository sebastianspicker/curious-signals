#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

if ! command -v git >/dev/null 2>&1; then
  echo "git not found." >&2
  exit 2
fi

if ! command -v rg >/dev/null 2>&1; then
  echo "rg not found. Install ripgrep to run the secret scan." >&2
  exit 2
fi

# Basic secret patterns. Keep this list tight to avoid noise.
# Note: output is parsed as file:lineno:content; filenames containing colons may be misparsed.
patterns=(
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

git ls-files -z --cached --others --exclude-standard -- . >"$files"
trap 'rm -f "$matches" "$files"' EXIT

is_excluded_analysis_path() {
  case "$1" in
    docs/archive/*|docs/deprecated/*|docs/ci/*|reference/*) return 0 ;;
    *) return 1 ;;
  esac
}

found=0
for pat in "${patterns[@]}"; do
  while IFS= read -r -d '' file; do
    [[ -f "$file" ]] || continue
    if is_excluded_analysis_path "$file"; then
      continue
    fi
    if rg --null --line-number --with-filename --regexp "$pat" -- "$file" >>"$matches"; then
      found=1
    fi
  done <"$files"
done

if ((found == 1)); then
  while IFS= read -r -d '' file && IFS= read -r line; do
    lineno="${line%%:*}"
    echo "Potential secret match: ${file}:${lineno}"
  done <"$matches"
  echo "Secret scan failed. Remove secrets or add safe handling before proceeding." >&2
  exit 1
fi

echo "OK"
