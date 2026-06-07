# Architecture Map

Architecture and flow map for the phyphox Arduino classroom kit as inspected on
2026-05-16.

This document is based on repository code, docs, tests, config, and file names.
Live hardware behavior that is not proven by code/tests is marked `UNCLEAR`.

## System Shape

The repository has four main surfaces:

1. Core Arduino BLE runtime:
   `arduino/phyphox_ble_sense/phyphox_ble_sense.ino`.
2. Core phyphox experiment generation:
   `src/phyphox/*.phyphox.xml` plus `src/phyphox/includes/*.xml` generate
   committed importable `experiments/*.phyphox`.
3. Hand-edited astronomy experiments:
   `experiments/astronomy/*.phyphox`, separate from the Arduino
   `phyphox-sense` runtime unless explicitly documented otherwise.
4. Verification/build scripts and Python validators:
   `scripts/*.sh`, `tools/*.py`, `tests/*.py`, `Makefile`, and CI config.

There is no database, server, long-running backend, or migration system in this
repo. Runtime state is either firmware memory on the Arduino, data containers in
the phyphox app, generated files on disk, or verification tool outputs.

## Main Runtime Entry Points

- `setup()` in `arduino/phyphox_ble_sense/phyphox_ble_sense.ino`: initializes
  sensors, starts BLE, registers service/characteristics, and advertises
  `phyphox-sense`.
- `loop()` in `arduino/phyphox_ble_sense/phyphox_ble_sense.ino`: polls BLE,
  accepts a connected central, reads config writes, and sends samples every
  `50 ms` while connected.
- `experiments/*.phyphox`: user-imported phyphox app entry points for core
  Arduino sensor modes.
- `experiments/astronomy/*.phyphox`: user-imported phyphox app entry points for
  phone/SensorTag/Owon classroom experiments.
- `scripts/build-phyphox.sh`: source XML to generated core experiment build
  entry point.
- `scripts/validate-xml.sh`: XML and core phyphox contract validation entry
  point.
- `scripts/compile-arduino.sh`: Arduino firmware compile entry point.
- `scripts/ci-local.sh`: aggregate local verification entry point.

## Important Domain Primitives

- BLE service UUID:
  `cddf0001-30f7-4671-8b43-5e40ba53514a`.
- BLE data characteristic UUID:
  `cddf1002-30f7-4671-8b43-5e40ba53514a`.
- BLE config characteristic UUID:
  `cddf1003-30f7-4671-8b43-5e40ba53514a`.
- Device name/local name: `phyphox-sense`.
- Data payload: five little-endian `float32` values, 20 bytes total.
- Phyphox app packet time: `CH0`, mapped through `extra="time"` and not read
  from the BLE payload.
- Arduino time: `CH1`, first float at offset `0`, seconds since boot.
- Data channels: `CH2..CH5`, mode-dependent floats at offsets `4`, `8`, `12`,
  and `16`.
- Active core modes: `1` acceleration, `2` gyroscope, `3` magnetometer, `4`
  pressure, `5` temperature/humidity, `6` light/RGB, `9` analog inputs.
- Reserved modes: `7`, `8`; firmware keeps the current mode when received.
- Generated core experiments: committed importable files in `experiments/*.phyphox`.
- Source core experiments: XInclude-based XML in `src/phyphox/*.phyphox.xml`.
- Astronomy experiments: hand-edited `.phyphox` files with English root locale
  plus `de` and `fr` translations.

## Dependency Boundaries

- Firmware depends on Arduino libraries:
  `ArduinoBLE`, `Arduino_APDS9960`, `Arduino_HTS221`, `Arduino_LPS22HB`,
  `Arduino_LSM9DS1`.
- Core phyphox source XML depends on shared XInclude fragments:
  `src/phyphox/includes/containers_ch0_ch5.xml` and
  `src/phyphox/includes/bluetooth_outputs_ch1_ch5.xml`.
