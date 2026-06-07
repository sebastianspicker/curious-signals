# Remediation Status

Updated: 2026-05-16.

Overall state: BLOCKED.

Current slice: none.

Counts by status:

- NOT_STARTED: 0
- IN_PROGRESS: 0
- BLOCKED: 2
- DEFERRED: 2
- IMPLEMENTED: 0
- VERIFIED: 0
- COMPLETE: 11

Highest remaining priority: 2, correctness/runtime guardrails.

Last commands/result:

- `pytest tests/test_repo_guardrails.py`: PASS, 7 passed.
- `ruff check tests/test_repo_guardrails.py`: PASS.
- `bash scripts/check-generated-clean.sh`: PASS, `OK`.
- `bash scripts/build-phyphox.sh /private/tmp/phyphox-build-check-r02`: PASS,
  built 7 files in a temp output directory.
- `pytest tests/test_astronomy_semantics.py`: PASS, 7 passed after R04.
- `pytest tests/test_astronomy_audit.py tests/test_astronomy_consolidation.py`:
  PASS, 14 passed.
- `ruff check tests/test_astronomy_semantics.py`: PASS.
- `bash scripts/validate-xml.sh`: PASS, `OK`.
- `pytest tests/test_phyphox_validate.py tests/test_phyphox_file_contracts.py`:
  PASS, 82 passed.
- `ruff check tools/validate_phyphox.py tests/test_phyphox_validate.py`: PASS.
- `pytest tests/test_repo_guardrails.py tests/test_phyphox_validate.py tests/test_astronomy_semantics.py`:
  PASS, 73 passed.
- `ruff check tests/test_repo_guardrails.py tests/test_phyphox_validate.py tests/test_astronomy_semantics.py`:
  PASS.
- `pytest tests/test_repo_guardrails.py`: PASS, 8 passed.
- `git diff --name-only`: inspected changed/deleted tracked files; the tracked
  `.github/dependabot.yml` deletion remains pre-existing and unresolved.
- `git diff --stat`: inspected total change shape, 16 tracked paths changed or
  deleted.
- `ruff format --check .`: PASS, 14 files already formatted.
- `pytest`: PASS, 145 passed.
- `bash scripts/validate-xml.sh`: PASS, `OK`.
- `bash scripts/check-generated-clean.sh`: PASS, `OK`.
- `bash scripts/build-phyphox.sh /private/tmp/phyphox-final-build`: PASS, built
  7 files in a temp output directory.
- `bash scripts/sast-minimal.sh`: PASS.
- `bash scripts/deps-scan.sh`: PASS, `OK`.
- `bash scripts/secret-scan.sh`: PASS, `OK`.
- `bash scripts/compile-arduino.sh`: failed once in sandbox with Arduino index
  update error, then PASS after escalation; sketch uses 339784 bytes and exits
  `OK`.
- `rg -n "NOT_STARTED|IN_PROGRESS|Pending" docs/remediation-ledger.md docs/remediation-status.md`:
  PASS for completion audit; only zero-count status lines remain.
- `rg -n "\\| R[0-9]+ \\|" docs/refactor-plan.md docs/remediation-ledger.md`:
  PASS for completion audit; R01 through R15 are represented in the ledger.
- `nl -ba arduino/phyphox_ble_sense/phyphox_ble_sense.ino | sed -n '1,260p'`:
  confirms the BLE payload is still only five float32 values, sensor-missing
  paths still emit `NaN`, and there is no status/error characteristic.
- `cat experiments/phyphox_constants.json`: confirms active mode IDs and
  reserved modes only; no unavailable/error protocol is defined there.
- `rg -n "R09|R14|LC-009|unavailable|sensor failure|NaN|live BLE" docs/logic-and-correctness-audit.md docs/architecture-map.md docs/refactor-plan.md docs/remediation-ledger.md docs/remediation-status.md`:
  confirms the plan and audits require live BLE/phyphox evidence for R09/R14.
- `arduino-cli board list`: no Arduino Nano 33 BLE Sense detected; only
  `/dev/cu.Bluetooth-Incoming-Port` and `/dev/cu.debug-console` are listed as
  unknown serial ports.
- `ls /dev/cu.*`: no Arduino USB serial device path is visible.
- `git remote -v`: origin is
  `https://github.com/sebastianspicker/phyphox-arduino-classroom-kit`.
- `gh repo view --json nameWithOwner,visibility,defaultBranchRef`: repository
  is public and default branch is `main`.
- `gh api repos/sebastianspicker/phyphox-arduino-classroom-kit/contents/.github/dependabot.yml`:
  returns HTTP 404.
- `git status --short --branch`: local `main` is behind `origin/main` by one
  commit, with `.github/dependabot.yml` deleted in the worktree.
- `git ls-tree -r origin/main -- .github/dependabot.yml`: no file listed.
- `git log --oneline HEAD..origin/main`: remote-only commit is
  `4fd276c chore: disable dependabot updates`.
- `git show --name-status --oneline origin/main -- .github/dependabot.yml`:
  confirms `4fd276c` deletes `.github/dependabot.yml`.
