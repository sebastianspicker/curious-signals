#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

if ! command -v xmllint >/dev/null 2>&1; then
  echo "xmllint not found. Install libxml2 utilities first." >&2
  exit 2
fi

if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 not found." >&2
  exit 2
fi

# Optional: output directory for *.phyphox (default: experiments/)
PHYPHOX_OUTDIR="${PHYPHOX_OUTDIR:-$repo_root/experiments}"
if [[ -n "${1:-}" ]]; then
  PHYPHOX_OUTDIR="$1"
fi
mkdir -p "$PHYPHOX_OUTDIR"

shopt -s nullglob

src_files=(src/phyphox/*.phyphox.xml)
if ((${#src_files[@]} == 0)); then
  echo "No source files found at src/phyphox/*.phyphox.xml"
  exit 0
fi

tmp="$(mktemp)"
trap 'rm -f "$tmp"' EXIT

for src in "${src_files[@]}"; do
  out="${src##*/}"
  out="${out%.xml}" # foo.phyphox.xml -> foo.phyphox
  outpath="$PHYPHOX_OUTDIR/$out"

  xmllint --xinclude "$src" | python3 tools/postprocess_phyphox_xml.py >"$tmp"
  cp "$tmp" "$outpath"
done

echo "Built ${#src_files[@]} phyphox files."
if [[ "$PHYPHOX_OUTDIR" != "$repo_root/experiments" ]]; then
  echo "Output: $PHYPHOX_OUTDIR"
fi
