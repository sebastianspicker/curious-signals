# Verification Baseline

Baseline established on 2026-05-16 from the repository root.

This is a verification record, not a remediation pass. No production code was
changed. Existing worktree state before this pass included a deleted tracked
`.github/dependabot.yml` plus untracked `AGENTS.md` and `docs/code-index.md`.

## Environment

- Shell: `zsh`
- `python3`: `/opt/homebrew/bin/python3`, `Python 3.14.5`
- `pytest`: `/opt/anaconda3/bin/pytest`, `pytest 8.3.4`
- Pytest runtime reported: Python `3.13.5`
- `ruff`: `/opt/anaconda3/bin/ruff`, `ruff 0.14.14`
- `xmllint`: `/usr/bin/xmllint`, libxml `20913` with XInclude support
- `arduino-cli`: `/opt/homebrew/bin/arduino-cli`, version `1.4.1`
- `rg`: `/opt/homebrew/bin/rg`
- `shellcheck`: `/opt/homebrew/bin/shellcheck`
- `git`: `/usr/bin/git`
- `zip`: `/usr/bin/zip`

Note: `python3` and `pytest` come from different installations. The current
baseline is still valid for the commands as run, but future failures may depend
on which Python environment is first on `PATH`.

## Commands Discovered

Dependency installation:

```sh
python3 -m pip install -r requirements-test.txt
```

System/toolchain prerequisites:

```sh
brew install libxml2 arduino-cli
```

Lint and format check:

```sh
ruff check .
ruff format --check .
make lint
```

Unit tests:

```sh
pytest
make test
```

XML, phyphox, and generated-file validation:

```sh
bash scripts/validate-xml.sh
make validate
bash scripts/build-phyphox.sh
bash scripts/check-generated-clean.sh
make build
```

Arduino firmware compile:

```sh
bash scripts/compile-arduino.sh
make compile
```

Security/static checks:

```sh
bash scripts/secret-scan.sh
bash scripts/deps-scan.sh
bash scripts/sast-minimal.sh
make security
```

Full local gate:

```sh
bash scripts/ci-local.sh
make ci-local
make ci
```

Bundle artifact:

```sh
make bundle
```

Manual runtime checks:

- Flash `arduino/phyphox_ble_sense/phyphox_ble_sense.ino`.
- Import a core file from `experiments/*.phyphox` into the phyphox app.
- Confirm `phyphox-sense` connects and streams live values.
- Switch core experiments and confirm the selected sensor payload changes.
- For astronomy files, import the chosen `experiments/astronomy/*.phyphox` file
  and verify the required phone/SensorTag/Owon path and locale behavior.

Migrations/required services:

- No database migrations discovered.
- No required local service stack discovered.
- No Docker Compose, web server, or external runtime service is required for the
  automated checks.
- Arduino compile may update/download Arduino package indexes, cores, and
  libraries through `arduino-cli`.

Generated code/snapshots/fixtures:

- `experiments/*.phyphox` are committed generated artifacts from
  `src/phyphox/*.phyphox.xml`.
- `scripts/build-phyphox.sh` writes generated artifacts in place by default.
- `scripts/check-generated-clean.sh` rebuilds into a temp directory and compares
  against committed artifacts.
- `tests` create normal ignored Python caches (`.pytest_cache`, `__pycache__`);
  these already existed in this checkout and remained ignored.

## Commands Actually Run

### `ruff check .`

- Result: PASS.
- Output: `All checks passed!`

### `ruff format --check .`

- Result: PASS.
- Output: `14 files already formatted`

### `pytest`

- Result: PASS.
- Output summary:

```text
platform darwin -- Python 3.13.5, pytest-8.3.4
collected 131 items
131 passed in 6.16s
```

Coverage by test file:

- `tests/test_astronomy_audit.py`: 9 passed
- `tests/test_astronomy_consolidation.py`: 5 passed
- `tests/test_astronomy_semantics.py`: 5 passed
- `tests/test_phyphox_file_contracts.py`: 22 passed
- `tests/test_phyphox_generated_parity.py`: 1 passed
- `tests/test_phyphox_physics.py`: 7 passed
- `tests/test_phyphox_validate.py`: 51 passed
- `tests/test_postprocess_phyphox_xml.py`: 16 passed
- `tests/test_repo_guardrails.py`: 5 passed
- `tests/test_validate_xinclude_paths.py`: 10 passed

### `bash scripts/validate-xml.sh`

- Result: PASS.
- Output:

```text
== xmllint --noout ==
== XInclude path guard ==
== xmllint --xinclude ==
== phyphox plausibility checks (generated) ==
== phyphox plausibility checks (expanded sources) ==
OK
```

### `bash scripts/check-generated-clean.sh`

- Result: PASS.
- Output: `OK`

### `bash scripts/build-phyphox.sh "$tmpdir"` with a temporary output directory

- Result: PASS.
- Purpose: Verified the build command without rewriting committed
  `experiments/*.phyphox`.
- Output:

```text
Built 7 phyphox files.
Output: /var/folders/mx/1hh941bd0s965vyh_b16pb040000gp/T/tmp.1QFGi1I8uR
```

The temporary output directory was removed after the command.

### `bash scripts/secret-scan.sh`

- Result: PASS.
- Output: `OK`

### `bash scripts/deps-scan.sh`

- Result: PASS.
- Output: `OK`

