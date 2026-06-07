# Code Index

Source-file inventory before cleanup or refactor work.

Generated from live inspection of the repository on 2026-05-16. This index covers
tracked source, experiment, script, test, and config surfaces file by file. The
ignored local `reference/` mirror is summarized as a directory because it contains
1,758 mirrored reference files and is excluded by `.gitignore`.

Current worktree note: `.github/dependabot.yml` is tracked but currently deleted
before this index pass; it was not inspected as a live file.

## Top-Level Config and Command Surface

### `Makefile`

- Language/type: Make.
- Primary responsibility: Defines the repository command facade for linting,
  tests, XML validation, generated experiment builds, Arduino compile, security
  checks, local CI, and experiment bundling.
- Main exports/classes/functions: targets `lint`, `test`, `validate`, `build`,
  `compile`, `security`, `ci`, `ci-local`, `bundle`.
- Runtime role: config.
- Direct dependencies worth knowing: `ruff`, `pytest`, `scripts/validate-xml.sh`,
  `scripts/build-phyphox.sh`, `scripts/compile-arduino.sh`,
  `scripts/secret-scan.sh`, `scripts/deps-scan.sh`, `scripts/sast-minimal.sh`,
  `scripts/ci-local.sh`, `zip`.
- Status: active; referenced by README and normal contributor workflow.
- Obvious smells: none obvious.

### `pyproject.toml`

- Language/type: TOML.
- Primary responsibility: Configures Ruff and pytest defaults.
- Main exports/classes/functions: `[tool.ruff]`, `[tool.ruff.lint]`,
  `[tool.pytest.ini_options]`.
- Runtime role: config.
- Direct dependencies worth knowing: `ruff`, `pytest`, `tools` import path,
  `tests` test path.
- Status: active; consumed by lint and test commands.
- Obvious smells: none obvious.

### `requirements-test.txt`

- Language/type: pip requirements.
- Primary responsibility: Pins the test/lint dependency range for pytest and
  Ruff.
- Main exports/classes/functions: `pytest>=8.0,<9.0`, `ruff>=0.12,<1.0`.
- Runtime role: config.
- Direct dependencies worth knowing: Python packaging / pip.
- Status: active; referenced by README, runbook, CI, and `scripts/ci-local.sh`.
- Obvious smells: none obvious.

### `.github/workflows/ci.yml`

- Language/type: GitHub Actions YAML.
- Primary responsibility: Runs CI as three jobs: XML/phyphox validation, Arduino
  compile, and security baseline.
- Main exports/classes/functions: jobs `xml`, `arduino`, `security`.
- Runtime role: config.
- Direct dependencies worth knowing: `actions/checkout`, `actions/setup-python`,
  `actions/cache`, `ruff`, `pytest`, `libxml2-utils`, `ripgrep`,
  `arduino-cli`, `shellcheck`, repository scripts.
- Status: active if GitHub Actions is enabled for this repository; proof would be
  current PR/push workflow runs.
- Obvious smells: some command duplication with `scripts/ci-local.sh`, but the
  split mirrors CI job boundaries.

## Arduino Firmware

### `arduino/phyphox_ble_sense/phyphox_ble_sense.ino`

- Language/type: Arduino C++.
- Primary responsibility: Implements the canonical BLE peripheral named
  `phyphox-sense`; reads Nano 33 BLE Sense sensors and publishes a 20-byte
  float32 payload selected by a config characteristic mode.
- Main exports/classes/functions: global Arduino entrypoints `setup()` and
  `loop()`; internal `Mode`, `writeFloat32LE`, `readFloat32LE`,
  `setModeFromConfig`, `setChannelsFromXYZ`, `readChannels`, `sendSample`,
  `pollConfigCharacteristic`.
- Runtime role: entrypoint.
- Direct dependencies worth knowing: `ArduinoBLE`, `Arduino_APDS9960`,
  `Arduino_HTS221`, `Arduino_LPS22HB`, `Arduino_LSM9DS1`, `<cmath>`,
  `experiments/phyphox_constants.json`, generated core experiment config values,
  `scripts/compile-arduino.sh`.
- Status: active; compiled by `scripts/compile-arduino.sh` and protocol-checked
  by tests and `tools/validate_phyphox.py`.
- Obvious smells: sequential mode branching in `readChannels`; reserved modes
  are a compatibility path; BLE init failure blocks forever with no visible
  diagnostic; sensor init failures are represented only as `NaN` channels.

## Phyphox Source XML

### `src/phyphox/accelerometer_plot_v1-2.phyphox.xml`

- Language/type: phyphox XML with XInclude.
- Primary responsibility: Source for the generated acceleration experiment,
  mode `1.0`, with graph, absolute, multi, simple, and raw data views.
- Main exports/classes/functions: title `Acceleration`; config
  `cddf1003...=1.0`; analysis containers `CH2_norm` through `CH5_norm`.
- Runtime role: domain logic.
- Direct dependencies worth knowing: `includes/containers_ch0_ch5.xml`,
  `includes/bluetooth_outputs_ch1_ch5.xml`, Arduino mode 1, BLE UUID constants.
- Status: active source; generated parity is tested against
  `experiments/accelerometer_plot_v1-2.phyphox`.
- Obvious smells: repeated view/analysis structure shared with gyroscope and
  magnetometer; duplication appears intentional but is a cleanup candidate.

### `src/phyphox/gyroscope_plot_v1-2.phyphox.xml`

- Language/type: phyphox XML with XInclude.
- Primary responsibility: Source for the generated angular velocity experiment,
  mode `2.0`, with graph, absolute, multi, simple, and raw data views.
