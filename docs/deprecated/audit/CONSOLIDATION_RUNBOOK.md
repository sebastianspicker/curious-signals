# phyphox Astronomy Consolidation Runbook

## Purpose

This runbook defines the operator-facing consolidation procedure for the
astronomy subtree under `experiments/astronomy/`.

The current repo state already reflects the desired steady state: one canonical
`.phyphox` file per astronomy concept. Use this runbook only if future work
reintroduces duplicate variants or adds a new sensor path that should be folded
back into an existing concept file.

The objective is to consolidate without weakening:

- physics correctness
- astronomy correctness
- phyphox file-format correctness
- classroom usability

This is not a cosmetic cleanup. A merge is only acceptable if the resulting
file remains scientifically bounded, operationally valid, and easier to
maintain than the split variants it replaces.

## Use This Runbook For

- merging simple and expert variants into one file
- merging same-concept smartphone and BLE variants into one file
- introducing shared canonical data pipelines for multi-sensor support
- deciding when **not** to merge a family yet

Do not use this runbook for:

- purely textual/didactic edits with no structural merge
- read-only science audits
- firmware-only changes unless a merge requires new transport support

## Canonical References

Use these in order:

1. If present locally, `reference/phyphox-wiki-core/file-format.md`
2. If present locally, `reference/phyphox-wiki-core/analysis-modules.md`
3. If present locally, `reference/phyphox-wiki-core/commands-and-transport.md`
4. `docs/deprecated/audit/PHYSICS_ASTRONOMY_AUDIT.md`
5. `docs/deprecated/audit/DIDACTIC_AUDIT.md`
6. repo experiment files and consolidation tests

If a planned merge conflicts with the red findings in
`PHYSICS_ASTRONOMY_AUDIT.md`, fix the science contract first or defer the merge.

## Strategic Rule

Prefer:

- one file per concept
- multiple static views for learner progression
- multiple input adapters feeding one canonical science pipeline

Avoid:

- dynamic UI tricks that try to hide large parts of the experiment
- duplicated science formulas across variants
- mixing raw source-specific buffers directly into shared views

In phyphox, `views` are presentation and `analysis` is the real computation
graph. Design around that fact.

## Steady-State Target Matrix

Keep exactly these teaching files as the canonical astronomy set:

- `albedo.phyphox`
- `greenhouse.phyphox`
- `ir-dist_habitable.phyphox`
- `missiontomars.phyphox`
- `pt-star.phyphox`
- `tidal-locking.phyphox`
- `transitmethode.phyphox`

Keep this file only as an auxiliary helper:

- `owon_digital_multimeter-debug.phyphox`

If a future branch introduces concept-specific variants, merge them back into
the canonical file for that concept unless the science contract makes that
unsafe.

## Canonical Merged-File Architecture

Every merged concept should use this internal layering.

### 1. Raw source layer

One set of containers per supported source, for example:

- `raw_phone`, `t_phone`
- `raw_sensortag`, `t_sensortag`
- `raw_multimeter`, `t_multimeter`

### 2. Source conversion layer

Each hardware path converts its raw data into the same physical quantity:

- pressure -> `p_source`
- reflected light -> `signal_source`
- transit signal -> `signal_source_rel`

No astronomy formulas should run directly on source-specific raw buffers.

### 3. Canonical science layer

All shared views and derived values must consume a single canonical layer:

- `signal`
- `t`
- `baseline`
- `signal_rel`
- concept-specific derived outputs

### 4. UI/state layer

Use explicit state containers for settings and user input:

- `source_mode`
- `expert_mode`
- thresholds
- reference values such as `R_star`

### 5. View progression

Order the tabs by user maturity:

1. primary measurement view
2. derived beginner result
3. advanced interpretation
4. calibration / trigger / source selection

This is the preferred replacement for separate `basic` and `expert` files.

## Design Patterns

### Pattern A: Simple + Expert in one file

Use one shared `analysis` graph and multiple static `views`.

Recommended structure:

- beginner views first
- advanced views later
- settings/calibration last

Do not rely on a true checkbox-driven hidden UI. If an expert toggle is needed,
use it only to gate calculations or defaults, not to remove views.

### Pattern B: Smartphone + external sensor in one file

Use:

- one source-specific input block per hardware path
- one normalization block per hardware path
- one source selector feeding the canonical buffers

The downstream science must not care whether the source was phone, SensorTag,
or multimeter.

### Pattern C: Comparison + single-arm variant in one file

For files like `greenhouse`:

- keep both channels in the data model
- allow the second channel to remain empty
- provide a `Single Setup` view and a `Comparison` view

Do not duplicate the entire file just because one comparison arm is absent.

## Merge Readiness Rules

A family is merge-ready only if all of the following are true:

- the underlying science claim is already acceptable or explicitly bounded
- the variants differ mainly by UI exposure, sensor input, or small adapter logic
- shared formulas can be factored into one canonical science layer
- empty inactive sources can be tolerated without breaking the analysis graph
- views can be reorganized without changing the core meaning of the experiment

Do not merge a family yet if:

- the current formulas are already scientifically red
- the hardware paths measure different physical quantities and no normalization layer exists
- the only way to merge would be duplicating large chunks of analysis inside one file

