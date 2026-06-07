# Logic and Correctness Audit

Audit date: 2026-05-16.

Scope: live repository source, scripts, generated/source phyphox XML, Arduino
sketch, and tests. This is an audit-only document. No production code was
changed.

Pre-existing worktree state before this document: `.github/dependabot.yml` is
tracked but deleted; `AGENTS.md`, `docs/code-index.md`,
`docs/verification-baseline.md`, `docs/architecture-map.md`, and
`docs/deprecation-and-simplification-audit.md` are untracked.

## Checks Run

- `ruff check .`: passed.
- `ruff format --check .`: passed, `14 files already formatted`.
- `pytest`: passed, `131 passed in 2.66s`.
- `bash scripts/validate-xml.sh`: passed.
- Static duplicate-container probe over `experiments/**/*.phyphox` and
  `src/phyphox/**/*.xml`: found one duplicate container name,
  `experiments/astronomy/tidal-locking.phyphox: factor2`.

Passing checks do not prove runtime correctness. This repo includes hardware,
BLE, mobile-app, and phyphox runtime behavior that was not exercised here.

## Confirmed Issues

### LC-001

- Location: `experiments/astronomy/tidal-locking.phyphox:122`,
  `experiments/astronomy/tidal-locking.phyphox:145`.
- Evidence: `factor2` appears twice as a `<container>` name in the same
  experiment. A static duplicate-container probe reported only this duplicate.
  The full `pytest` suite and `bash scripts/validate-xml.sh` still passed.
- Why it matters: duplicate data containers can alias, overwrite, or make
  phyphox runtime state ambiguous while XML syntax and current tests stay green.
- Minimal reproduction or reasoning: parse `tidal-locking.phyphox`, collect
  `./data-containers/container` text values, and count duplicates; `factor2`
  has count `2`.
- Existing test coverage, if any: `tests/test_astronomy_semantics.py` checks a
  few tidal-locking graph inputs, but no astronomy test rejects duplicate
  container names.
- Missing test that should exist: an astronomy-wide XML semantic test that
  rejects duplicate container names and unknown references.
- Suggested minimal fix: rename or remove the unintended duplicate after
  checking which `factor2` path the runtime expects.
- Risk level: medium.
- Verification command or strategy: add the semantic test, run `pytest
  tests/test_astronomy_semantics.py`, full `pytest`, and import the experiment
  in phyphox.
- Confidence: high.

### LC-002

- Location: `scripts/validate-xml.sh:48-60`,
  `tools/validate_phyphox.py:220-468`,
  `experiments/astronomy/tidal-locking.phyphox:122-145`.
- Evidence: `validate-xml.sh` runs `tools/validate_phyphox.py` only on
  `experiments/*.phyphox` and expanded `src/phyphox/*.phyphox.xml`. Astronomy
  files are covered by `xmllint --noout`, but not by the semantic validator; the
  duplicate `factor2` astronomy container passes the current command.
- Why it matters: syntax-valid astronomy files can contain semantic runtime
  errors and still pass the canonical validation command.
- Minimal reproduction or reasoning: `bash scripts/validate-xml.sh` passed while
  the duplicate-container probe found `factor2`.
- Existing test coverage, if any: astronomy tests inspect selected labels,
  wording, and a few graph connections, but they do not apply the common
  `validate_phyphox` semantic checks to astronomy files.
- Missing test that should exist: either extend the validator for astronomy
  files or add a separate astronomy semantic validator that checks duplicate
  containers, unknown references, and known safe multi-input patterns.
- Suggested minimal fix: add astronomy semantic checks without changing runtime
  XML first; then fix only failures that are confirmed.
- Risk level: medium.
- Verification command or strategy: `pytest`, `bash scripts/validate-xml.sh`,
  and manual phyphox import for every changed astronomy experiment.
- Confidence: high.

### LC-003

- Location: `scripts/ci-local.sh:30-32`,
  `scripts/build-phyphox.sh:17-45`,
  `scripts/check-generated-clean.sh:10-35`.
- Evidence: `ci-local.sh` rebuilds `experiments/*.phyphox` in place before
  calling `check-generated-clean.sh`. The clean check then compares the rebuilt
  files against a temp rebuild.
- Why it matters: stale generated artifacts can be silently repaired by CI/local
  verification before the check runs, producing a false-green result while the
  working tree has changed.
- Minimal reproduction or reasoning: if a generated experiment is stale,
  `bash scripts/build-phyphox.sh` overwrites it; the following
  `bash scripts/check-generated-clean.sh` compares two freshly generated copies.
- Existing test coverage, if any: `tests/test_repo_guardrails.py:27-33` asserts
  that the scripts call each other, but not that CI fails before mutating stale
  generated artifacts.
