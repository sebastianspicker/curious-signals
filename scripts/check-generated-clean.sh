#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

tmpdir="$(mktemp -d)"
trap 'rm -rf "$tmpdir"' EXIT

bash scripts/build-phyphox.sh "$tmpdir" >/dev/null

shopt -s nullglob
built_files=("$tmpdir"/*.phyphox)
repo_files=(experiments/*.phyphox)

if ((${#built_files[@]} != ${#repo_files[@]})); then
  printf 'Built files: %s\n' "${#built_files[@]}" >&2
  printf 'Repo files: %s\n' "${#repo_files[@]}" >&2
  echo "Generated experiments are not up to date." >&2
  exit 1
fi

for repo_path in "${repo_files[@]}"; do
  built_path="$tmpdir/${repo_path##*/}"
  if [[ ! -f "$built_path" ]]; then
    echo "Missing generated artifact: ${repo_path##*/}" >&2
    echo "Generated experiments are not up to date." >&2
    exit 1
  fi
  if ! cmp -s "$repo_path" "$built_path"; then
    echo "Out-of-date generated artifact: ${repo_path##*/}" >&2
    echo "Generated experiments are not up to date." >&2
    exit 1
  fi
done

echo "OK"