- `git diff --check`: PASS.
- `git diff --name-only`: inspected the current changed/deleted tracked-file
  set after the latest ledger/status updates.
- `rg -n "NOT_STARTED|IN_PROGRESS|Pending|BLOCKED: 3|COMPLETE: 10|R09, R12|R12 are blocked|Current slice: R" docs/remediation-ledger.md docs/remediation-status.md`:
  PASS for status consistency; only zero-count status lines remain.
- `rg -n "\\| R0?[0-9]+ \\||\\| R1[0-5] \\|" docs/remediation-ledger.md`:
  PASS for ledger coverage; R01 through R15 are present.
- `rg -n "NaN|unavailable sensor|unavailable-sensor|stale sample|No data / flat plot" README.md docs/RUNBOOK.md arduino/phyphox_ble_sense/README.md docs/remediation-ledger.md docs/remediation-status.md`:
  PASS for R09 documentation visibility; firmware README, README, and runbook
  now state the current `NaN` unavailable-sensor contract.
- `git diff --check`: PASS after the R09 documentation clarification.
- `rg -n 'Rounded to the nearest|mode \(1–9\)|mode \(1-9\)|1–9|accepts only raw values `1\.\.9`|rounds config|full range `1\.\.9`' README.md docs arduino/phyphox_ble_sense/README.md`:
  PASS for current docs; only the original logic audit finding still contains
  historical pre-R08 `1..9` evidence.
- `git diff --check`: PASS after R08 documentation alignment.
- `rg -n "accepts the full range|accepts only raw values|reserved.*fall through|reserved.*silently|roundf|rounds config|mode.*1\\.\\.9|1\\.\\.9|1–9|1-9|Mode::kAnalogInputs|reserved modes" docs README.md arduino src experiments/phyphox_constants.json`:
  PASS for current-doc sweep; remaining stale-behavior references are historical
  audit evidence or live code symbols, not current operator guidance.
- `ruff check .`: PASS after latest documentation/status updates.
- `pytest`: PASS, 145 passed after latest documentation/status updates.
- `bash scripts/validate-xml.sh`: PASS, `OK` after latest documentation/status
  updates.
- `git diff --check`: PASS after latest documentation/status updates.
- `arduino-cli board list`: fresh probe still shows no Arduino Nano 33 BLE
  Sense; only `/dev/cu.Bluetooth-Incoming-Port` and `/dev/cu.debug-console` are
  listed as unknown serial ports.
- `ls /dev/cu.*`: fresh probe still shows only Bluetooth/debug serial ports.
- `ruff check tests/test_repo_guardrails.py`: PASS.
- `bash scripts/compile-arduino.sh`: failed once in sandbox with Arduino index
  update error, then PASS after escalation; sketch uses 339784 bytes and exits
  `OK`.
- `rg -n "agent\\.md|docs/ci|ci-decision|deprecated/audit|owon|Owon|debug" README.md docs .gitignore`:
  PASS for R11; remaining hits are intentional current docs, archive/audit
  evidence, or inventory references.
- `pytest tests/test_astronomy_audit.py tests/test_astronomy_consolidation.py tests/test_astronomy_semantics.py`:
  PASS, 21 passed.
- `ruff check .`: PASS.
- `git log --oneline -- .github/dependabot.yml`: PASS for R12 inspection;
  tracked history exists.
- `git show HEAD:.github/dependabot.yml`: PASS for R12 inspection; tracked
  config monitors GitHub Actions and pip weekly.
- `rg -n "dependabot|Dependency|dependencies" .github docs README.md pyproject.toml requirements-test.txt`:
  PASS for R12 inspection.
- `bash scripts/sast-minimal.sh`: initially failed after an attempted R13 Bash
  regex simplification; PASS after moving the regex into a variable.
- `shellcheck scripts/*.sh`: initially failed on the same R13 regex; PASS after
  the fix.
- `bash scripts/deps-scan.sh`: PASS.
- `bash scripts/secret-scan.sh`: PASS.
- `bash scripts/build-phyphox.sh /private/tmp/phyphox-build-check-r13`: PASS,
  built 7 files in a temp output directory.
- `pytest tests/test_repo_guardrails.py`: PASS, 8 passed.

Uncertainty:

- Live hardware, BLE, phyphox app, SensorTag, and Owon checks are not available
  yet in this run.
- Hardware probing found no Arduino Nano 33 BLE Sense attached; only unknown
  Bluetooth/debug serial ports were visible.
- Arduino compile may require network/index access outside the default sandbox.

Completed slices:

- R01: generated-clean now runs before in-place generated rebuild in
  `scripts/ci-local.sh`.
- R02: missing source XML now fails `scripts/build-phyphox.sh`.
- R03: astronomy semantic guardrails now check duplicate containers and unknown
  references.
- R04: removed the duplicate `factor2` container from
  `experiments/astronomy/tidal-locking.phyphox`.
- R05: tightened mode and BLE offset validation with regression tests.
- R06: removed a remaining literal workflow/script assertion after adding
  behavior-level guardrail coverage.