- Main exports/classes/functions: title `Angular Velocity (Gyroscope)`; config
  `cddf1003...=2.0`; normalized channel analysis containers.
- Runtime role: domain logic.
- Direct dependencies worth knowing: shared XInclude fragments, Arduino mode 2,
  BLE UUID constants.
- Status: active source; generated parity is tested.
- Obvious smells: duplicate structure with accelerometer/magnetometer.

### `src/phyphox/magnetometer_plot_v1-2.phyphox.xml`

- Language/type: phyphox XML with XInclude.
- Primary responsibility: Source for the generated magnetic field experiment,
  mode `3.0`, with graph, absolute, multi, and simple views.
- Main exports/classes/functions: title `Magnetic Field`; config
  `cddf1003...=3.0`.
- Runtime role: domain logic.
- Direct dependencies worth knowing: shared XInclude fragments, Arduino mode 3,
  BLE UUID constants.
- Status: active source; generated parity is tested.
- Obvious smells: duplicate view pattern with other 3-axis sensor experiments.

### `src/phyphox/pressure_plot_v1-2.phyphox.xml`

- Language/type: phyphox XML with XInclude.
- Primary responsibility: Source for the generated pressure experiment, mode
  `4.0`; converts the Arduino kPa channel into hPa for display.
- Main exports/classes/functions: title `Pressure`; config `cddf1003...=4.0`;
  analysis container `CH2_norm`.
- Runtime role: domain logic.
- Direct dependencies worth knowing: shared XInclude fragments, Arduino mode 4,
  BLE UUID constants.
- Status: active source; generated parity and physics expectations are tested.
- Obvious smells: unit conversion is split between firmware comment and XML
  analysis; future edits need both surfaces checked.

### `src/phyphox/temperature_plot_v1-2.phyphox.xml`

- Language/type: phyphox XML with XInclude.
- Primary responsibility: Source for the generated temperature/humidity
  experiment, mode `5.0`, with temperature, humidity, graph, and simple views.
- Main exports/classes/functions: title `Temperature and Humidity`; config
  `cddf1003...=5.0`; empty analysis block.
- Runtime role: domain logic.
- Direct dependencies worth knowing: shared XInclude fragments, Arduino mode 5,
  BLE UUID constants.
- Status: active source; generated parity and physics expectations are tested.
- Obvious smells: no obvious smell.

### `src/phyphox/light_plot_v1-2.phyphox.xml`

- Language/type: phyphox XML with XInclude.
- Primary responsibility: Source for the generated light/RGB experiment, mode
  `6.0`, displaying ambient and RGB channels.
- Main exports/classes/functions: title `Relative Light Level with Colors`;
  config `cddf1003...=6.0`; graph, ambient, RGB, multi, and simple views.
- Runtime role: domain logic.
- Direct dependencies worth knowing: shared XInclude fragments, Arduino mode 6,
  APDS9960 payload layout, BLE UUID constants.
- Status: active source; generated parity and physics expectations are tested.
- Obvious smells: RGB/channel semantics depend on the firmware's CH2..CH5 order;
  this coupling is easy to break without protocol tests.

### `src/phyphox/analog_input_plot_v1-2.phyphox.xml`

- Language/type: phyphox XML with XInclude.
- Primary responsibility: Source for the generated analog input experiment,
  mode `9.0`, showing A0/A1/A2-derived values.
- Main exports/classes/functions: title `Analog Input`; config
  `cddf1003...=9.0`; graph, simple, and raw data views.
- Runtime role: domain logic.
- Direct dependencies worth knowing: shared XInclude fragments, Arduino mode 9,
  analog payload layout, BLE UUID constants.
- Status: active source; generated parity and physics expectations are tested.
- Obvious smells: conversion from raw ADC to displayed quantity is split across
  firmware/XML expectations; verify before changing units.

### `src/phyphox/includes/containers_ch0_ch5.xml`

- Language/type: XML fragment.
- Primary responsibility: Shared data containers for CH0..CH5 used by generated
  core experiments.
- Main exports/classes/functions: six `<container>` definitions.
- Runtime role: domain logic.
- Direct dependencies worth knowing: XInclude expansion in `xmllint`,
  `scripts/build-phyphox.sh`, `tools/validate_xinclude_paths.py`.
- Status: active source; included by every generated core experiment.
- Obvious smells: generic CH names are protocol-driven but not self-describing.

### `src/phyphox/includes/bluetooth_outputs_ch1_ch5.xml`

- Language/type: XML fragment.
- Primary responsibility: Shared BLE data characteristic output mappings for
  CH1..CH5 and app-managed CH0 time.
- Main exports/classes/functions: five float32 little-endian output mappings and
  one `extra="time"` mapping.
- Runtime role: adapter.
- Direct dependencies worth knowing: BLE data characteristic UUID,
  `tools/validate_phyphox.py`, Arduino 20-byte payload contract.
- Status: active source; included by every generated core experiment.
- Obvious smells: hard-coded UUID and offsets are correct by contract but high
  risk if changed without firmware and tests.

## Generated Core Experiments

These files are committed importable artifacts generated from `src/phyphox/*.xml`.
Do not hand-edit them unless the task is specifically about generated output or
the generator.

### `experiments/accelerometer_plot_v1-2.phyphox`

- Language/type: generated phyphox XML.
- Primary responsibility: Importable acceleration experiment for Arduino mode 1.
- Main exports/classes/functions: title `Acceleration`; BLE input/output mapping;
  graph, absolute, multi, simple, and raw data views.