- Generated core experiments depend on `xmllint --xinclude` and
  `tools/postprocess_phyphox_xml.py`.
- Validators depend on Python stdlib XML/JSON/path/regex modules only.
- Tests depend on `pytest` and direct imports from `tools/`.
- Shell checks depend on `bash`, `xmllint`, `python3`, `ruff`, `pytest`,
  `arduino-cli`, `rg`, and optionally `shellcheck`.
- Astronomy files depend on phyphox app support for phone sensors and Bluetooth
  sensor paths. Exact runtime behavior is `UNCLEAR` without live app/device
  probes.

## Configuration Sources

- `experiments/phyphox_constants.json`: shared BLE UUID and mode metadata.
- Firmware constants in `phyphox_ble_sense.ino`: UUIDs, payload size, send
  period, active modes, reserved-mode behavior.
- `src/phyphox/*.phyphox.xml`: app-side config writes and data mappings for core
  experiments.
- `src/phyphox/includes/*.xml`: shared core data container and BLE output
  mappings.
- `scripts/compile-arduino.sh`: pinned Arduino core and library versions.
- `pyproject.toml`: Ruff and pytest config.
- `requirements-test.txt`: pytest/Ruff dependency ranges.
- `.github/workflows/ci.yml`: CI jobs and installed tools.
- `.gitignore`: ignored local mirrors, caches, generated archives, and local
  audit artifacts.

## Public Contracts That Must Not Break

- The Arduino must advertise as `phyphox-sense` for documented core workflows.
- Core experiment files in `experiments/*.phyphox` must remain importable by
  phyphox app 1.x according to README compatibility wording.
- BLE UUIDs must remain aligned across firmware,
  `experiments/phyphox_constants.json`, source XML, and generated core XML.
- Payload offsets must remain `0`, `4`, `8`, `12`, `16` for `float32`
  little-endian values.
- `CH0` must remain app-managed packet time; `CH1` must remain firmware device
  time.
- Core mode IDs in source XML `<config>` values must match firmware enum values
  and `experiments/phyphox_constants.json`.
- `experiments/*.phyphox` are generated artifacts and must match
  `src/phyphox/*.phyphox.xml` after XInclude expansion and post-processing.
- Astronomy files must remain hand-edited, English-root, and include German and
  French translation blocks.
- Astronomy files must not be implied to use the Arduino `phyphox-sense` runtime
  unless their XML/runtime contract is deliberately changed.
- Pinned Arduino core/library versions in `scripts/compile-arduino.sh` are part
  of the reproducible compile contract.

## Hidden Coupling

- `tools/validate_phyphox.py` parses firmware constants and enum values with
  regex. Moving constants or changing enum syntax can break validation without
  changing runtime behavior.
- `src/phyphox/includes/bluetooth_outputs_ch1_ch5.xml` hard-codes the data UUID
  and offsets expected by firmware.
- `experiments/phyphox_constants.json`, firmware constants, source XML config
  values, and generated XML all duplicate parts of the same protocol.
- `tests/test_repo_guardrails.py` checks literal script/workflow text, including
  `bash scripts/check-generated-clean.sh`.
- Astronomy tests protect wording and labels in `.phyphox` XML and
  `docs/ASTRONOMY_EXPERIMENTS_COMPANION.md`; copy edits can break tests even
  when XML remains structurally valid.
- `scripts/deps-scan.sh` parses `scripts/compile-arduino.sh` text rather than a
  lockfile.
- `scripts/secret-scan.sh` scans tracked and untracked non-ignored files; local
  untracked docs can affect the result.

## Flow 1: Core BLE Measurement Runtime

What starts the flow?

- User flashes the Arduino sketch, imports a generated core `.phyphox` file, and
  starts the experiment in the phyphox app.
- Firmware starts in `setup()`, advertises BLE, and `loop()` waits for a central.

Trusted and untrusted inputs:

- Trusted by code: compile-time UUID constants, mode enum, payload size, sensor
  library APIs.
- Untrusted at runtime: BLE central connection, config characteristic bytes,
  sensor availability/freshness.
- App-side XML config value is trusted by project tests but still arrives as
  runtime bytes.

Validation:

- Firmware rejects non-finite and fractional config values.
- Firmware accepts only active raw values `1..6` and `9`.
- Active values update `mode`; reserved `7`/`8` and out-of-range values keep the
  current mode.
- `readFloat32LE` returns `0.0f` if passed a null/short buffer, but current code
  reads a 4-byte buffer from the BLE characteristic before using it.

State read:

- Sensor init flags: `imuOk`, `htsOk`, `baroOk`, `apdsOk`.
- Current `mode`.
- BLE central connection state.
- Sensor fresh-data predicates such as `IMU.accelerationAvailable()` and
  `APDS.colorAvailable()`.
- `millis()` timing state.

State written:

- Firmware globals: `startMs`, `lastSendMs`, `mode`, sensor init flags.
- BLE config characteristic initial zero value.
- BLE notification payload on the data characteristic.
- Phyphox app data containers after notification receipt.

State transitions:

1. Boot starts `setup()`.
2. Sensor begin calls set availability flags.
3. `BLE.begin()` succeeds or firmware blocks forever.
4. Firmware advertises `phyphox-sense`.
5. `loop()` polls BLE and waits for central.
6. Connected central writes config.
7. Config value changes mode or is ignored/keeps current mode.
8. Every `50 ms`, firmware reads the selected sensor path and sends one payload.
9. Disconnect exits the inner `while (central.connected())` loop and returns to
   advertising/polling behavior controlled by ArduinoBLE.

What can fail?

- Sensor initialization can fail.
- BLE initialization can fail.
- Central may not connect.
- Config bytes may be invalid or reserved.
- Sensor sample may be unavailable.
- Payload/channel meaning can drift from XML if UUIDs, offsets, or mode IDs are
  changed inconsistently.

How failure is surfaced:

- BLE init failure blocks forever in `setup()` with no LED or Serial diagnostic.
- Missing/unfresh sensor data sends `NaN` for active channels.
- Invalid config values are ignored silently.
- Reserved modes are ignored silently and keep previous mode.
- Connection/import failures surface only through phyphox app behavior;
  repository code does not log them.

Tests currently protecting it:

- `tests/test_repo_guardrails.py` checks constants/firmware UUID presence and
  reserved-mode metadata.
- `tests/test_phyphox_file_contracts.py` checks source/generated inventory,
  locales, includes, and generated validation.
- `tests/test_phyphox_physics.py` checks mode-specific generated experiment
  physics/display contracts.
- `tools/validate_phyphox.py` checks generated XML UUIDs, offsets, containers,
  one config block, and mode alignment.
- `scripts/compile-arduino.sh` compiles firmware but does not run it.

Where it can run without crashing but produce the wrong result:

- A wrong mode mapping can stream valid floats with the wrong sensor meaning.
- Offset or channel-order drift can produce plausible but mislabeled graphs.
- Pressure unit drift between firmware kPa and XML hPa conversion can produce
  wrong displayed values.
- Reserved mode writes silently keep old mode, which can look like a successful
  new selection.
- Sensor init failure yields `NaN`; if the app UI does not make that obvious,
  users may see no useful data without a firmware-side error.
- BLE config initial value is zero while default firmware mode is acceleration;
  until the app writes a config, default behavior depends on firmware mode.

## Flow 2: Core Experiment Generation

What starts the flow?

- Developer runs `bash scripts/build-phyphox.sh`, `make build`, or CI/local CI.

Trusted and untrusted inputs:

- Trusted: repository source XML and include fragments.
- Untrusted: XInclude `href` values in source XML, output directory argument,
  environment variable `PHYPHOX_OUTDIR`, installed `xmllint` behavior.

