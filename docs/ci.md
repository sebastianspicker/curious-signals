# Continuous Integration

`.github/workflows/ci.yml` runs for pushes, pull requests, and manual workflow
dispatches. It has three jobs and does not deploy, upload firmware, or publish
artifacts.

## XML and Python

The `XML + phyphox validation` job uses Ubuntu 22.04 and Python 3.11. It runs:

```sh
ruff check .
ruff format --check .
pytest
bash scripts/validate-xml.sh
bash scripts/check-generated-clean.sh
```

The generated-file check rebuilds into a temporary directory and compares the
result with tracked root experiments. CI does not rebuild in place before this
comparison.

## Arduino compile

The Arduino job downloads Arduino CLI 1.4.1, restores its caches, and invokes
`scripts/compile-arduino.sh`. That script installs the pinned board core and
libraries before compiling:

```sh
arduino-cli compile \
  --fqbn arduino:mbed_nano:nano33ble \
  arduino/phyphox_ble_sense
```

This job checks compilation for the original Nano 33 BLE Sense. It does not
upload or run the firmware. The CLI archive is version-pinned but is not
verified against a checksum.

## Security checks

The `Security baseline` job runs:

- a narrow scan for selected credential patterns
- Arduino and Python dependency constraint checks
- `bash -n`
- `shellcheck`
- Python bytecode compilation

These checks are repository guardrails, not a complete security assessment.

## Permissions and network access

The workflow grants read-only `contents` and `actions` permissions. Pull
requests use the `pull_request` event, not `pull_request_target`.

The Arduino job downloads the CLI archive, package index, core, and libraries.
Python tools are installed from the bounded ranges in
`requirements-test.txt`.

## Local equivalent

After activating the Python environment:

```sh
make ci-local
```

This runs the same functional categories and may update the local Arduino
package cache. See [the development runbook](RUNBOOK.md) for individual
workflows and troubleshooting.
