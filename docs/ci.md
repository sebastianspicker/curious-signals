# CI

The consolidated validation matrix keeps the existing required job names and expands the XML job to cover Python quality checks.

## Jobs

- `XML + phyphox validation`
  - install Python test dependencies
  - `ruff check .`
  - `ruff format --check .`
  - `pytest`
  - `bash scripts/validate-xml.sh`
  - `bash scripts/build-phyphox.sh`
  - `bash scripts/check-generated-clean.sh`
- `Arduino compile`
  - install `arduino-cli`
  - compile the canonical `arduino/phyphox_ble_sense/` sketch
- `Security baseline`
  - secret scan
  - dependency pin check
  - minimal shell/python static checks

## Local equivalent

```sh
bash scripts/ci-local.sh
```