Validation:

- Script checks `xmllint` and `python3` availability.
- `tools/validate_xinclude_paths.py` rejects URL, absolute, query/fragment,
  parent-directory, missing, non-file, and symlink-escaping include paths.
- `xmllint --xinclude` must parse and expand source XML.
- `tools/postprocess_phyphox_xml.py` strips `xml:base` and leftover XInclude
  namespace text.

State read:

- `src/phyphox/*.phyphox.xml`.
- `src/phyphox/includes/*.xml`.
- Optional output directory argument or `PHYPHOX_OUTDIR`.

State written:

- Default: `experiments/*.phyphox`.
- If an output directory is supplied: generated `.phyphox` files in that
  directory.
- Temporary file from `mktemp`, removed by trap.

What can fail?

- Missing `xmllint` or `python3`.
- Unsafe or broken XInclude path.
- XML parse/XInclude expansion failure.
- Output directory creation or file copy failure.

How failure is surfaced:

- Shell exits non-zero because of `set -euo pipefail`.
- Missing tools and unsafe include errors print to stderr.
- `xmllint`/Python errors print tool messages.

Tests currently protecting it:

- `tests/test_phyphox_generated_parity.py` rebuilds to a temp directory and
  diffs generated artifacts.
- `tests/test_validate_xinclude_paths.py` covers include path rejection cases.
- `tests/test_postprocess_phyphox_xml.py` covers post-processing.
- `scripts/check-generated-clean.sh` compares generated output to committed
  artifacts.

Where it can run without crashing but produce the wrong result:

- Post-processing is text-based; a future XML pattern could be stripped
  incorrectly if it matches the narrow regex/string assumptions.
- `make build` rewrites generated artifacts in place; a developer can forget to
  review generated diffs.
- Generated output may be XML-valid but semantically wrong if source formulas,
  labels, or channel names drift without a dedicated test.

## Flow 3: XML and Protocol Validation

What starts the flow?

- Developer runs `bash scripts/validate-xml.sh`, `make validate`, CI, or
  `scripts/ci-local.sh`.

Trusted and untrusted inputs:

- Untrusted: source XML, include XML, generated core `.phyphox` files,
  constants JSON, firmware text.
- Trusted by scripts: tool behavior from `xmllint` and Python stdlib XML/JSON.

Validation:

- `xmllint --noout` checks include/source/generated core XML syntax.
- `validate_xinclude_paths.py` checks include boundaries.
- `xmllint --xinclude --noout` checks source expansion.
- `validate_phyphox.py` loads expected UUIDs from constants JSON and firmware.
- `validate_phyphox.py` loads expected modes from constants JSON, firmware enum,
  and source XML config values.
- `validate_phyphox.py` checks generated/expanded XML top-level structure,
  container uniqueness, references, one Bluetooth input, one config output,
  conversion type, UUIDs, offsets, and numeric config values.

State read:

- `src/phyphox/*.phyphox.xml`.
- `src/phyphox/includes/*.xml`.
- `experiments/*.phyphox`.
- `experiments/phyphox_constants.json`.
- `arduino/phyphox_ble_sense/phyphox_ble_sense.ino`.

State written:

- Temporary expanded files in a temp directory, removed by trap.

What can fail?

- Missing tools.
- Broken XML or XInclude.
- Missing generated files.
- UUID/mode drift.
- Container reference errors.
- Wrong data offsets or config conversion.

How failure is surfaced:

- Script exits non-zero.
- Validator prints specific error messages to stderr.
- `xmllint` prints parse/validation errors.

Tests currently protecting it:

- `tests/test_phyphox_validate.py`.
- `tests/test_phyphox_file_contracts.py`.
- `tests/test_repo_guardrails.py`.
- `tests/test_validate_xinclude_paths.py`.

Where it can run without crashing but produce the wrong result:

- Validator is tuned to generated core Arduino experiments and does not validate
  hand-edited astronomy files through the same Bluetooth contract.