- Runtime role: generated.
- Direct dependencies worth knowing: generated from
  `src/phyphox/accelerometer_plot_v1-2.phyphox.xml`; consumed by phyphox app.
- Status: active generated artifact.
- Obvious smells: generated duplication; inspect source XML instead for changes.

### `experiments/gyroscope_plot_v1-2.phyphox`

- Language/type: generated phyphox XML.
- Primary responsibility: Importable gyroscope experiment for Arduino mode 2.
- Main exports/classes/functions: title `Angular Velocity (Gyroscope)`; BLE
  input/output mapping; graph, absolute, multi, simple, and raw data views.
- Runtime role: generated.
- Direct dependencies worth knowing: generated from
  `src/phyphox/gyroscope_plot_v1-2.phyphox.xml`.
- Status: active generated artifact.
- Obvious smells: generated duplication.

### `experiments/magnetometer_plot_v1-2.phyphox`

- Language/type: generated phyphox XML.
- Primary responsibility: Importable magnetometer experiment for Arduino mode 3.
- Main exports/classes/functions: title `Magnetic Field`; BLE input/output
  mapping; graph, absolute, multi, and simple views.
- Runtime role: generated.
- Direct dependencies worth knowing: generated from
  `src/phyphox/magnetometer_plot_v1-2.phyphox.xml`.
- Status: active generated artifact.
- Obvious smells: generated duplication.

### `experiments/pressure_plot_v1-2.phyphox`

- Language/type: generated phyphox XML.
- Primary responsibility: Importable pressure experiment for Arduino mode 4.
- Main exports/classes/functions: title `Pressure`; hPa normalization analysis;
  graph, simple, and raw data views.
- Runtime role: generated.
- Direct dependencies worth knowing: generated from
  `src/phyphox/pressure_plot_v1-2.phyphox.xml`.
- Status: active generated artifact.
- Obvious smells: generated artifact; source-of-truth is XML source.

### `experiments/temperature_plot_v1-2.phyphox`

- Language/type: generated phyphox XML.
- Primary responsibility: Importable temperature/humidity experiment for Arduino
  mode 5.
- Main exports/classes/functions: title `Temperature and Humidity`; graph,
  temperature, humidity, and simple views.
- Runtime role: generated.
- Direct dependencies worth knowing: generated from
  `src/phyphox/temperature_plot_v1-2.phyphox.xml`.
- Status: active generated artifact.
- Obvious smells: generated artifact.

### `experiments/light_plot_v1-2.phyphox`

- Language/type: generated phyphox XML.
- Primary responsibility: Importable light/RGB experiment for Arduino mode 6.
- Main exports/classes/functions: title `Relative Light Level with Colors`;
  ambient and RGB views.
- Runtime role: generated.
- Direct dependencies worth knowing: generated from
  `src/phyphox/light_plot_v1-2.phyphox.xml`.
- Status: active generated artifact.
- Obvious smells: generated artifact.

### `experiments/analog_input_plot_v1-2.phyphox`

- Language/type: generated phyphox XML.
- Primary responsibility: Importable analog input experiment for Arduino mode 9.
- Main exports/classes/functions: title `Analog Input`; graph, simple, and raw
  data views.
- Runtime role: generated.
- Direct dependencies worth knowing: generated from
  `src/phyphox/analog_input_plot_v1-2.phyphox.xml`.
- Status: active generated artifact.
- Obvious smells: generated artifact.

### `experiments/phyphox_constants.json`

- Language/type: JSON.
- Primary responsibility: Documents BLE UUIDs, active mode IDs, and reserved
  modes for validation and human review.
- Main exports/classes/functions: `bluetooth.service_uuid`,
  `bluetooth.data_char_uuid`, `bluetooth.config_char_uuid`, `modes`,
  `reserved_modes`.
- Runtime role: config.
- Direct dependencies worth knowing: `tools/validate_phyphox.py`,
  `tests/test_repo_guardrails.py`, firmware constants, generated XML.
- Status: active contract file.
- Obvious smells: duplicates constants from firmware and XML by design; tests
  mitigate drift.

## Astronomy Experiments

These `.phyphox` files are hand-edited importable experiments and are not part of
the generated Arduino `phyphox-sense` pipeline unless explicitly changed.

### `experiments/astronomy/albedo.phyphox`

- Language/type: phyphox XML.
- Primary responsibility: Relative reflected-light classroom experiment using
  phone light sensor and SensorTag light input paths.
- Main exports/classes/functions: title `Relative Reflected Light`; views `Phone
  reflectance proxy` and `SensorTag reflectance proxy`; `de`/`fr` translations.
- Runtime role: domain logic.
- Direct dependencies worth knowing: phone light sensor, SensorTag light BLE
  UUIDs, astronomy tests and companion docs.
- Status: active hand-edited experiment.
- Obvious smells: duplicate phone/SensorTag analysis paths; no obvious dead path
  without live device proof.

### `experiments/astronomy/greenhouse.phyphox`

- Language/type: phyphox XML.
- Primary responsibility: Greenhouse-effect analogy using one or two SensorTag
  temperature paths.
- Main exports/classes/functions: title `Greenhouse effect`; views `Comparison`
  and `Single setup`; `de`/`fr` translations.
- Runtime role: domain logic.
- Direct dependencies worth knowing: SensorTag temperature BLE UUIDs, astronomy
  consolidation tests.
- Status: active hand-edited experiment.
- Obvious smells: duplicated SensorTag blocks for two setups; appears intentional
  for comparison mode.

### `experiments/astronomy/ir-dist_habitable.phyphox`