- Missing test that should exist: a subprocess test using a temp copy with a
  deliberately stale generated file proving that the canonical CI path exits
  non-zero or reports a dirty tree.
- Suggested minimal fix: run `check-generated-clean.sh` before any in-place
  build in CI, or add a post-build `git diff --exit-code -- experiments`.
- Risk level: medium.
- Verification command or strategy: targeted guardrail test plus full `pytest`
  and `bash scripts/check-generated-clean.sh`.
- Confidence: high.

### LC-004

- Location: `scripts/build-phyphox.sh:28-31`.
- Evidence: when no `src/phyphox/*.phyphox.xml` files are found, the script
  prints "No source files found" and exits `0`.
- Why it matters: a missing or wrongly checked-out source directory can look like
  a successful build. Downstream automation may treat "built zero files" as
  success.
- Minimal reproduction or reasoning: run the script from a temp copy where
  `src/phyphox/*.phyphox.xml` is absent; the code path exits `0`.
- Existing test coverage, if any: generated parity tests cover the current
  source directory but not missing-source failure behavior.
- Missing test that should exist: subprocess test in a temp repo with no source
  files asserting non-zero exit.
- Suggested minimal fix: change the no-source branch to exit non-zero.
- Risk level: low.
- Verification command or strategy: targeted script test, then `pytest` and
  `bash scripts/build-phyphox.sh "$tmpdir"`.
- Confidence: high.

### LC-005

- Location: `tools/validate_phyphox.py:205-214`,
  `tools/validate_phyphox.py:455-466`,
  `arduino/phyphox_ble_sense/phyphox_ble_sense.ino:70-96`.
- Evidence: XML config validation only checks that `<config>` text is numeric.
  `_load_expected_modes()` uses `int(float(config.text.strip()))`, while the
  firmware uses `roundf(configValue)` before selecting a mode.
- Why it matters: non-integer mode values can be accepted by validation and
  interpreted differently by firmware. For example, `1.9` truncates to `1` in
  validation but rounds to `2` in firmware.
- Minimal reproduction or reasoning: compare Python `int(float("1.9")) == 1`
  with firmware `roundf(1.9f) == 2`.
- Existing test coverage, if any: tests reject non-numeric config text but do
  not reject fractional or out-of-range numeric mode values.
- Missing test that should exist: config values must be exact active mode IDs,
  not arbitrary floats.
- Suggested minimal fix: parse config as a finite integer-valued number and
  compare exact values against `phyphox_constants.json`.
- Risk level: high.
- Verification command or strategy: add validator tests for `1.1`, `1.9`, `7`,
  `8`, `0`, and `10`; run `pytest tests/test_phyphox_validate.py` and full
  `pytest`.
- Confidence: high.

### LC-006

- Location: `tools/validate_phyphox.py:343-386`,
  `tests/test_phyphox_validate.py:468-484`.
- Evidence: Bluetooth data offsets are collected in a `set[int]`. The validator
  checks that the set equals `{0, 4, 8, 12, 16}`, but it does not reject duplicate
  offsets or enforce exactly one mapping per payload field.
- Why it matters: a file with two outputs reading offset `0` and all expected
  offsets present can pass while duplicating one channel and leaving another
  semantic mapping wrong.
- Minimal reproduction or reasoning: sets discard duplicate values; the check
  cannot distinguish `[0, 0, 4, 8, 12, 16]` from `[0, 4, 8, 12, 16]`.
- Existing test coverage, if any: there are tests for invalid and missing
  offsets, but not duplicate offsets.
- Missing test that should exist: duplicate offset values should fail with a
  clear message.
- Suggested minimal fix: track offsets as a list and reject duplicates before
  comparing the expected set.
- Risk level: medium.
- Verification command or strategy: targeted validator test plus full `pytest`.
- Confidence: high.

### LC-007

- Location: `experiments/astronomy/albedo.phyphox:77-89`,
  `experiments/astronomy/albedo.phyphox:123-135`,
  `experiments/astronomy/transitmethode.phyphox:350-368`.
- Evidence: reflectance/transit-depth formulas divide by the maximum signal:
  `([1]-[2])/[1]*100`. The same depth is then used in `sqrt([2]/100)` for
  planet radius.
- Why it matters: zero, empty, or all-dark input can produce divide-by-zero,
  infinite, NaN, or negative-square-root outputs while the experiment keeps
  running.
- Minimal reproduction or reasoning: if `max_amplitude == 0`, the formula
  divides by zero; if `min_amplitude > max_amplitude` because of stale or mixed
  data, transit depth can be negative and `sqrt(depth/100)` is invalid.