- Firmware regex parsing can miss contracts if the firmware is reorganized.
- XML can satisfy structural checks while carrying wrong physics, translations,
  or classroom wording unless separate tests catch it.

## Flow 4: Arduino Compile

What starts the flow?

- Developer runs `bash scripts/compile-arduino.sh`, `make compile`, CI Arduino
  job, or local CI.

Trusted and untrusted inputs:

- Trusted by repo: pinned core and library versions in the script.
- Untrusted/environmental: network/package indexes, Arduino CLI cache,
  installed `arduino-cli`, external package registry availability.

Validation:

- Script checks `arduino-cli` availability.
- `arduino-cli core update-index` updates package indexes.
- `arduino-cli core install arduino:mbed_nano@4.5.0` installs pinned core.
- `arduino-cli lib install` installs pinned libraries.
- `arduino-cli compile --fqbn arduino:mbed_nano:nano33ble` compiles the sketch.

State read:

- `arduino/phyphox_ble_sense/phyphox_ble_sense.ino`.
- Arduino package indexes and local Arduino cache.

State written:

- Arduino CLI package index/cache outside the repository.
- Build output in Arduino CLI-managed locations.

What can fail?

- Missing `arduino-cli`.
- Network/index update failure.
- Package install failure.
- Compile errors.
- Sandbox restrictions on package index/cache access.

How failure is surfaced:

- Script exits non-zero with `arduino-cli` output.
- In the current baseline, sandboxed run failed with `Some indexes could not be
  updated`; escalated run passed.

Tests currently protecting it:

- No unit test executes firmware.
- `scripts/compile-arduino.sh` itself is the compile gate.
- CI has an Arduino compile job.
- `scripts/deps-scan.sh` checks pinned core/library command text.

Where it can run without crashing but produce the wrong result:

- Successful compile does not prove BLE runtime behavior, sensor readings, or
  app compatibility.
- Pinned libraries can compile while changing runtime behavior only when
  upgraded deliberately.
- Firmware can compile with wrong UUIDs/modes if validators are not run.

## Flow 5: Core User Import and Measurement

What starts the flow?

- User imports one generated file from `experiments/*.phyphox` into the phyphox
  app and starts it.

Trusted and untrusted inputs:

- Trusted by repo tests: generated experiment files and shared BLE mapping.
- Untrusted at runtime: phone/app version, Bluetooth environment, selected
  Arduino device, runtime sensor values.

Validation:

- Static validation occurs before runtime via XML tests/scripts.
- Runtime validation inside the phyphox app is `UNCLEAR` from this repository.

State read:

- Imported `.phyphox` file.
- Bluetooth advertisements and characteristic values.
- Arduino notification payloads.

State written:

- Phyphox app data containers and UI graphs/values.
- Config characteristic write to select firmware mode.

What can fail?

- Import failure.
- Device not found or already connected elsewhere.
- Wrong experiment file selected for desired mode.
- Config write failure.
- Sensor unavailable or stale.

How failure is surfaced:

- README documents user-visible issues such as Arduino not found, no data/flat
  plot, or board not advertising.
- Repository code does not capture app logs or runtime errors.

Tests currently protecting it:

- Generated file validation, physics tests, generated parity tests, and firmware
  compile.
- No live app/hardware test in the repo.

Where it can run without crashing but produce the wrong result:

- App can connect to a compatible-looking device with wrong firmware.
- Graphs can display plausible values with wrong units/channel mapping.
- `NaN` samples from unavailable sensors may produce confusing empty/flat views.
- If config write fails, firmware default/previous mode may continue.

## Flow 6: Astronomy Experiment Runtime

What starts the flow?

- User imports a file from `experiments/astronomy/*.phyphox` into the phyphox app
  and runs it with the required phone, SensorTag, or Owon path.

Trusted and untrusted inputs:

- Trusted by repo tests: file inventory, English root locale, `de`/`fr`
  translation presence, selected wording/labels, and some XML graph/input
  semantics.
- Untrusted at runtime: phone sensor values, SensorTag/Owon Bluetooth devices,
  hardware availability, app locale handling, user inputs such as trigger/star
  radius values.

Validation:

- Static pytest checks cover inventory, locales, didactic wording, selected view
  labels, graph inputs, time units, and some positive input constraints.
- Full phyphox runtime validation for these files is `UNCLEAR`; the core
  `tools/validate_phyphox.py` validator expects exactly one Arduino Bluetooth
  input and is not the contract for astronomy files.

State read:

- Imported astronomy `.phyphox` file.
- Phone sensors such as light or pressure where declared.
- SensorTag/Owon BLE characteristics where declared.
- User-editable values in the phyphox UI where present.

State written:

- Phyphox app data containers, views, graphs, values, and exports.
- Bluetooth config writes for SensorTag-style devices where declared.

What can fail?

- Missing required sensor hardware.
- Bluetooth config/read failure for SensorTag/Owon paths.
- Locale translation drift.
- Formula/container graph mistakes in large hand-edited XML.
- User input outside intended range if XML constraints are missing.

How failure is surfaced:

- Mostly through phyphox app behavior; repository code has no runtime logging for
  these experiments.
- Static tests surface known wording/semantic regressions.

Tests currently protecting it:

- `tests/test_astronomy_audit.py`.
- `tests/test_astronomy_consolidation.py`.
- `tests/test_astronomy_semantics.py`.
- `docs/ASTRONOMY_EXPERIMENTS_COMPANION.md` is used as a semantic companion and
  partially tested.

Where it can run without crashing but produce the wrong result:

- Large files like `transitmethode.phyphox` and `tidal-locking.phyphox` can have
  valid XML with wrong container wiring.
- Phone/SensorTag/Owon branches can silently diverge in meaning.
- Translation text can lag behind English semantics.
- A classroom analogy can overstate scientific meaning even if calculations run.

## Flow 7: Security and Static Baseline

What starts the flow?

- Developer runs `make security`, `scripts/ci-local.sh`, or CI security job.

Trusted and untrusted inputs:

- Untrusted: tracked and untracked non-ignored files scanned by secret scanner,
  shell scripts, Python tools, dependency declarations.
- Trusted: pattern list and pinning rules in scripts.

Validation:

- `scripts/secret-scan.sh` scans tight private-key/token patterns with `rg`.
- `scripts/deps-scan.sh` checks Arduino and Python dependency pinning.
- `scripts/sast-minimal.sh` runs `bash -n`, `shellcheck` if installed, and
  Python bytecode compilation.

State read:

- Git file list including untracked non-ignored files.
- `scripts/*.sh`.
- `tools/*.py`.
- `requirements-test.txt`.
- `scripts/compile-arduino.sh`.

State written:

- Temporary files from shell scripts; removed by traps.
- Python bytecode caches may be written by `py_compile` in normal ignored cache
  locations.

What can fail?

- Missing `git`, `rg`, `python3`, or optional `shellcheck`.
- Secret pattern match.
- Unpinned dependency text.
- Shell syntax or shellcheck violation.
- Python compile error.

How failure is surfaced:

- Scripts exit non-zero and print a short diagnostic.
- Secret scan prints file/line for potential matches.

Tests currently protecting it:

- `tests/test_repo_guardrails.py` checks secret scan catches an untracked test
  token and that generated-clean guardrails are wired.
- Baseline run also executed the scripts directly.

Where it can run without crashing but produce the wrong result:

- Secret scanner has a deliberately tight pattern list and is not comprehensive.
- Filenames containing colons may be misparsed according to script comments.
- Dependency scanner parses shell text and can miss semantically equivalent
  unpinned installs if the compile script is rewritten.
- If `shellcheck` is absent, `sast-minimal.sh` skips shellcheck locally.