- Language/type: phyphox XML.
- Primary responsibility: Qualitative habitable-zone analogy using IR and
  ambient temperature signals over distance.
- Main exports/classes/functions: title `Habitable Zone: IR Temperature Signal
  and Distance`; views `IR Temperature Signal`, `Temperature trend`, `IR and
  Ambient Temperature`; `de`/`fr` translations.
- Runtime role: domain logic.
- Direct dependencies worth knowing: SensorTag IR temperature BLE UUIDs,
  qualitative wording tests.
- Status: active hand-edited experiment.
- Obvious smells: multi-path SensorTag configuration; usage would be proven by a
  device import/run probe.

### `experiments/astronomy/missiontomars.phyphox`

- Language/type: phyphox XML.
- Primary responsibility: Spaceship-atmosphere classroom pressure experiment
  with phone pressure and SensorTag pressure paths.
- Main exports/classes/functions: title `Checking a Spaceship Atmosphere`; phone
  and SensorTag data/graph views; `de`/`fr` translations.
- Runtime role: domain logic.
- Direct dependencies worth knowing: phone pressure sensor, SensorTag pressure
  BLE UUIDs, astronomy tests.
- Status: active hand-edited experiment.
- Obvious smells: duplicate phone/SensorTag pressure analysis paths; hardware
  availability determines which path is actually used.

### `experiments/astronomy/owon_digital_multimeter-debug.phyphox`

- Language/type: phyphox XML.
- Primary responsibility: Auxiliary/debug importable file for Owon digital
  multimeter Bluetooth data.
- Main exports/classes/functions: title `Digital Multimeter`; view `Value`;
  `de`/`fr` translations.
- Runtime role: adapter.
- Direct dependencies worth knowing: supported Owon multimeter BLE payload;
  transit-method measurement path.
- Status: active but auxiliary/debug; exact classroom usage is UNCLEAR. A live
  Owon import/run or documentation reference would prove use.
- Obvious smells: debug naming in an importable experiment; likely candidate for
  clearer status or archival decision.

### `experiments/astronomy/pt-star.phyphox`

- Language/type: phyphox XML.
- Primary responsibility: Pressure/temperature star-formation analogy using
  SensorTag pressure and temperature.
- Main exports/classes/functions: title `Pressure and Temperature:
  Star-Formation Analogy`; view `Analogy Comparison`; `de`/`fr` translations.
- Runtime role: domain logic.
- Direct dependencies worth knowing: SensorTag pressure/temperature BLE UUIDs,
  astronomy wording tests.
- Status: active hand-edited experiment.
- Obvious smells: no obvious smell from static inspection.

### `experiments/astronomy/tidal-locking.phyphox`

- Language/type: phyphox XML.
- Primary responsibility: Tidal-locking classroom experiment with temperature,
  IR, and light views, using multiple SensorTag-style measurement paths.
- Main exports/classes/functions: title `Tidal locking`; views `Temperature`,
  `IR`, and `Light`; 48 data containers; `de`/`fr` translations.
- Runtime role: domain logic.
- Direct dependencies worth knowing: SensorTag temperature, IR, and light BLE
  UUIDs; astronomy semantic tests.
- Status: active hand-edited experiment.
- Obvious smells: large file with many containers and parallel measurement
  paths; likely overcomplicated relative to the rest of the repo, but device
  workflow may justify it.

### `experiments/astronomy/transitmethode.phyphox`

- Language/type: phyphox XML.
- Primary responsibility: Transit-method classroom experiment combining phone,
  SensorTag, and Owon-style measurement paths plus derived transit/orbital/planet
  calculations.
- Main exports/classes/functions: title `Transit Method`; views `Relative
  Signal`, `Transit Duration`, `Orbital Period`, `Planet Size`, `Trigger
  Configuration`; 65 data containers; `de`/`fr` translations.
- Runtime role: domain logic.
- Direct dependencies worth knowing: phone light sensor, SensorTag light BLE
  UUIDs, Owon/multimeter path, astronomy tests and companion docs.
- Status: active hand-edited experiment.
- Obvious smells: largest source file in the repo; many containers and
  calculation paths increase risk of unclear state/trigger interactions.

## Scripts

### `scripts/build-phyphox.sh`

- Language/type: Bash.
- Primary responsibility: Expands XInclude source XML with `xmllint`, strips
  generated noise, and writes core `experiments/*.phyphox` artifacts.
- Main exports/classes/functions: script entrypoint; optional output directory
  argument or `PHYPHOX_OUTDIR`.
- Runtime role: script.
- Direct dependencies worth knowing: `xmllint`, `python3`,
  `tools/validate_xinclude_paths.py`, `tools/postprocess_phyphox_xml.py`,
  `src/phyphox/*.phyphox.xml`.
- Status: active; used by Makefile, CI, generated parity tests.
- Obvious smells: uses one temp file reused in a loop, which is fine serially;
  no obvious error-swallowing because `set -euo pipefail` is active.

### `scripts/check-generated-clean.sh`

- Language/type: Bash.
- Primary responsibility: Rebuilds generated core experiments into a temp
  directory and compares them against committed `experiments/*.phyphox`.
- Main exports/classes/functions: script entrypoint.
- Runtime role: script.
- Direct dependencies worth knowing: `scripts/build-phyphox.sh`, `cmp`,
  generated core experiments.
- Status: active; used by CI and local CI.
- Obvious smells: none obvious.

### `scripts/validate-xml.sh`

- Language/type: Bash.
- Primary responsibility: Validates source/includes/generated XML, checks safe
  XInclude paths, expands sources, and runs phyphox plausibility checks.
