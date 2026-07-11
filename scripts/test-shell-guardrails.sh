#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
tmpdir=""

fail() {
  echo "FAIL: $*" >&2
  exit 1
}

cleanup() {
  if [[ -n "${tmpdir:-}" && -d "$tmpdir" ]]; then
    rm -rf "$tmpdir"
  fi
}
trap cleanup EXIT

tmpdir="$(mktemp -d)"

test_generated_clean_before_rebuild() {
  local repo="$tmpdir/generated-order"
  local scripts="$repo/scripts"
  local bin_dir="$repo/bin"
  local log="$repo/calls.log"
  local script

  mkdir -p "$scripts" "$bin_dir"
  cp "$repo_root/scripts/ci-local.sh" "$scripts/ci-local.sh"

  for script in ruff pytest; do
    printf '%s\n' '#!/usr/bin/env bash' 'exit 0' >"$bin_dir/$script"
    chmod +x "$bin_dir/$script"
  done

  for script in validate-xml.sh check-generated-clean.sh build-phyphox.sh compile-arduino.sh test-shell-guardrails.sh secret-scan.sh deps-scan.sh sast-minimal.sh; do
    printf '%s\n' '#!/usr/bin/env bash' "printf '%s\\n' '$script' >> '$log'" >"$scripts/$script"
    chmod +x "$scripts/$script"
  done

  PATH="$bin_dir:$PATH" "$BASH" "$scripts/ci-local.sh" || fail "ci-local guardrail fixture failed"

  if ! awk '
    /check-generated-clean.sh/ { clean = NR }
    /build-phyphox.sh/ { build = NR }
    END { exit !(clean && build && clean < build) }
  ' "$log"; then
    fail "ci-local must check generated files before rebuilding them"
  fi
}

test_missing_sources_fail_before_tool_invocation() {
  local repo="$tmpdir/missing-sources"
  local scripts="$repo/scripts"
  local bin_dir="$repo/bin"
  local log="$repo/tools.log"
  local stdout="$repo/stdout"
  local stderr="$repo/stderr"
  local status

  mkdir -p "$scripts" "$bin_dir"
  cp "$repo_root/scripts/build-phyphox.sh" "$scripts/build-phyphox.sh"
  for script in xmllint python3; do
    printf '%s\n' '#!/usr/bin/env bash' "printf '%s\\n' '$script' >> '$log'" 'exit 0' >"$bin_dir/$script"
    chmod +x "$bin_dir/$script"
  done

  if PATH="$bin_dir:$PATH" "$BASH" "$scripts/build-phyphox.sh" >"$stdout" 2>"$stderr"; then
    fail "build-phyphox unexpectedly succeeded without source files"
  else
    status=$?
  fi

  [[ "$status" -eq 1 ]] || fail "expected missing-source exit 1, got $status"
  grep -F 'No source files found at src/phyphox/*.phyphox.xml' "$stderr" >/dev/null || fail "missing source diagnostic"
  [[ ! -e "$log" ]] || fail "build-phyphox invoked a tool before checking for source files"
}

test_secret_scan_checks_untracked_files() {
  local repo="$tmpdir/untracked-secret"
  local stdout="$repo/stdout"
  local stderr="$repo/stderr"
  local token_prefix='ghp'
  local token="${token_prefix}_012345678901234567890123456789012345"
  local status

  command -v git >/dev/null 2>&1 || fail "git is required for the secret-scan guardrail test"
  command -v rg >/dev/null 2>&1 || fail "rg is required for the secret-scan guardrail test"

  mkdir -p "$repo/scripts"
  cp "$repo_root/scripts/secret-scan.sh" "$repo/scripts/secret-scan.sh"
  git init -q "$repo"
  printf '%s\n' "$token" >"$repo/untracked-token.txt"

  if (cd "$repo" && "$BASH" scripts/secret-scan.sh >"$stdout" 2>"$stderr"); then
    fail "secret-scan unexpectedly accepted an untracked token"
  else
    status=$?
  fi

  [[ "$status" -eq 1 ]] || fail "expected secret-scan exit 1, got $status"
  grep -F 'Potential secret match: untracked-token.txt:1' "$stdout" >/dev/null || fail "untracked token was not reported"
}

test_generated_clean_before_rebuild
test_missing_sources_fail_before_tool_invocation
test_secret_scan_checks_untracked_files

echo "OK"
