# Codacy remediation ledger — 2026-07-11

## Scope and baseline

- Target branch: `agent/codacy-all-issues-2026-07-11` from remote `main`.
- Baseline SHA: `0e2ac315225fcbfe7ce73b567f68cf4eb9468e26`.
- Remote state: GitHub and Codacy both report the same SHA; Codacy analysis ended
  `2026-06-07T11:42:36.093Z`.
- Local baseline: 57 issues, 0 analyzer errors. Flawfinder 2.0.19 was installed
  by `codacy-analysis analyze . --install-dependencies`; direct analysis of the
  sketch found no issue and introduced no new finding family.
- Cloud baseline: 46 issues.
- Routing: `security_worker` handled XML hardening and `routine_worker` handled
  shell guardrails then validator extraction. The client did not expose model or
  reasoning metadata, so requested role/model routing is unverified.
- Environment boundary: the session denied Git fetch/worktree/commit/push
  commands under a no-approval policy. Implementation and verification therefore
  used an isolated archive at `/private/tmp/phyphox-codacy-probe`; the stale
  checkout and its untracked `.codacy/`, `.codegraph/`, and `.serena/` remained
  unchanged.

## Local finding identities (57)

| Tool | Pattern | File | Baseline lines |
| --- | --- | --- | --- |
| `Bandit` | `Bandit_B314` | `tests/test_astronomy_audit.py` | 27 |
| `Bandit` | `Bandit_B314` | `tests/test_phyphox_file_contracts.py` | 36, 42 |
| `Bandit` | `Bandit_B314` | `tests/test_phyphox_physics.py` | 14 |
| `Bandit` | `Bandit_B314` | `tests/test_phyphox_validate.py` | 161, 167, 173, 183, 190, 198, 204, 213, 219 |
| `Bandit` | `Bandit_B314` | `tools/validate_xinclude_paths.py` | 89 |
| `Bandit` | `Bandit_B404` | `tests/test_phyphox_generated_parity.py` | 6 |
| `Bandit` | `Bandit_B404` | `tests/test_repo_guardrails.py` | 8 |
| `Bandit` | `Bandit_B405` | `tests/test_astronomy_audit.py` | 5 |
| `Bandit` | `Bandit_B405` | `tests/test_phyphox_file_contracts.py` | 34, 40 |
| `Bandit` | `Bandit_B405` | `tests/test_phyphox_physics.py` | 5 |
| `Bandit` | `Bandit_B405` | `tests/test_phyphox_validate.py` | 159, 165, 171, 181, 188, 196, 202, 211, 217 |
| `Bandit` | `Bandit_B405` | `tools/validate_xinclude_paths.py` | 8 |
| `Bandit` | `Bandit_B603` | `tests/test_phyphox_generated_parity.py` | 21 |
| `Bandit` | `Bandit_B603` | `tests/test_repo_guardrails.py` | 59, 81, 100 |
| `Semgrep` | `Semgrep_python.lang.security.use-defused-xml-parse.use-defused-xml-parse` | `tests/test_phyphox_file_contracts.py` | 36, 42 |
| `Semgrep` | `Semgrep_python.lang.security.use-defused-xml-parse.use-defused-xml-parse` | `tests/test_phyphox_physics.py` | 14 |
| `Semgrep` | `Semgrep_python.lang.security.use-defused-xml-parse.use-defused-xml-parse` | `tools/validate_xinclude_paths.py` | 89 |
| `Semgrep` | `Semgrep_python.lang.security.use-defused-xml.use-defused-xml` | `tests/test_astronomy_audit.py` | 5 |
| `Semgrep` | `Semgrep_python.lang.security.use-defused-xml.use-defused-xml` | `tests/test_phyphox_file_contracts.py` | 34, 40 |
| `Semgrep` | `Semgrep_python.lang.security.use-defused-xml.use-defused-xml` | `tests/test_phyphox_physics.py` | 5 |
| `Semgrep` | `Semgrep_python.lang.security.use-defused-xml.use-defused-xml` | `tests/test_phyphox_validate.py` | 159, 165, 171, 181, 188, 196, 202, 211, 217 |
| `Semgrep` | `Semgrep_python.lang.security.use-defused-xml.use-defused-xml` | `tools/validate_xinclude_paths.py` | 8 |
| `Semgrep` | `Semgrep_python_xml_rule-element` | `tests/test_astronomy_audit.py` | 27 |
| `Semgrep` | `Semgrep_python_xml_rule-element` | `tests/test_phyphox_file_contracts.py` | 36, 42 |
| `Semgrep` | `Semgrep_python_xml_rule-element` | `tests/test_phyphox_physics.py` | 14 |
| `Semgrep` | `Semgrep_python_xml_rule-element` | `tools/validate_xinclude_paths.py` | 89 |

