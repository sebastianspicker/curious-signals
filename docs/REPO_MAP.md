# Repository Map

## Product boundaries

The repository contains two experiment sets with different source ownership.

### Core sensor experiments

- `arduino/phyphox_ble_sense/phyphox_ble_sense.ino` is the firmware entry point
  for the original Nano 33 BLE Sense.
- `src/phyphox/*.phyphox.xml` contains the seven editable experiment sources.
- `src/phyphox/includes/*.xml` contains shared containers and BLE mappings.
- `experiments/*.phyphox` contains generated, importable output.
- `experiments/phyphox_constants.json` defines UUIDs and active mode IDs for
  validation.

### Astronomy experiments

- `experiments/astronomy/*.phyphox` contains eight hand-maintained files.
- Seven files are classroom experiments.
- `owon_digital_multimeter-debug.phyphox` is an integration helper for the
  multimeter transit path.
- These files use phone sensors, TI SensorTags, a Bluetooth HID mouse, or Owon
  B35T and W18B decoder paths. They do not use the Arduino firmware.
- `docs/ASTRONOMY_EXPERIMENTS_COMPANION.md` documents their measurement and
  interpretation limits.

## Core generation flow

```text
src/phyphox/*.phyphox.xml
        +
src/phyphox/includes/*.xml
        |
        v
tools/validate_xinclude_paths.py
        |
        v
xmllint --xinclude
        |
        v
tools/postprocess_phyphox_xml.py
        |
        v
experiments/*.phyphox
```

`scripts/build-phyphox.sh` owns this flow. It checks include paths, expands
XInclude, removes expansion metadata, and writes the seven generated files.

`scripts/check-generated-clean.sh` uses a temporary directory and compares file
count, names, and bytes with the tracked outputs. It does not modify the
working tree.

## Validation flow

`scripts/validate-xml.sh`:

1. parses source, include, and generated XML with `xmllint`
2. enforces the local XInclude boundary
3. expands every source file
4. validates the committed generated experiments
5. postprocesses and validates each expanded source

`tools/validate_phyphox.py` checks document structure, container references,
Bluetooth input and output mappings, UUIDs, byte offsets, config values, and
active mode agreement across the constants file, firmware, and source XML.

Astronomy tests inspect `experiments/astronomy/` directly. The core generator
and core validator select only root `experiments/*.phyphox` files.

## Test suite

The active pytest suite is deliberately compact:

| File | Responsibility |
| --- | --- |
| `test_runtime_contracts.py` | XML validation, local XInclude confinement, and postprocessing behavior using inline data |

Test caches and reports are ignored; active test source files are not.

## Firmware flow

`setup()` initializes the four onboard sensor interfaces, starts BLE, registers
the service and characteristics, sets mode 1, and advertises as
`phyphox-sense`.

`loop()` polls BLE and config writes. When a central is connected, it sends a
20-byte notification no more frequently than every 50 ms. Only the active
mode's inputs are read.

The config characteristic accepts exactly four bytes interpreted as a
little-endian `float32`. Valid active mode values select a sensor path.
Reserved, invalid, and incorrectly sized values leave the active mode
unchanged. The characteristic is then written back with the normalized active
mode.

Output channels start as `NaN` for each sample. Values remain `NaN` when a
sensor did not initialize or has no fresh sample. Analog mode reads A0, A1, and
A2 directly.

## Main entry points

| Command | Action |
| --- | --- |
| `make lint` | Run Ruff lint and format checks |
| `make test` | Run pytest |
| `make validate` | Validate XML, includes, and phyphox contracts |
| `make check-generated` | Compare tracked output with a temporary rebuild |
| `make build` | Regenerate tracked core experiments |
| `make compile` | Install pinned Arduino packages and compile firmware |
| `make security` | Run local secret, dependency, shell, and Python checks |
| `make ci-local` | Run all local checks, including firmware compilation |
| `make bundle` | Regenerate and zip the seven core experiments |

## High-impact changes

- UUID, mode, or packet layout changes affect firmware and every core
  experiment.
- XInclude or postprocessing changes affect all generated core files.
- Running an in-place build before the parity check can hide stale committed
  output.
- Sensor-library changes can change the supported board revision.
- Astronomy normalization changes can affect several hardware input paths.
- Embedded images and inherited experiment content require provenance review
  before redistribution.