- Main exports/classes/functions: script entrypoint.
- Runtime role: script.
- Direct dependencies worth knowing: `xmllint`, `python3`,
  `tools/validate_xinclude_paths.py`, `tools/postprocess_phyphox_xml.py`,
  `tools/validate_phyphox.py`.
- Status: active; used by Makefile, CI, and local CI.
- Obvious smells: validates generated core experiments only, not astronomy files;
  that may be intentional because astronomy uses different Bluetooth/sensor
  contracts. A written contract would prove intent.

### `scripts/compile-arduino.sh`

- Language/type: Bash.
- Primary responsibility: Installs pinned Arduino core/libraries and compiles the
  canonical Nano 33 BLE sketch.
- Main exports/classes/functions: script entrypoint.
- Runtime role: script.
- Direct dependencies worth knowing: `arduino-cli`, `arduino:mbed_nano@4.5.0`,
  `ArduinoBLE@1.5.0`, `Arduino_LSM9DS1@1.1.1`, `Arduino_HTS221@1.0.0`,
  `Arduino_LPS22HB@1.0.2`, `Arduino_APDS9960@1.0.4`.
- Status: active; used by Makefile, CI, local CI.
- Obvious smells: network/toolchain side effects from installing cores/libs; this
  is expected for compile verification but can be slow or environment-sensitive.

### `scripts/ci-local.sh`

- Language/type: Bash.
- Primary responsibility: Canonical local verification bundle: Ruff, pytest, XML
  validation, generated freshness, Arduino compile, and security baseline.
- Main exports/classes/functions: script entrypoint.
- Runtime role: script.
- Direct dependencies worth knowing: `ruff`, `pytest`, validation/build/compile
  scripts, security scripts.
- Status: active; documented as the full local CI entrypoint.
- Obvious smells: no fallback when `arduino-cli` or `xmllint` is absent; it
  correctly fails rather than claiming partial success.

### `scripts/secret-scan.sh`

- Language/type: Bash.
- Primary responsibility: Scans tracked and untracked non-ignored files for a
  tight set of private-key and token patterns.
- Main exports/classes/functions: script entrypoint; pattern array.
- Runtime role: script.
- Direct dependencies worth knowing: `git`, `rg`.
- Status: active; used by security and CI.
- Obvious smells: comment notes filenames containing colons may be misparsed;
  pattern list is intentionally minimal and not a full secret scanner.

### `scripts/deps-scan.sh`

- Language/type: Bash.
- Primary responsibility: Checks that Arduino core/libs and Python test
  dependencies are version-constrained.
- Main exports/classes/functions: script entrypoint.
- Runtime role: script.
- Direct dependencies worth knowing: `grep`, `requirements-test.txt`,
  `scripts/compile-arduino.sh`.
- Status: active; used by security and CI.
- Obvious smells: parses shell command text rather than an Arduino lockfile;
  acceptable as a lightweight guard but brittle if the compile script is
  restructured.

### `scripts/sast-minimal.sh`

- Language/type: Bash.
- Primary responsibility: Runs `shellcheck` when available and Python bytecode
  compilation over tool/test files.
- Main exports/classes/functions: script entrypoint.
- Runtime role: script.
- Direct dependencies worth knowing: `shellcheck`, `python3`, `find`.
- Status: active; used by security and CI.
- Obvious smells: shellcheck is optional locally but installed in CI; local
  absence weakens the check unless reported.

## Python Tools

### `tools/postprocess_phyphox_xml.py`

- Language/type: Python.
- Primary responsibility: Removes `xml:base` attributes and leftover XInclude
  namespace declarations from expanded phyphox XML.
- Main exports/classes/functions: `postprocess`, `main`.
- Runtime role: adapter.
- Direct dependencies worth knowing: `argparse`, `re`, `sys`; called from build
  and validation scripts.
- Status: active; tested by `tests/test_postprocess_phyphox_xml.py`.
- Obvious smells: regex/string transformation on XML text; acceptable for the
  narrow current cleanup but should not grow into general XML rewriting.

### `tools/validate_xinclude_paths.py`

- Language/type: Python.
- Primary responsibility: Validates XInclude `href` values before `xmllint`
  expansion so includes stay under `src/phyphox/includes/`.
- Main exports/classes/functions: `_include_elements`, `_is_within`,
  `_validate_href`, `validate_xinclude_paths`, `main`.
- Runtime role: adapter.
- Direct dependencies worth knowing: `argparse`, `xml.etree.ElementTree`,
  `pathlib`, `urllib.parse`.
- Status: active; used by build/validation scripts and tested by
  `tests/test_validate_xinclude_paths.py`.
- Obvious smells: none obvious.

### `tools/validate_phyphox.py`

- Language/type: Python.
- Primary responsibility: Performs plausibility checks for generated phyphox
  experiments and enforces UUID/mode consistency across constants, source XML,
  generated XML, and Arduino firmware.
- Main exports/classes/functions: `ValidationError`, `_load_expected_uuids`,
  `_load_expected_modes`, `validate_phyphox`, `main`, helper functions for XML
  traversal.
- Runtime role: domain logic.
- Direct dependencies worth knowing: `argparse`, `json`, `re`,
  `xml.etree.ElementTree`, `dataclasses`, `pathlib`, Arduino sketch,
  `experiments/phyphox_constants.json`, `src/phyphox/*.phyphox.xml`.
- Status: active; used by validation script and heavily tested.
- Obvious smells: largest Python tool; many repository-contract checks in one
  file. The regex dependency on firmware syntax is a compatibility shim and will
  break if constants move or change style.

