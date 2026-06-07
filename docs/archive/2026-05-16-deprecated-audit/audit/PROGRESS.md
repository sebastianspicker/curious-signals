# phyphox Astronomy Audit Progress

## Current State

- Phase: consolidation and science remediation
- Checkpoint: `M7`
- Status: complete

## Completed Work

- Reset the audit workspace to the astronomy subtree.
- Wrote astronomy-specific didactic and consolidation contract tests.
- Reframed the imported astronomy files so their didactics match the actual classroom method.
- Collapsed duplicate astronomy variants into one canonical file per concept.
- Merged the transit family into a single multisource experiment that supports:
  - smartphone light sensor
  - TI SensorTag light sensor
  - solar cell on the supported Owon multimeter
- Removed the physically invalid `log(T/°C)` habitable-zone view.
- Narrowed the albedo family to a relative reflected-light interpretation.
- Narrowed `pt-star` to an explicit star-formation analogy.
- Narrowed `missiontomars` reference language to cabin-pressure framing instead of Earth altitude physiology.
- Changed the transit relative-size output from a cube-law ratio to a linear radius ratio.
- Fixed the remaining didactic polish issues found in the live re-check:
  - added in-file learner scaffolding to `pt-star.phyphox`
  - retitled `missiontomars.phyphox` toward spaceship atmosphere instead of Mars travel
  - aligned `ir-dist_habitable.phyphox` terminology around IR temperature signal versus distance
  - replaced `2in1` labels in `tidal-locking.phyphox`
  - fixed visible wording defects in `transitmethode.phyphox`
  - clarified the two export columns in `greenhouse.phyphox`
- Normalized the entire astronomy subtree to an English root locale with German and French translations so unsupported phone languages fall back to English.
- Verified the final subtree with targeted pytest, full pytest, XML validation, and diff hygiene.

## Consolidation Campaign

### Merge Batch Ledger

| Batch | Scope | Contract | Science | Runtime | Status | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| M1 | `missiontomars*` | complete | complete | complete | complete | merged into `missiontomars.phyphox` |
| M2 | `greenhouse*` | complete | complete | complete | complete | merged into `greenhouse.phyphox` |
| M3 | `tidal-locking*` | complete | complete | complete | complete | merged into `tidal-locking.phyphox` |
| M4 | smartphone `transitmethode*` | complete | complete | complete | complete | simple/expert folded into `transitmethode.phyphox` |
| M5 | SensorTag and multimeter transit sources | complete | complete | complete | complete | BLE paths folded into `transitmethode.phyphox` |
| M6 | `albedo*` and `ir-dist_habitable*` | complete | complete | complete | complete | science claim narrowed and duplicate files removed |
| M7 | workspace sync | complete | complete | complete | complete | docs, tests, and inventory aligned |

### Consolidation Checkpoint Ledger

| Checkpoint | Gate | Pass Criteria | Status | Evidence |
| --- | --- | --- | --- | --- |
| `M0` | Runbook setup | consolidation runbook and ledger are in place | complete | `docs/deprecated/audit/CONSOLIDATION_RUNBOOK.md` |
| `M1` | First merge contract | merge-contract tests exist for the first low-risk family | complete | `tests/test_astronomy_consolidation.py` |
| `M2` | Low-risk merge gate | `missiontomars*` merged and validated | complete | pytest + XML validation |
| `M3` | Comparative-family gate | `greenhouse*` and `tidal-locking*` merged and validated | complete | pytest + XML validation |
| `M4` | Transit UI merge gate | smartphone transit variants merged into one file | complete | pytest + XML validation |
| `M5` | Multi-source gate | shared source normalization exists for transit | complete | pytest + XML validation |
| `M6` | High-risk science gate | `albedo*` and `ir-dist_habitable*` are repaired or explicitly narrowed | complete | file/content recheck + tests |
| `M7` | Closure gate | docs, inventory, and tests are synchronized | complete | `docs/deprecated/audit/*`, `git diff --check` |

## Final Inventory

- `experiments/astronomy/albedo.phyphox`
- `experiments/astronomy/greenhouse.phyphox`
- `experiments/astronomy/ir-dist_habitable.phyphox`
- `experiments/astronomy/missiontomars.phyphox`
- `experiments/astronomy/owon_digital_multimeter-debug.phyphox`
- `experiments/astronomy/pt-star.phyphox`
- `experiments/astronomy/tidal-locking.phyphox`
- `experiments/astronomy/transitmethode.phyphox`

## Verification Snapshot

- `pytest -q tests/test_astronomy_consolidation.py tests/test_astronomy_audit.py`
- `python3 -m pytest -q`
- `bash scripts/validate-xml.sh`
- `git diff --check`

## Latest Read-Only Re-Check

- Date: `2026-04-15`
- Scope: didactic re-audit and remediation closure for all files in `experiments/astronomy/`
- Result: pass
- Evidence: `docs/deprecated/audit/DIDACTIC_AUDIT.md`
- Open items:
  - none in the previously identified didactic-fix set

## Resume Note

Resume from maintenance, not baseline remediation. If the astronomy subtree changes again:

1. update the relevant contract tests first
2. rerun `pytest -q tests/test_astronomy_consolidation.py tests/test_astronomy_audit.py`
3. rerun `bash scripts/validate-xml.sh`
4. update the audit notes only after the checks are green
