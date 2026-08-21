# Development Runbook

Run all commands from the repository root.

## Setup

Use Python 3.11, matching CI:

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-test.txt
```

Install `xmllint`, `arduino-cli`, `ripgrep`, and `shellcheck` separately. The
Arduino compile script installs these pinned packages when they are absent:

- `arduino:mbed_nano@4.5.0`
- `ArduinoBLE@1.5.0`
- `Arduino_LSM9DS1@1.1.1`
- `Arduino_HTS221@1.0.0`
- `Arduino_LPS22HB@1.0.2`
- `Arduino_APDS9960@1.0.4`

On macOS with Homebrew:

```sh
brew install libxml2 arduino-cli ripgrep shellcheck
```

## Core experiment workflow

The editable core files are `src/phyphox/*.phyphox.xml` and the shared
fragments in `src/phyphox/includes/`.

1. Edit the source or shared fragment.
2. Run focused tests while iterating.
3. Regenerate the seven tracked experiments with `make build`.
4. Run `make check-generated` and `make validate`.
5. Review `git diff -- src/phyphox experiments`.

`make build` writes to `experiments/`. For a non-default output location, call
the script directly:

```sh
PHYPHOX_OUTDIR=/tmp/phyphox-output bash scripts/build-phyphox.sh
```

An output directory supplied as the first positional argument takes precedence
over `PHYPHOX_OUTDIR`.

Do not run files in `experiments/astronomy/` through this generator.

## Astronomy experiment workflow

Astronomy files are edited directly. Keep source-specific input processing
separate from the common physical quantity consumed by views and exports.

Run:

```sh
pytest -q tests/test_runtime_contracts.py
bash scripts/validate-xml.sh
```

Review English root strings and German and French translations. Update
`docs/ASTRONOMY_EXPERIMENTS_COMPANION.md` if the measurement path, model, or
interpretation limit changes.

## Firmware workflow

Compile without uploading:

```sh
make compile
```

This updates the Arduino package index, installs missing pinned packages, and
compiles for `arduino:mbed_nano:nano33ble`. It may require network access. It
does not verify sensor initialization, BLE discovery, packet timing, or
phyphox behavior.

For a manual device test:

1. Record the board revision. The supported target is the original Nano 33 BLE
   Sense, not Rev2.
2. List connected boards with `arduino-cli board list`.
3. Upload the sketch:

   ```sh
   arduino-cli upload -p <serial-port> \
     --fqbn arduino:mbed_nano:nano33ble \
     arduino/phyphox_ble_sense
   ```

4. Import a core experiment into phyphox.
5. Confirm that `phyphox-sense` connects and the expected channels update.
6. Test a second mode.
7. Confirm that invalid and reserved config writes do not change the readable
   active mode.
8. Record unavailable sensor samples as `NaN`, not valid zero values.

The upload and device steps require hardware and are not automated.

## Validation

Use the fast local sequence during development:

```sh
make lint
make test
make validate
make check-generated
make security
```

`make check-generated` rebuilds into a temporary directory and compares the
result byte for byte with tracked outputs. Run it before any in-place rebuild
when checking whether committed output was already current.

Run the complete local CI entry point before proposing a change:

```sh
make ci-local
git diff --check
```

`make ci-local` adds the pinned Arduino compile. Passing it does not verify
hardware or authorize a release.

## Packaging

Create a zip containing the seven root experiments:

```sh
make bundle
```

This command regenerates the core experiments before writing
`phyphox-experiments.zip`. The archive does not include
`experiments/astronomy/`.

## Troubleshooting

### Python tools are missing

Activate `.venv` and reinstall:

```sh
python -m pip install -r requirements-test.txt
```

### `xmllint` is missing

Install libxml2 utilities and confirm that `xmllint` is on `PATH`.

### Arduino package installation fails

Confirm outbound network access and retry `make compile`. Do not remove version
pins to work around a transient failure.

### Generated parity fails

Run `make build`, inspect the source and generated diff, then rerun
`make check-generated`.

### Sensor channels remain `NaN`

Confirm the board revision and pinned sensor libraries. The firmware uses
`NaN` when a sensor did not initialize or has no fresh sample.

### The board is not visible in phyphox

Confirm that the board is powered and not connected to another BLE central.
Connect from phyphox, then power-cycle and reflash the board if discovery still
fails. The firmware has no visible diagnostic for BLE initialization failure.

## Release preparation

Before selecting a release candidate, run the full local validation, review the
complete diff and tracked tree, test the supported hardware path, and resolve
the blockers in [RELEASE_STATUS.md](../RELEASE_STATUS.md). No workflow in this
repository publishes a release.