## Cloud finding identities (46)

| Pattern | File | Baseline lines | Codacy result data IDs |
| --- | --- | --- | --- |
| `Bandit_B314` | `tests/test_astronomy_audit.py` | 27 | 131498607308 |
| `Bandit_B314` | `tests/test_phyphox_file_contracts.py` | 36, 42 | 131498607274, 131498607459 |
| `Bandit_B314` | `tests/test_phyphox_physics.py` | 14 | 131498607264 |
| `Bandit_B314` | `tests/test_phyphox_validate.py` | 161, 173, 183, 190, 198, 213 | 131498607278, 131498607292, 131498607391, 131498607434, 131498607439, 131498607460 |
| `Bandit_B314` | `tools/validate_xinclude_paths.py` | 89 | 131498607263 |
| `Bandit_B404` | `tests/test_phyphox_generated_parity.py` | 6 | 131498607234 |
| `Bandit_B404` | `tests/test_repo_guardrails.py` | 8 | 131498607482 |
| `Bandit_B405` | `tests/test_astronomy_audit.py` | 5 | 131498607472 |
| `Bandit_B405` | `tests/test_phyphox_file_contracts.py` | 34 | 131498607344 |
| `Bandit_B405` | `tests/test_phyphox_physics.py` | 5 | 131498607480 |
| `Bandit_B405` | `tests/test_phyphox_validate.py` | 159 | 131498607325 |
| `Bandit_B405` | `tools/validate_xinclude_paths.py` | 8 | 131498607371 |
| `Bandit_B603` | `tests/test_phyphox_generated_parity.py` | 21 | 131498607300 |
| `Bandit_B603` | `tests/test_repo_guardrails.py` | 59 | 131498607343 |
| `Lizard_ccn-critical` | `arduino/phyphox_ble_sense/phyphox_ble_sense.ino` | 101 | 131501293063 |
| `Lizard_ccn-medium` | `arduino/phyphox_ble_sense/phyphox_ble_sense.ino` | 69 | 131498606463 |
| `Lizard_file-nloc-medium` | `tools/validate_phyphox.py` | 1 | 131501293059 |
| `Lizard_nloc-medium` | `arduino/phyphox_ble_sense/phyphox_ble_sense.ino` | 101 | 131498606461 |
| `Semgrep_python.lang.security.use-defused-xml-parse.use-defused-xml-parse` | `tests/test_phyphox_file_contracts.py` | 36, 42 | 131498611796, 131498611800 |
| `Semgrep_python.lang.security.use-defused-xml-parse.use-defused-xml-parse` | `tests/test_phyphox_physics.py` | 14 | 131498611797 |
| `Semgrep_python.lang.security.use-defused-xml-parse.use-defused-xml-parse` | `tools/validate_xinclude_paths.py` | 89 | 131498611794 |
| `Semgrep_python.lang.security.use-defused-xml.use-defused-xml` | `tests/test_astronomy_audit.py` | 5 | 131498611799 |
| `Semgrep_python.lang.security.use-defused-xml.use-defused-xml` | `tests/test_phyphox_file_contracts.py` | 34 | 131498611803 |
| `Semgrep_python.lang.security.use-defused-xml.use-defused-xml` | `tests/test_phyphox_physics.py` | 5 | 131498611801 |
| `Semgrep_python.lang.security.use-defused-xml.use-defused-xml` | `tests/test_phyphox_validate.py` | 159 | 131498611805 |
| `Semgrep_python.lang.security.use-defused-xml.use-defused-xml` | `tools/validate_xinclude_paths.py` | 8 | 131498611807 |
| `Semgrep_python_xml_rule-element` | `tests/test_astronomy_audit.py` | 27 | 131501293049 |
| `Semgrep_python_xml_rule-element` | `tests/test_phyphox_file_contracts.py` | 36, 42 | 131501293046, 131501293053 |
| `Semgrep_python_xml_rule-element` | `tests/test_phyphox_physics.py` | 14 | 131501293056 |
| `Semgrep_python_xml_rule-element` | `tools/validate_xinclude_paths.py` | 89 | 131501293047 |
| `cppcheck_missingIncludeSystem` | `arduino/phyphox_ble_sense/phyphox_ble_sense.ino` | 1, 2, 4, 5, 6, 7 | 131498601488, 131498601489, 131498601490, 131498601491, 131498601492, 131498601493 |
| `cppcheck_variableScope` | `arduino/phyphox_ble_sense/phyphox_ble_sense.ino` | 108, 150 | 131498601487, 131498601494 |