## Tests

### `tests/__init__.py`

- Language/type: Python package marker.
- Primary responsibility: Marks `tests` as a package; contains no runtime logic.
- Main exports/classes/functions: none.
- Runtime role: test.
- Direct dependencies worth knowing: none.
- Status: active but empty.
- Obvious smells: none.

### `tests/test_phyphox_file_contracts.py`

- Language/type: pytest.
- Primary responsibility: Verifies expected generated/source file inventory,
  source locales/includes, and generated phyphox validation.
- Main exports/classes/functions: `expected_uuids` fixture,
  `test_expected_file_inventory`, `test_source_files_have_supported_locales`,
  `test_source_files_reference_shared_includes`, `test_generated_files_validate`.
- Runtime role: test.
- Direct dependencies worth knowing: `pytest`, `validate_phyphox`.
- Status: active.
- Obvious smells: inventory assertions can become brittle but intentionally guard
  the published classroom surface.

### `tests/test_phyphox_generated_parity.py`

- Language/type: pytest.
- Primary responsibility: Rebuilds core experiments into a temporary directory
  and diffs them against committed generated artifacts.
- Main exports/classes/functions: `_source_files`,
  `test_generated_files_match_sources`.
- Runtime role: test.
- Direct dependencies worth knowing: `subprocess`, `scripts/build-phyphox.sh`,
  `difflib`.
- Status: active.
- Obvious smells: none obvious.

### `tests/test_phyphox_physics.py`

- Language/type: pytest.
- Primary responsibility: Checks physics/unit/display contracts for the core
  generated experiments.
- Main exports/classes/functions: helper XML accessors plus tests for
  accelerometer, gyroscope, magnetometer, pressure, temperature, light, and
  analog input contracts.
- Runtime role: test.
- Direct dependencies worth knowing: generated core `experiments/*.phyphox`,
  `xml.etree.ElementTree`.
- Status: active.
- Obvious smells: some assertions encode UI labels and formulas; this is useful
  behavior coverage but can be brittle during wording/UI changes.

### `tests/test_phyphox_validate.py`

- Language/type: pytest.
- Primary responsibility: Unit-tests `tools/validate_phyphox.py`, including XML
  traversal helpers, required structure, Bluetooth validation, config validation,
  offset plausibility, output blocks, and CLI behavior.
- Main exports/classes/functions: fixtures `valid_phyphox_file`, `xml_factory`;
  classes `TestLocalName`, `TestChild`, `TestChildren`, `TestText`,
  `TestFileErrors`, `TestValidFile`, `TestPhyphoxAttributes`,
  `TestRequiredTopLevel`, `TestDataContainers`, `TestBluetoothValidation`,
  `TestConfigValidation`, `TestContainerReferences`, `TestValidationError`,
  `TestOffsetPlausibility`, `TestOutputBluetoothBlocks`, `TestMainCli`.
- Runtime role: test.
- Direct dependencies worth knowing: `pytest`, `validate_phyphox`, temporary XML
  fixtures.
- Status: active.
- Obvious smells: largest test file; could be split by validator responsibility
  if it becomes harder to maintain.

### `tests/test_postprocess_phyphox_xml.py`

- Language/type: pytest.
- Primary responsibility: Tests post-processing of `xml:base`, XInclude
  namespace stripping, combined cases, edge cases, and CLI file/stdin behavior.
- Main exports/classes/functions: classes `TestPostprocessXmlBase`,
  `TestPostprocessXIncludeNamespace`, `TestPostprocessCombined`,
  `TestPostprocessEdgeCases`, `TestMainFileArg`.
- Runtime role: test.
- Direct dependencies worth knowing: `postprocess_phyphox_xml`, `subprocess`,
  `sys`, `textwrap`.
- Status: active.
- Obvious smells: none obvious.

### `tests/test_validate_xinclude_paths.py`

- Language/type: pytest.
- Primary responsibility: Tests safe XInclude boundary enforcement, including
  path escapes, absolute paths, URL-style hrefs, query/fragment hrefs,
  directories, symlink escapes, and CLI failure.
- Main exports/classes/functions: `_source_with_include`,
  `test_current_source_includes_are_within_allowed_directory`, multiple
  rejection tests, `test_cli_fails_on_unsafe_include_before_expansion`.
- Runtime role: test.
- Direct dependencies worth knowing: `validate_xinclude_paths`, `pytest`,
  `subprocess`, temporary files.
- Status: active.
- Obvious smells: none obvious.

### `tests/test_repo_guardrails.py`

- Language/type: pytest.
- Primary responsibility: Repository-level guardrails for UUID consistency,
  generated-file script behavior, secret-scan behavior, constants shape, and mode
  metadata.
- Main exports/classes/functions:
  `test_service_uuid_matches_between_constants_and_firmware`,
  `test_guardrail_scripts_check_untracked_generated_files`,
  `test_secret_scan_flags_untracked_files`,
  `test_uuid_loader_requires_all_expected_keys`,
  `test_constants_json_documents_reserved_modes`.
- Runtime role: test.
- Direct dependencies worth knowing: `json`, `subprocess`, `validate_phyphox`,
  generated files, scripts.
- Status: active.
- Obvious smells: tests script internals and file text; useful as repo guardrails
  but not pure behavior tests.

### `tests/test_astronomy_audit.py`

- Language/type: pytest.
- Primary responsibility: Guardrails for astronomy experiment inventory,
  locales, didactic wording, bounded claims, and auxiliary/debug status.
