# CI

The repository uses one GitHub Actions workflow, `.github/workflows/ci.yml`, to
validate generated phyphox files, Python tooling, Arduino compilation, and a
small security baseline.

The workflow runs on:

- `push`
- `pull_request`
- `workflow_dispatch`

Archive and reference-only paths are ignored by push and pull request triggers:

- `docs/archive/**`
- `docs/deprecated/**`
- `docs/ci/**`
- `reference/**`

No scheduled or secret-requiring jobs are configured.

## Jobs

- `XML + phyphox validation`
  - install `xmllint` and `ripgrep`
  - install Python test dependencies
  - `ruff check .`
  - `ruff format --check .`
  - `pytest`
  - `bash scripts/validate-xml.sh`
  - `bash scripts/build-phyphox.sh`
  - `bash scripts/check-generated-clean.sh`
- `Arduino compile`
  - install a pinned `arduino-cli` release
  - restore Arduino core/library cache
  - compile the canonical `arduino/phyphox_ble_sense/` sketch
- `Security baseline`
  - `bash scripts/secret-scan.sh`
  - `bash scripts/deps-scan.sh`
  - `bash scripts/sast-minimal.sh`

## Permissions and caches

- `GITHUB_TOKEN` is read-only: `contents: read`, `actions: read`.
- The workflow uses `pull_request`, not `pull_request_target`, so fork PRs do
  not receive elevated repository permissions.
- The Arduino job caches toolchain state under `~/.arduino15`,
  `~/Arduino/libraries`, and `~/.cache/arduino`.

## Local equivalent

```sh
bash scripts/ci-local.sh
```

For a shorter local loop, run:

```sh
ruff check .
ruff format --check .
pytest
bash scripts/validate-xml.sh
bash scripts/check-generated-clean.sh
```

`make compile` and the Arduino compile job require outbound network access when
the pinned Arduino core or libraries are not already installed.