### `bash scripts/sast-minimal.sh`

- Result: PASS.
- Output:

```text
== bash -n (shell syntax) ==
== shellcheck ==
== python3 -m py_compile ==
OK
```

### `bash scripts/compile-arduino.sh`

- First run result: FAIL in sandbox.
- First-run output:

```text
Downloading index: package_index.tar.bz2 downloaded
Some indexes could not be updated.
```

- Escalated rerun result: PASS.
- Escalated rerun output:

```text
Platform arduino:mbed_nano@4.5.0 already installed
Already installed ArduinoBLE@1.5.0
Already installed Arduino_LSM9DS1@1.1.1
Already installed Arduino_HTS221@1.0.0
Already installed Arduino_LPS22HB@1.0.2
Already installed Arduino_APDS9960@1.0.4
Sketch uses 339720 bytes (34%) of program storage space. Maximum is 983040 bytes.
Global variables use 71304 bytes (27%) of dynamic memory, leaving 190840 bytes for local variables. Maximum is 262144 bytes.
OK
```

Interpretation: Arduino compile is verified in the unrestricted local
environment, but the command cannot be trusted to run inside the default sandbox
when it needs to update Arduino indexes.

## Current Verification Status

Verified:

- Python lint passes.
- Python format check passes.
- Full discovered pytest suite passes: 131 tests.
- XML syntax and XInclude expansion checks pass for source/generated core files.
- Generated core experiment parity passes.
- Core phyphox plausibility checks pass for committed generated files and
  expanded source output.
- Out-of-tree phyphox build produces 7 core files.
- Security baseline scripts pass.
- Shell syntax and `shellcheck` pass for `scripts/*.sh`.
- Python tool bytecode compilation passes.
- Arduino firmware compiles for `arduino:mbed_nano:nano33ble` after allowing the
  compile script to update/use Arduino package indexes outside the sandbox.

Not verified:

- `make ci-local`, `make ci`, and bare `make build` were not run because they
  rebuild generated artifacts in place. Equivalent constituent checks were run
  individually, and the build command was run with a temporary output directory.
- `make bundle` was not run because it creates `phyphox-experiments.zip`, an
  output artifact not needed for this baseline.
- Hardware flashing was not run.
- Live BLE connection to `phyphox-sense` was not run.
- Live phyphox app import/streaming checks were not run.
- Astronomy files were not manually imported into the phyphox app.
- Phone/SensorTag/Owon hardware paths were not runtime-tested.
- GitHub Actions CI was not queried or rerun.

## Failures and Blockers

- Sandbox blocker: `bash scripts/compile-arduino.sh` failed in the default
  sandbox with `Some indexes could not be updated.` It passed after escalation.
- Runtime blocker: no Arduino Nano 33 BLE Sense and phone/app hardware probe was
  performed in this pass.
- Environment caveat: `python3` and `pytest` resolve to different Python
  installations; this did not block the current baseline but is suspicious for
  reproducibility.
- Worktree caveat: `.github/dependabot.yml` is deleted in the live worktree from
  pre-existing state. This baseline did not restore or inspect it.

## Flaky or Suspicious Tests

- No flaky tests were observed in this run.
- `tests/test_phyphox_validate.py` includes many direct tests of private helper
  functions in `tools/validate_phyphox.py`; useful for validator stability, but
  some are implementation-coupled.
- `tests/test_repo_guardrails.py` intentionally checks repository text/scripts
  and can be brittle if scripts are refactored without behavior changes.
- Astronomy tests include wording/string-presence assertions. They protect
  didactic claims, but some failures may reflect copy changes rather than broken
  runtime behavior.
- The suite has strong static and process-level coverage, but no live BLE or
  phyphox app execution coverage.

## Commands That Cannot Be Fully Trusted

- `bash scripts/compile-arduino.sh`: trustworthy for actual compile when
  `arduino-cli` can update indexes and access its package cache; not trustworthy
  inside the default sandbox.
- `make ci-local` / `make ci`: likely good full gates, but not run as a single
  command in this pass because they rebuild generated files in place.
- `bash scripts/secret-scan.sh`: useful minimal scanner, but it only checks a
  tight pattern list and comments that filenames containing colons may be
  misparsed.
- `bash scripts/deps-scan.sh`: useful pinning guard, but it parses shell text in
  `scripts/compile-arduino.sh`; it may need updates if the compile script is
  restructured.
- `bash scripts/validate-xml.sh`: validates generated core experiments and
  expanded core source output, not the hand-edited astronomy experiments through
  `tools/validate_phyphox.py`. Astronomy files are covered by pytest guardrails
  instead.

## Stronger Verification Needed

To move beyond this baseline:

1. Run `bash scripts/ci-local.sh` in a context where rewriting generated files is
   acceptable, then confirm `git diff -- experiments/*.phyphox` is empty.
2. Flash `arduino/phyphox_ble_sense/phyphox_ble_sense.ino` to a Nano 33 BLE
   Sense and run the core phyphox app import/streaming probe.
3. Import at least one generated core experiment per mode family and confirm the
   payload changes match the selected mode.
4. Import high-risk astronomy files, especially `transitmethode.phyphox` and
   `tidal-locking.phyphox`, and test the relevant phone/SensorTag/Owon paths.
5. Check current GitHub Actions status after committing/restoring the current
   worktree state.