- Main exports/classes/functions: `_text`, `_root`, inventory/localization tests,
  and file-specific audit tests for albedo, habitable zone, pt-star,
  mission-to-mars, greenhouse, tidal-locking, Owon debug, and transit method.
- Runtime role: test.
- Direct dependencies worth knowing: `experiments/astronomy/*.phyphox`,
  `xml.etree.ElementTree`.
- Status: active.
- Obvious smells: wording-heavy assertions can be brittle, but they protect
  classroom semantics.

### `tests/test_astronomy_consolidation.py`

- Language/type: pytest.
- Primary responsibility: Verifies that consolidated astronomy files preserve
  combined measurement paths and richer views after repo consolidation.
- Main exports/classes/functions: tests for mission-to-mars, greenhouse,
  tidal-locking, transit method, and albedo consolidation.
- Runtime role: test.
- Direct dependencies worth knowing: hand-edited astronomy `.phyphox` files.
- Status: active.
- Obvious smells: text-presence tests are simple but may miss broken XML
  semantics.

### `tests/test_astronomy_semantics.py`

- Language/type: pytest.
- Primary responsibility: Checks semantic contracts in astronomy files and
  companion docs, including tidal-locking graph inputs/time units, mission labels,
  positive star-radius input, and companion wording.
- Main exports/classes/functions: `_load`, `_view`, `_graphs`, `_graph_inputs`,
  plus five semantic tests.
- Runtime role: test.
- Direct dependencies worth knowing: `experiments/astronomy/*.phyphox`,
  `docs/ASTRONOMY_EXPERIMENTS_COMPANION.md`.
- Status: active.
- Obvious smells: couples XML labels and docs text; useful but potentially
  brittle during copy edits.

## Documentation and Non-Code Source Surfaces

### `README.md`

- Language/type: Markdown.
- Primary responsibility: Main project overview, quickstart, command reference,
  runtime summary, and troubleshooting.
- Main exports/classes/functions: no code exports.
- Runtime role: config.
- Direct dependencies worth knowing: Make targets, scripts, docs, Arduino sketch,
  experiments.
- Status: active user-facing documentation.
- Obvious smells: no obvious smell.

### `CONTRIBUTING.md`

- Language/type: Markdown.
- Primary responsibility: Maintainer workflow, verification commands, core XML
  generation rule, UUID alignment rule, and astronomy localization policy.
- Main exports/classes/functions: no code exports.
- Runtime role: config.
- Direct dependencies worth knowing: `scripts/ci-local.sh`, generated/source XML,
  astronomy files.
- Status: active maintainer guidance.
- Obvious smells: command list duplicates README/AGENTS content; acceptable but
  should be kept synchronized.

### `SECURITY.md`

- Language/type: Markdown.
- Primary responsibility: Security policy surface.
- Main exports/classes/functions: no code exports.
- Runtime role: config.
- Direct dependencies worth knowing: security baseline scripts.
- Status: active policy doc.
- Obvious smells: not inspected deeply in this pass.

### `AGENTS.md`

- Language/type: Markdown.
- Primary responsibility: Durable agent guidance for this repository.
- Main exports/classes/functions: no code exports.
- Runtime role: config.
- Direct dependencies worth knowing: command surface, runtime contracts, final
  response expectations.
- Status: active guidance, currently untracked in this worktree.
- Obvious smells: none obvious.

### `docs/REPO_MAP.md`

- Language/type: Markdown.
- Primary responsibility: Technical map of top-level files, key flows, hot spots,
  and entrypoints.
- Main exports/classes/functions: no code exports.
- Runtime role: config.
- Direct dependencies worth knowing: scripts, tools, firmware, experiment trees.
- Status: active documentation.
- Obvious smells: mentions `agent.md`, which is ignored/local and not present in
  tracked files; verify before relying on it.

### `docs/RUNBOOK.md`

- Language/type: Markdown.
- Primary responsibility: Reproducible setup, fast/full verification loop, and
  manual classroom probe.
- Main exports/classes/functions: no code exports.
- Runtime role: config.
- Direct dependencies worth knowing: Python 3.11+, `xmllint`, `arduino-cli`,
  pinned Arduino libraries, scripts.
- Status: active documentation.
- Obvious smells: no obvious smell.

### `docs/ci.md`, `docs/ci/README.md`, `docs/ci/ci.md`, `docs/ci/ci-decision.md`

- Language/type: Markdown.
- Primary responsibility: CI matrix and CI decision/history documentation.
- Main exports/classes/functions: no code exports.
- Runtime role: config.
- Direct dependencies worth knowing: GitHub Actions workflow and local CI script.
- Status: active docs if maintained with workflow changes; exact freshness is
  UNCLEAR. Comparing each document to `.github/workflows/ci.yml` would prove it.
- Obvious smells: duplicate CI docs in root and `docs/ci/`; possible stale or
  duplicate documentation path.

### `docs/ASTRONOMY_EXPERIMENTS_COMPANION.md`

- Language/type: Markdown.
- Primary responsibility: Teacher/operator companion for astronomy methods,
  physics basis, didactic goal, and scope limits.
- Main exports/classes/functions: no code exports.
- Runtime role: config.
- Direct dependencies worth knowing: `experiments/astronomy/*.phyphox`,
  `tests/test_astronomy_semantics.py`.
- Status: active; referenced by README and tests.
- Obvious smells: must stay synchronized with hand-edited astronomy XML wording.

### `docs/deprecated/audit/*`

- Language/type: Markdown.
- Primary responsibility: Archived audit workspace, remediation runbook,
  progress ledger, didactic and physics audit history.