- R07: initial config characteristic now matches default acceleration mode.
- R08: reserved/fractional mode writes are explicitly rejected instead of
  accepted via broad range handling, and current docs now describe active config
  modes as `1`-`6` or `9`.
- R11: current docs now route CI through `docs/ci.md`, remove stale current
  `agent.md` guidance, mark deprecated audit material as archive-only, and
  classify the Owon debug file as auxiliary.
- R12: Dependabot removal is intentional remote default-branch state; local
  deletion matches `origin/main` commit `4fd276c chore: disable dependabot
  updates`.
- R13: simplified the dependency and secret scan scripts without changing their
  command contracts.

Blocked slices:

- R09: unavailable-sensor surfacing needs a protocol/UI decision and live BLE
  app evidence; the existing `NaN` contract is now visible in README/RUNBOOK,
  but no live phyphox proof is available.
- R14: firmware mode-dispatch simplification depends on R09's unavailable-mode
  semantics and live BLE probes for all active modes. No safe style refactor was
  made without that evidence.

Deferred slices:

- R10: astronomy formula guards need live phyphox expression/runtime evidence
  before changing calculations safely.
- R15: additional XML deduplication would be maintainability churn without a
  narrow generated-source candidate and phyphox import/runtime proof.

Completion audit:

- R01, R02, R03, R04, R05, R06, R07, R08, R11, R12, and R13 are complete.
- R09 and R14 are blocked by missing external runtime evidence.
- R10 and R15 are deferred because the safe next step is runtime/import evidence,
  not blind formula/XML churn.
- No planned slice remains `NOT_STARTED` or `IN_PROGRESS`.
- Final remediation cannot be marked `COMPLETE` while high-risk R09/R14 remain
  blocked by missing protocol/UI decisions and live BLE/phyphox evidence.

Prompt-to-artifact checklist:

- Deliverable: remediate all actionable issues from `docs/refactor-plan.md`.
  Evidence: `docs/remediation-ledger.md` maps R01 through R15 to a status,
  files changed, tests, verification, uncertainty, and last note.
- Deliverable: use `docs/refactor-plan.md` as source of truth. Evidence:
  ledger rows use the plan's slice IDs and titles; no extra unplanned slice is
  listed.
- Deliverable: process one bounded slice at a time. Evidence: ledger records
  per-slice status and verification; status file records current slice as
  `none` after all slices were evaluated.
- Deliverable: complete required/actionable slices or justify deferral/blocker.
  Evidence: R01, R02, R03, R04, R05, R06, R07, R08, R11, R12, and R13 are
  `COMPLETE`; R09 and R14 are `BLOCKED`; R10 and R15 are `DEFERRED`.
- Deliverable: high-risk/P1 slices complete unless externally blocked. Evidence:
  R07 and R08 are complete; R09 and R14 are blocked by missing live BLE/phyphox
  evidence and protocol/UI decisions, not by unstarted implementation work.
- Deliverable: final verification passes or skipped checks are documented.
  Evidence: final commands above record passing Ruff, format, pytest, XML,
  generated-clean, temp build, SAST, dependency scan, secret scan, and Arduino
  compile checks; skipped live BLE/phyphox/SensorTag/Owon checks are documented
  as uncertainty.
- Deliverable: inspect actual current state before claiming completion.
  Evidence: final audit commands above inspect the ledger/status, refactor plan,
  `git status`, firmware code, constants JSON, and R09/R14 audit references.
- Deliverable: mark final status `COMPLETE` only if no high-risk blocker remains.
  Evidence: overall state remains `BLOCKED`; goal must not be marked complete
  until R09/R14 are resolved or explicitly re-scoped by the repository owner.

Unblock criteria:

- R09 can resume only after a repository owner chooses the unavailable-sensor
  contract if the existing five-float `NaN` semantics are not acceptable. If the
  existing contract remains, it still needs a live phyphox app probe on Arduino
  Nano 33 BLE Sense hardware before implementation is marked complete.
- R14 can resume only after R09 is resolved and live probes confirm payload
  bytes, timing, and channel semantics for every active mode: acceleration,
  gyroscope, magnetometer, pressure, temperature/humidity, light/RGB, and analog
  inputs.
- Final status can become `COMPLETE` only after R09/R14 are complete or the
  repository owner explicitly re-scopes those high-risk runtime slices out of
  this remediation goal.

Required live probe checklist:

- Connect an Arduino Nano 33 BLE Sense that appears in `arduino-cli board list`
  as a usable board, not only as an unknown serial port.
- Flash `arduino/phyphox_ble_sense/phyphox_ble_sense.ino`.
- Import each generated core experiment from `experiments/` into the phyphox
  app.
- For R09, induce or observe unavailable/stale sensor conditions and verify the
  app presents blank, missing, or `NaN` values in a way that cannot be mistaken
  for valid zero measurements.
- For R14, run every active mode (`1`-`6`, `9`) and record that payload timing,
  channel meaning, and mode switching still match the documented BLE contract.
- If any probe cannot be run, record the exact missing device/app condition and
  keep R09/R14 blocked.