- Existing test coverage, if any: tests assert wording and formula presence, but
  they do not simulate zero-signal or invalid-depth cases.
- Missing test that should exist: semantic or runtime test documenting the
  expected display behavior for zero maximum signal and incomplete samples.
- Suggested minimal fix: add explicit guard behavior in the phyphox analysis, or
  document that the result remains empty until a positive maximum exists.
- Risk level: medium.
- Verification command or strategy: phyphox import plus manual/simulated runs
  with all-zero, constant, and normal transit signals.
- Confidence: high for the zero-division risk, medium for exact phyphox runtime
  display behavior.

### LC-008

- Location: `tests/test_phyphox_physics.py:149-165`,
  `tests/test_astronomy_audit.py:46-135`,
  `tests/test_astronomy_consolidation.py:14-52`,
  `tests/test_repo_guardrails.py:27-33`.
- Evidence: several tests assert literal strings, string absence, or raw XML
  counts. Examples include checking that `"ch2 > 4.0f"` is not present, counting
  `<bluetooth` strings, and checking that helper script text appears in CI.
- Why it matters: these tests can pass while runtime behavior is wrong. They
  protect prior cleanup text more than user-visible or data-path correctness.
- Minimal reproduction or reasoning: renaming a string can fail tests without
  breaking behavior, while a duplicate astronomy container or generated-clean
  false-green path currently passes.
- Existing test coverage, if any: full `pytest` passes.
- Missing test that should exist: behavior-oriented tests for XML semantic
  contracts, generated-clean failure behavior, and runtime edge cases.
- Suggested minimal fix: replace brittle string tests one at a time with tests
  that fail when a meaningful contract breaks.
- Risk level: medium.
- Verification command or strategy: run changed test files and full `pytest`.
- Confidence: high.

## Suspected Issues / Needs Runtime Verification

### LC-009

- Location: `arduino/phyphox_ble_sense/phyphox_ble_sense.ino:197-218`,
  `arduino/phyphox_ble_sense/phyphox_ble_sense.ino:107-189`.
- Evidence: sensor initialization failures are stored in `imuOk`, `htsOk`,
  `baroOk`, and `apdsOk`; the sketch still advertises BLE. `readChannels()`
  initializes channels to `NAN`, and `sendSample()` writes and notifies the
  payload regardless of whether the active sensor produced a reading.
- Why it matters: the device can appear connected and streaming while sending
  NaNs for the selected mode. That is silent partial failure, not a crash.
- Minimal reproduction or reasoning: force a sensor `begin()` failure or select
  a mode whose `*_Ok` flag is false; BLE still advertises and notifications are
  sent.
- Existing test coverage, if any: no firmware unit test or hardware runtime test
  covers failed sensor initialization.
- Missing test that should exist: hardware/simulator check that failed sensors
  surface an explicit state or do not present the mode as valid.
- Suggested minimal fix: expose sensor availability explicitly or block/mark
  unavailable modes instead of sending indistinguishable samples.
- Risk level: high.
- Verification command or strategy: Arduino compile plus live BLE probes with
  each sensor mode and induced/mocked sensor failures.
- Confidence: medium.

### LC-010

- Location: `arduino/phyphox_ble_sense/phyphox_ble_sense.ino:43`,
  `arduino/phyphox_ble_sense/phyphox_ble_sense.ino:215-216`,
  `experiments/phyphox_constants.json:7-16`.
- Evidence: firmware runtime mode defaults to acceleration, but setup writes a
  zeroed config characteristic. Active mode IDs are `1..6` and `9`; `0` is not a
  valid mode.
- Why it matters: any client reading the config characteristic before the app
  writes experiment config can see mode `0` while the device is actually sending
  acceleration payloads.
- Minimal reproduction or reasoning: after setup, `mode == kAcceleration` and
  the characteristic contains four zero bytes.
- Existing test coverage, if any: tests check constants and generated config
  values, but not firmware initial config state.
- Missing test that should exist: firmware-level or static contract test that
  the advertised/readable config matches the actual default mode.
- Suggested minimal fix: initialize the config characteristic to float32 little
  endian `1.0`, or make the characteristic write-only if reads are not a public
  state contract.
- Risk level: medium.
- Verification command or strategy: Arduino compile and BLE readback before
  selecting an experiment.
- Confidence: medium.

### LC-011

- Location: `arduino/phyphox_ble_sense/phyphox_ble_sense.ino:70-96`,
  `experiments/phyphox_constants.json:16`,
  `tests/test_repo_guardrails.py:97-112`.
- Evidence: config values `7` and `8` are documented as reserved. Firmware
  accepts the full range `1..9`, but reserved values fall through silently and
  leave the previous mode active.