## Flow 8: CI and Local Aggregate Verification

What starts the flow?

- GitHub `push`, `pull_request`, or `workflow_dispatch` starts
  `.github/workflows/ci.yml`.
- Developer runs `bash scripts/ci-local.sh`, `make ci-local`, or `make ci`.

Trusted and untrusted inputs:

- Untrusted: all source, generated artifacts, scripts, tests, external package
  installs, CI runner environment.
- Trusted: workflow/tool commands after inspection.

Validation:

- CI XML job installs XML/Python tooling, runs Ruff, pytest, XML validation,
  build, and generated-clean.
- CI Arduino job installs Arduino CLI and compiles the sketch.
- CI security job installs security tools and runs secret/dependency/static
  scripts.
- `scripts/ci-local.sh` runs the same broad categories serially.

State read:

- Entire repo verification surface.
- External package indexes for Arduino compile.

State written:

- Generated experiments if `scripts/build-phyphox.sh` is run with default output.
- Tool caches outside or inside ignored cache directories.

What can fail?

- Any underlying lint/test/build/compile/security failure.
- Missing local tools.
- Network or package index failure.
- Generated files becoming out of date after build.

How failure is surfaced:

- Shell/CI exits non-zero at first failing command.
- CI presents job logs.

Tests currently protecting it:

- `tests/test_repo_guardrails.py` checks that generated-clean is wired into
  `scripts/ci-local.sh` and workflow text.

Where it can run without crashing but produce the wrong result:

- `make ci-local` can rewrite generated files before checking cleanliness; a
  caller must inspect git diff afterward.
- CI may pass without live hardware/runtime evidence.
- Local aggregate success can differ from CI if Python/tool versions differ.

## Storage and File-System Interactions

- Source XML read from `src/phyphox/`.
- Generated core experiments written to `experiments/` by default.
- Generated parity uses temp directories via `mktemp -d`.
- Arduino CLI writes package indexes, cores, libraries, and build artifacts
  outside the repo-managed source tree.
- Secret scan reads tracked plus untracked non-ignored files from `git ls-files`.
- Test and static tooling may write ignored caches such as `.pytest_cache`,
  `.ruff_cache`, and `__pycache__`.
- `reference/` is ignored local mirror material. Active use is `UNCLEAR`.

## Error-Handling Strategy

- Shell scripts use `set -euo pipefail` and mostly fail fast.
- Python validators collect multiple validation errors where useful and return
  non-zero from CLI entry points.
- Firmware handles invalid config by ignoring it, handles missing sensor samples
  by emitting `NaN`, and handles BLE initialization failure by blocking forever.
- Firmware does not expose Serial logs or LED diagnostics in current code.
- phyphox app runtime error handling is outside this repo and therefore
  `UNCLEAR`.

## Compatibility and Deprecation Layers

- Core files target phyphox app 1.x and experiment version v1.2 per README.
- Firmware reserves modes `7` and `8` and silently keeps the current mode if they
  are received.
- `docs/deprecated/audit/*` is archived audit/remediation material, not active
  runtime architecture.
- `reference/` is ignored local reference material and may be stale.
- Astronomy files are explicitly separate from the Arduino `phyphox-sense`
  runtime unless a future contract says otherwise.

## Not Fully Understood

- Live BLE connection behavior across phones and phyphox app versions is not
  proven by repository tests.
- Whether ArduinoBLE continues advertising exactly as expected after disconnect
  is not proven here beyond the code path and library behavior.
- SensorTag and Owon runtime compatibility for astronomy files is not proven by
  local tests.
- Full phyphox app validation/import behavior for each astronomy file is not
  modeled by `tools/validate_phyphox.py`.
- Current use of the ignored `reference/` mirrors is `UNCLEAR`.
- `.github/dependabot.yml` is tracked but deleted in this worktree, so its
  architecture role was not mapped from a live file.