- Main exports/classes/functions: no code exports.
- Runtime role: deprecated.
- Direct dependencies worth knowing: none for runtime; historical context only.
- Status: deprecated/archived by path; do not treat as active source without
  explicit task scope.
- Obvious smells: deprecated compatibility/archive path; keep out of runtime
  decisions unless a current doc references a specific finding.

## Ignored Local Reference Mirror

### `reference/phyphox-wiki-core/`

- Language/type: mirrored Markdown/HTML/assets.
- Primary responsibility: Local phyphox wiki reference subset.
- Main exports/classes/functions: no repository code exports found from directory
  inventory.
- Runtime role: unknown.
- Direct dependencies worth knowing: ignored by `.gitignore`; not part of tracked
  CI.
- Status: UNCLEAR local reference. It appears intentionally ignored; a current
  doc or task that uses this mirror would prove active usage.
- Obvious smells: local-only reference material can drift from upstream.

### `reference/phyphox-wiki/`

- Language/type: large mirrored website tree.
- Primary responsibility: Local phyphox wiki mirror with HTML/assets and example
  files.
- Main exports/classes/functions: no repository code exports inspected.
- Runtime role: unknown.
- Direct dependencies worth knowing: ignored by `.gitignore`; not tracked; 1,721
  files in this checkout.
- Status: UNCLEAR local reference. Not inspected file by file due size and
  ignored status.
- Obvious smells: very large local mirror; possible stale/deprecated reference
  source if future work relies on it without checking upstream/current docs.

## Highest-Risk Files

1. `arduino/phyphox_ble_sense/phyphox_ble_sense.ino` - real BLE runtime,
   sensor reads, mode switching, payload layout, and failure behavior.
2. `tools/validate_phyphox.py` - central contract validator for UUIDs, modes,
   containers, offsets, and generated experiment plausibility.
3. `src/phyphox/includes/bluetooth_outputs_ch1_ch5.xml` - hard-coded BLE
   payload offsets and UUID mapping shared by every generated core experiment.
4. `experiments/phyphox_constants.json` - duplicated protocol contract that must
   stay aligned with firmware and XML.
5. `experiments/astronomy/transitmethode.phyphox` and
   `experiments/astronomy/tidal-locking.phyphox` - largest hand-edited XML
   experiments with many containers and measurement paths.
6. `scripts/compile-arduino.sh` - installs pinned external Arduino toolchain
   components and compiles firmware.

## Likely Dead Files

- None proven dead from static inspection.
- `experiments/astronomy/owon_digital_multimeter-debug.phyphox` is auxiliary and
  debug-named, but tests explicitly expect it to be marked auxiliary. A live
  Owon workflow or documented classroom dependency is needed before calling it
  dead.
- `docs/deprecated/audit/*` is intentionally archived, not dead production code.
- `reference/` is ignored local reference material; active use is UNCLEAR.

## Likely Overcomplicated Files

- `experiments/astronomy/transitmethode.phyphox` - 1,170 lines, 65 containers,
  multiple input paths and calculation views.
- `experiments/astronomy/tidal-locking.phyphox` - 536 lines, 48 containers,
  multiple SensorTag measurement paths.
- `tools/validate_phyphox.py` - 490 lines combining UUID loading, mode loading,
  XML structure checks, Bluetooth checks, and CLI handling.
- `arduino/phyphox_ble_sense/phyphox_ble_sense.ino` - mostly direct, but
  mode-specific sensor reads are a long branch chain in a runtime-critical loop.

## Likely Deprecated Compatibility Paths

- `docs/deprecated/audit/*` - explicitly deprecated archive.
- Arduino reserved modes `7` and `8` in firmware/constants - deliberate
  forward-compatibility path; keep only with documented contract.
- Silent retention of current mode when config receives reserved mode values -
  compatibility behavior in firmware.
- `reference/` mirrors - local ignored reference snapshots that may be stale.

## Recommended Next Audit Targets

1. Runtime/protocol audit of `phyphox_ble_sense.ino`,
   `experiments/phyphox_constants.json`, `src/phyphox/includes/*`, and
   `tools/validate_phyphox.py`.
2. Astronomy XML audit of `transitmethode.phyphox` and `tidal-locking.phyphox`,
   focusing on container graph correctness, trigger/state semantics, and
   localization drift.
3. Documentation freshness audit of duplicate CI docs versus
   `.github/workflows/ci.yml` and `scripts/ci-local.sh`.
4. Script robustness audit for `secret-scan.sh` filename parsing,
   `deps-scan.sh` shell-text parsing, and local-vs-CI `shellcheck` behavior.
5. Generated/source parity audit after any XML edits: source XML, generated
   artifacts, tests, and README/runbook examples.

## Coverage Gaps and Uncertainty

- No tests, builds, lint, XML validation, Arduino compile, or hardware probes
  were run for this index; this is a read-only/static inventory plus one new
  documentation file.
- `reference/phyphox-wiki-core/` and `reference/phyphox-wiki/` were not
  inspected file by file because they are ignored local mirrors and large
  reference surfaces. Current usage is UNCLEAR; proof would be a tracked doc,
  script, test, or explicit task that relies on them.
- `.github/dependabot.yml` is tracked but currently deleted in the worktree, so
  the live file could not be indexed. Restoring or inspecting Git history would
  be needed to inventory it.
- Astronomy experiment "active" status is inferred from tracked files, README,
  companion docs, and tests. Actual classroom/device usage would require live
  phyphox import and hardware-path probes.
- Firmware runtime behavior was inspected statically only. BLE connection,
  sensor availability, timing, and payload correctness still need device-level
  verification for runtime claims.
