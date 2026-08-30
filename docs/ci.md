# Continuous Integration

`.github/workflows/ci.yml` runs on pushes, pull requests, and manual dispatch.
It has read-only repository permissions and cancels superseded runs on the same
ref.

## XML and Python

The first job installs Python 3.11, the package's `test` extra, `xmllint`, and
`ripgrep`, then runs:

```sh
make lint
make test
make validate
make check-generated
```

Validation covers the protocol catalog, firmware/source conformance, core XML,
expanded core experiments, committed generated artifacts, and astronomy XML and
locales. The parity check rebuilds in a temporary directory. CI never runs
`make build` and never rewrites tracked artifacts.

## Firmware

The Arduino job downloads Arduino CLI 1.4.1 and verifies the pinned Linux
archive SHA-256 before extraction. It restores the Arduino package cache and
runs `make compile`, which installs the pinned Nano core and sensor libraries
before compiling for `arduino:mbed_nano:nano33ble`.

This job does not upload or run firmware on a physical board. Package-index,
core, and library downloads remain separate network trust boundaries from the
verified CLI archive.

## Security

The security job installs `ripgrep` and ShellCheck, then runs `make security`.
That gate checks tracked and untracked files for a narrow set of credential
patterns, dependency and Arduino pin sanity, shell syntax, ShellCheck, and
Python syntax.

These checks are repository guardrails, not a substitute for supply-chain,
firmware, hardware, electrical, licensing, or content-provenance review.

## Local equivalent

```sh
make ci
```

The full local target does not rewrite the checkout, but it includes the same
network-backed firmware compile and may update user-level Arduino CLI state.
