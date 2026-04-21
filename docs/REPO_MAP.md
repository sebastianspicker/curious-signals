# REPO MAP

## Top-Level

- `README.md`: classroom-facing overview and quickstart
- `CONTRIBUTING.md`, `SECURITY.md`: maintainer policy surface
- `experiments/*.phyphox`: committed importable core sensor experiments
- `experiments/astronomy/*.phyphox`: committed importable astronomy experiments with localized UI and their own phone/SensorTag/Owon runtime paths
- `experiments/phyphox_constants.json`: BLE UUID and mode metadata
- `src/phyphox/*.phyphox.xml`: source XML with XInclude deduplication
- `src/phyphox/includes/*`: shared XML fragments
- `arduino/phyphox_ble_sense/phyphox_ble_sense.ino`: canonical Arduino sketch
- `scripts/`: build, validation, compile, and local CI entrypoints
- `tools/`: XML post-processing and phyphox plausibility validation
- `docs/ASTRONOMY_EXPERIMENTS_COMPANION.md`: teacher/operator companion for astronomy methods, physics, and didactics
- `agent.md`: operator guidance for phyphox-specific follow-up work, including fallback behavior when the optional local wiki reference is absent
- `docs/`: runbook, CI notes, archived audit material, and repository map

## Key flows

- Build flow:
  - `scripts/build-phyphox.sh` expands XInclude via `xmllint --xinclude`, post-processes XML, and writes `experiments/*.phyphox`.
- Validation flow:
  - `scripts/validate-xml.sh` validates committed experiments and expanded source output.
  - `tools/validate_phyphox.py` enforces phyphox structure plus UUID alignment with `experiments/phyphox_constants.json` and the Arduino sketch.
- Arduino flow:
  - `scripts/compile-arduino.sh` installs pinned Arduino core/libs and compiles the sketch.
- Local CI flow:
  - `scripts/ci-local.sh` runs `ruff`, `pytest`, XML validation, rebuild freshness, Arduino compile, and the security baseline.

## Hot spots / risks

- XML generation pipeline: `scripts/build-phyphox.sh`, `tools/postprocess_phyphox_xml.py`
- BLE UUID consistency across `experiments/phyphox_constants.json`, XML sources, and Arduino firmware — validated by `tools/validate_phyphox.py` and guardrail tests
- Generation freshness: `scripts/check-generated-clean.sh` enforces that `experiments/*.phyphox` match sources; always rebuild before committing experiment changes
- Keep the Arduino runtime docs separate from the astronomy subtree docs, because the astronomy files currently do not use the `phyphox-sense` firmware path
- Localization drift between English root strings and the `de` / `fr` translation blocks in `experiments/astronomy/*.phyphox`

## Entrypoints

- `make ci-local`
- `bash scripts/ci-local.sh`
- `bash scripts/validate-xml.sh`
