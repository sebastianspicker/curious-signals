# CI Overview

This repository uses a single workflow (`.github/workflows/ci.yml`) to validate phyphox files, run Python quality checks, compile the Arduino sketch, and run a minimal security baseline.

## Workflows & Triggers
- `ci`:
  - `push`
  - `pull_request`
  - `workflow_dispatch`

## Jobs
- **XML + phyphox validation**
  - Installs `xmllint`
  - Installs Python test dependencies
  - Runs `ruff check .` and `ruff format --check .`
  - Runs `pytest`
  - Validates `experiments/*.phyphox`, source XML, and expanded source output
  - Rebuilds `experiments/*.phyphox` from `src/phyphox/*.phyphox.xml`
  - Fails if generated experiments are out of date
- **Arduino compile**
  - Installs pinned Arduino CLI
  - Restores cache for Arduino core + libraries
  - Compiles the sketch for `arduino:mbed_nano:nano33ble`
- **Security baseline**
  - Secret scan (tight patterns)
  - Dependency pin check for Arduino core/libs
  - Minimal SAST (bash + python syntax)

## Local Reproduction
The Makefile mirrors CI steps.

```sh
make ci-local
```

Or run the expanded sequence manually:

```sh
make lint
make test
make validate
make build
make compile
make security
```

## Dependencies
- `bash`
- `python3`
- `xmllint` (libxml2)
- `ruff`
- `pytest`
- `arduino-cli` (for `make compile` only)

Note: the compile step downloads Arduino core and library indexes, so it needs outbound network access.

## Caching
The CI caches Arduino CLI data and libraries:
- `~/.arduino15`
- `~/Arduino/libraries`
- `~/.cache/arduino`

This speeds up repeated runs and keeps the compile job stable.

## Secrets & Permissions
- No secrets are required.
- `GITHUB_TOKEN` is read-only (`contents: read`) with cache access.

## Extending CI
- Add a new script in `scripts/` and wire it into the Makefile.
- Add a job or step in `.github/workflows/ci.yml` with a clear name and timeout.
- Prefer pinned versions for tools and dependencies.

## Releasing

To publish a release, tag a version (for example `v1.2.0`) and create a GitHub Release. Optionally attach `phyphox-experiments.zip` from `make bundle` so users can download all experiments in one file.

## Optional: act
If you use `act` locally, prefer `make ci` for parity and keep runtime images minimal. Avoid adding secrets to local runs unless required by new jobs.
