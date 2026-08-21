# Continuous Integration

`.github/workflows/ci.yml` runs for pushes, pull requests, and manual workflow
dispatches. It has three jobs and does not deploy, upload firmware, or publish
artifacts.

Archive and reference-only paths are ignored by push and pull request triggers:

- `docs/archive/**`
- `docs/deprecated/**`
- `docs/ci/**`
- `reference/**`

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

The Arduino job downloads Arduino CLI 1.4.1, verifies the Linux archive against
the SHA-256 digest published on the upstream GitHub release, restores its
caches, and invokes `scripts/compile-arduino.sh`. Extraction fails closed when
the archive does not match the pinned digest. The compile script installs the
pinned board core and libraries before compiling:

```sh
arduino-cli compile \
  --fqbn arduino:mbed_nano:nano33ble \
  arduino/phyphox_ble_sense
```

This job checks compilation for the original Nano 33 BLE Sense. It does not
upload or run the firmware. Checksum verification covers the CLI archive only;
the Arduino package index, board core, and libraries remain network trust
boundaries even though their versions are pinned.

## Security checks

The `Security baseline` job runs:

- a narrow scan for selected credential patterns
- Bash guardrails for generated-file parity, missing sources, and untracked
  secret scanning
- Arduino and Python dependency constraint checks
- `bash -n`
- `shellcheck`
- Python bytecode compilation

These checks are repository guardrails, not a complete security assessment.

## Permissions and network access

The primary workflow grants read-only `contents` and `actions` permissions. Pull
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