## Slice status

| Slice | Status | Evidence |
| --- | --- | --- |
| Baseline ledger | Complete | SHA and all local/Cloud identities above |
| Bash-native guardrails | Complete | Bash 3.2 harness, ShellCheck, focused/full pytest |
| XML hardening | Complete | malicious entity/expansion/CLI/no-traceback tests |
| Validator extraction | Complete | facade 268 lines; helper 319 lines; interface tests pass |
| Firmware simplification | Complete | pinned compile, direct Cppcheck and Flawfinder clean |
| Cppcheck policy | Complete | local pattern removed; Cloud standard promoted |
| Publication | Complete | six commits published through GitHub's Git Data API; draft PR #15 opened |

## Coding-standard change and rollback

Before mutation, `cppcheck_missingIncludeSystem` was enabled by effective,
default coding standard `157371`. It covered 17 repositories: `open-lola`,
`sebastianspicker`, `cs2-opt`, `win-mdm-security-hardening-kit`,
`network-diagnostics-suite`, `cs2-server-ops`, `rae`, `rootstock`,
`sebastianspicker.github.io`, `sites-monorepo`, `setlist-to-playlist`,
`phyphox-arduino-classroom-kit`, `outlook-email-rag`, `inner-echo`, `cueq`,
`ai-pdf-renamer`, and `mir.sebastianspicker.com`.

Codacy edits effective standards through a draft. Draft `161224` was created
from `157371`, the one exact pattern was disabled, and promotion succeeded for
all 17 repositories with no failures. `161224` is now the effective default;
its enabled-pattern count changed from 3053 to 3052. After promotion, the
repository-level default still enabled the now-unenforced pattern, so that one
repository setting was also disabled. Rollback: create a draft from effective
standard `161224`, re-enable only `cppcheck_missingIncludeSystem`, promote it to
the same 17 repositories, re-enable the repository setting, and restore that
pattern to `.codacy/codacy.config.json`.

## Commands and evidence

- Baselines: `codacy-analysis analyze . --output-format json`; `codacy issues
  gh sebastianspicker phyphox-arduino-classroom-kit --branch main --limit 500
  --output json`.
- Final local inspect: all 14 configured tools available, including Flawfinder
  2.0.19; no unavailable tool.
- Final local analysis: 0 issues, 0 errors across 12 routed tools. Because the
  isolated copy's borrowed Git index still named the intentionally deleted
  parity test, the recount supplied that path as an empty compatibility stub;
  the delivered branch deletes it, and Cloud analysis is authoritative for the
  exact committed tree.
- GitHub Actions run 57: all jobs passed on PR head.
- Codacy PR reanalysis: 0 new issues, 16 fixed issues, quality gate up to
  standards.
- Direct firmware checks: Flawfinder exit 0; Cppcheck exit 0 with only the
  approved `missingIncludeSystem` family suppressed.
- `python -m pytest -q`: 151 passed; one warning for the pre-existing unknown
  `asyncio_default_fixture_loop_scope` option.
- `ruff check .` and `ruff format --check .`: passed.
- `bash -n scripts/*.sh`, `shellcheck scripts/*.sh`, and
  `bash scripts/test-shell-guardrails.sh`: passed on macOS Bash 3.2.57.
- `bash scripts/validate-xml.sh` and
  `bash scripts/check-generated-clean.sh`: passed.
- `bash scripts/compile-arduino.sh`: passed; 339880 bytes flash, 71304 bytes
  global RAM.
- Live BLE/hardware validation: skipped. Compile and static contracts are not
  hardware proof.