- Why it matters: a future or malformed app-side experiment can believe it
  selected mode `7` or `8` while the device continues streaming the previous
  mode.
- Minimal reproduction or reasoning: write config float `7.0` after using
  pressure mode; `setModeFromConfig()` returns without changing `mode`.
- Existing test coverage, if any: tests only verify `reserved_modes` is present
  and not active; they do not verify runtime behavior for reserved writes.
- Missing test that should exist: explicit reserved-mode behavior test or
  documentation contract test deciding whether reserved writes should reject,
  reset, or surface an error.
- Suggested minimal fix: reject reserved values explicitly and expose failure, or
  remove the accepted reserved range until real modes exist.
- Risk level: high.
- Verification command or strategy: BLE config-write probe for modes `7` and
  `8`, then inspect emitted payload mode semantics.
- Confidence: medium.

### LC-012

- Location: `experiments/astronomy/transitmethode.phyphox:373-390`,
  `experiments/astronomy/transitmethode.phyphox:1037-1092`.
- Evidence: average transit duration and average year duration always divide by
  five inputs. The UI note says averages display only after enough transits, but
  the `<value>` elements are always present and the timing containers are
  initialized or reset through zero-heavy paths.
- Why it matters: before enough events have occurred, users may see `0` or an
  average polluted by missing events rather than an empty/not-ready result.
- Minimal reproduction or reasoning: on a fresh/reset run, `on*`, `off*`, `dt*`,
  and `don*` paths are initialized or reset to zero; the average formulas still
  consume five values.
- Existing test coverage, if any: tests assert the text warning and some labels,
  not the timing state transition.
- Missing test that should exist: runtime or semantic test for 0, 1, 4, 5, and
  6 transit events.
- Suggested minimal fix: gate average outputs until the required event count is
  available.
- Risk level: medium.
- Verification command or strategy: manual/simulated phyphox runs with
  controlled light curves and exported timing data.
- Confidence: medium.

### LC-013

- Location: `tools/postprocess_phyphox_xml.py:9-17`,
  `tests/test_postprocess_phyphox_xml.py:18-117`.
- Evidence: post-processing strips `xml:base` and `xmlns:xi` with text regex and
  replacement rather than parsing XML. Tests cover intended strings but not
  comments, CDATA-like content, alternate namespace formatting, or legitimate
  `xml:base` use outside XInclude expansion.
- Why it matters: text-level XML rewriting can silently remove content that
  happens to match the pattern, or fail to remove equivalent namespace forms.
- Minimal reproduction or reasoning: the function applies `re.sub` to the full
  XML text without knowing whether a match is an attribute on an element that
  came from `xmllint --xinclude`.
- Existing test coverage, if any: unit tests cover simple intended cases.
- Missing test that should exist: generated XML fixture with comments/text and a
  documented decision on whether any legitimate `xml:base` should be preserved.
- Suggested minimal fix: keep as-is if generated outputs are the only supported
  input, but document that contract; otherwise replace with XML-aware handling.
- Risk level: low.
- Verification command or strategy: `pytest tests/test_postprocess_phyphox_xml.py`
  and `bash scripts/check-generated-clean.sh`.
- Confidence: medium.

## No Finding / Lower-Risk Notes

- `ruff`, `pytest`, and XML validation are green on the current tree.
- Core generated phyphox files have behavior-oriented coverage for several
  physics/unit contracts, but no hardware runtime tests.
- `tools/validate_xinclude_paths.py` has explicit tests for URL, absolute path,
  parent traversal, missing target, directory target, and symlink escape.
- No date/time/timezone logic was found in production paths.
- No deprecated or hallucinated third-party Python APIs were found by static
  inspection.

## Recommended Next Verification

1. Add duplicate-container and unknown-reference checks for astronomy XML.
2. Add targeted validator tests for fractional mode IDs and duplicate payload
   offsets.
3. Fix or explicitly document the generated-clean false-green behavior before
   relying on `ci-local` as proof that generated artifacts are current.
4. Run live BLE mode probes for startup config, failed sensors, reserved modes,
   and every active mode.
5. Import and exercise astronomy experiments in phyphox with zero/empty and
   normal sample data before changing formulas.

## Coverage Gaps and Uncertainty

- No Arduino compile was run in this pass.
- No live Arduino Nano 33 BLE Sense, phone, SensorTag, Owon, or phyphox-app
  runtime checks were run.
- Exact phyphox behavior for NaN, infinity, duplicate containers, empty
  containers, and not-yet-ready analysis values needs runtime confirmation.
- Git history was not used to decide intended behavior; history may clarify
  reserved modes, astronomy compatibility, and debug hardware paths.