## Consolidation Priority

If future drift appears, prefer this order:

1. same-concept simple/expert duplicates
2. same-concept phone versus SensorTag duplicates
3. extra transit source variants
4. anything that would change the science contract

Rationale:

- UI-only duplication is the safest to remove
- input-path duplication is next
- science-contract changes are highest risk and should be last

## TDD Loop For Each Merge Batch

For every duplicated concept family:

1. inventory the variants and mark one file as the temporary source of truth
2. write or extend the smallest regression tests that define the canonical merged contract
3. make the tests fail against the duplicate state if the contract is not yet represented
4. merge the file structure around the canonical architecture
5. rerun the targeted tests
6. rerun XML validation
7. rerun broader astronomy tests if shared invariants changed
8. update `PROGRESS.md`

Required mindset:

- one merged concept at a time
- no opportunistic extra edits
- no silent formula changes

## Required Test Surfaces

Each merged family needs explicit tests for:

### Structural contract

- expected number of files after merge
- expected set of views
- expected shared exports
- no dangling source-specific references in canonical views

### Source contract

- each supported sensor path maps into canonical buffers
- inactive source paths do not break analysis assumptions
- units are correct at the canonical layer

### Science contract

- merged formulas match the intended classroom model
- renamed outputs are semantically correct
- no degraded astronomy claim appears after the merge

### UI contract

- beginner workflow works without advanced controls
- advanced controls do not change baseline outputs unless explicitly intended

## Checkpoints

- `M0`: consolidation runbook and ledger are in place
- `M1`: merge-contract tests exist for the affected concept
- `M2`: low-risk duplicate variants are merged and validated
- `M3`: comparison-style families remain valid after consolidation
- `M4`: simple/expert transit duplication is merged into one file
- `M5`: multi-source transit normalization remains valid
- `M6`: any science-boundary changes are resolved or explicitly deferred with rationale
- `M7`: docs, tests, and file inventory synchronized after consolidation

Checkpoint rules:

- only one checkpoint may be in progress at a time
- do not skip ahead because a later family looks easier
- a checkpoint is not complete until its gate evidence is written into `PROGRESS.md`

## Gates

### Gate G1: Merge contract

Pass criteria:

- targeted tests encode the merged structure and source behavior

Evidence:

- `tests/test_astronomy_audit.py`
- any new family-specific tests

### Gate G2: XML / file-format validity

Pass criteria:

- merged file parses cleanly and passes phyphox plausibility checks

Evidence:

- `bash scripts/validate-xml.sh`
- `python3 tools/validate_phyphox.py` when needed

### Gate G3: Shared science integrity

Pass criteria:

- merged formulas still satisfy the intended astronomy contract
- no output label now overclaims the math

Evidence:

- targeted pytest checks
- relevant audit notes updated if science scope changes

### Gate G4: View usability

Pass criteria:

- beginner views exist and remain coherent
- advanced settings are separated, not interleaved into the beginner workflow

Evidence:

- file inspection with line references
- tests where feasible

### Gate G5: Workspace sync

Pass criteria:

- `README.md`, `PROGRESS.md`, and relevant audit notes match the new file layout

Evidence:

- `git diff --check`

## Per-Family Acceptance Criteria

### `missiontomars.phyphox`

- the canonical file supports phone pressure and SensorTag pressure
- one canonical `p` / `t` pipeline
- no duplicated statistics logic

### `greenhouse.phyphox`

- the canonical file supports single-arm and comparison use
- second channel may be absent without corrupting the first
- views clearly distinguish `Single Setup` vs `Comparison`

### `tidal-locking.phyphox`

- the canonical file keeps the richer comparison surface
- duplicate concepts are not split across files again

### `transitmethode.phyphox`

- simple and expert remain view layers, not separate files
- source normalization exists before phone, SensorTag, and multimeter paths share one science pipeline
- the learner-facing outputs still describe a relative signal and derived radius ratio correctly

### `albedo.phyphox`

- if new variants appear, merge only after deciding whether the concept remains a relative reflected-light comparison or gains actual albedo normalization

### `ir-dist_habitable.phyphox`

- if new variants appear, merge only after the astronomy model is bounded
- no log-Celsius or arbitrary-distance quantitative claim survives into the canonical file without explicit justification

## Resume Rules

Before resuming:

1. read `docs/deprecated/audit/PROGRESS.md`
2. identify the last green `M*` checkpoint
3. identify the first pending or reopened merge batch
4. inspect the last touched canonical file and its tests
5. continue from that file only

Do not:

- reopen already-green families unless a shared invariant changed
- merge two unrelated concepts in one batch
- mark a family merged before the old redundant file is either removed or explicitly retained with rationale

## Recommended Verification Commands

- `pytest -q tests/test_astronomy_audit.py`
- `pytest -q`
- `bash scripts/validate-xml.sh`
- `python3 tools/validate_phyphox.py <file>`
- `git diff --check`

## Operator Notes

- If a family has a red scientific finding, fix the concept boundary before the merge.
- If a merge requires duplicated science formulas, stop and redesign around a canonical layer.
- If the multimeter transit path cannot be normalized cleanly, keep it separate until the normalization contract is explicit.
