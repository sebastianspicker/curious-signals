# phyphox Astronomy Remediation Runbook

## Purpose

This runbook defines the operator-facing remediation procedure for the current
astronomy subtree under `experiments/astronomy/`.

The current repo state is already consolidated. Use this runbook when a future
change reopens a physics, didactic, localization, or phyphox-format defect in
one of the canonical astronomy files.

This campaign is test-driven. A change is not complete until the failing check
is identified, the fix is applied, and the relevant verification gate passes.

## Canonical References

Use these in order:

1. If present locally, `reference/phyphox-wiki-core/file-format.md`
2. If present locally, `reference/phyphox-wiki-core/analysis-modules.md`
3. If present locally, `reference/phyphox-wiki-core/commands-and-transport.md`
4. `docs/ASTRONOMY_EXPERIMENTS_COMPANION.md`
5. Repo experiment files and tests

`reference/phyphox-wiki-core/` is intentionally untracked. In a fresh clone,
skip directly to the tracked repo docs and sources.

## Scope

Audit and remediate the astronomy subtree as it exists now:

- `experiments/astronomy/*.phyphox`
- `tools/validate_phyphox.py` if the astronomy files reveal missing contract
  coverage
- `tests/test_astronomy_audit.py`
- `tests/test_astronomy_consolidation.py`

Do not mix this campaign with the earlier classroom sensor audit unless the
scope is deliberately expanded again.

## Inventory

Current canonical astronomy files:

- `albedo.phyphox`
- `greenhouse.phyphox`
- `ir-dist_habitable.phyphox`
- `missiontomars.phyphox`
- `owon_digital_multimeter-debug.phyphox`
- `pt-star.phyphox`
- `tidal-locking.phyphox`
- `transitmethode.phyphox`

Special cases:

- `owon_digital_multimeter-debug.phyphox` is an auxiliary debug artifact, not a
  classroom astronomy lesson.
- `transitmethode.phyphox` is the only multisource transit teaching file and
  therefore carries the highest drift risk for source-path wording and derived
  quantity labels.
- All canonical astronomy files should now be English-root with German and
  French translations.

## What Must Be Checked

### File-format correctness

- valid XML structure
- correct phyphox root and namespace handling
- coherent `data-containers`, `input`, `output`, `views`, `analysis`, and
  `export` wiring
- legal BLE/network attributes
- no dangling buffer references
- generated artifacts remain internally consistent

### Physics correctness

- the experiment matches the intended astronomy concept
- units, signs, scaling, and time constants are defensible
- the title, description, and plot labels do not overclaim
- the classroom interpretation matches the actual sensor or measured effect

### Didactic correctness

- the file teaches the intended concept instead of a misleading shortcut
- debug/helper files are quarantined from the teaching story

### Localization correctness

- locale root is `en`
- `de` and `fr` translations exist and match the learner-facing contract
- unsupported phone locales fall back to English cleanly

## TDD Loop

For each affected file:

1. write the smallest regression test that captures the risk
2. observe the failure
3. fix the XML or the shared validation code
4. rerun the targeted test
5. rerun the broader astronomy gate
6. update `PROGRESS.md`

Do not approve a file because it "looks fine" in a viewer.

## Checkpoints

- `R0`: failing condition is reproduced and scoped to one file or shared contract
- `R1`: regression test is in place
- `R2`: targeted fix is applied
- `R3`: targeted and broad astronomy gates are green
- `R4`: docs/progress are synchronized if the learner-facing contract changed

Checkpoint rules:

- advance one checkpoint at a time
- fix shared issues at the shared source
- do not close a checkpoint without evidence in `PROGRESS.md`

## Resume Rules

Before resuming work:

1. read `PROGRESS.md`
2. identify the last green checkpoint
3. identify the first red or pending gate
4. inspect the first problematic file
5. continue from there

Do not:

- merge unrelated fixes into one batch
- mark a checkpoint green without running the relevant checks

## Recommended Verification Commands

- `pytest -q tests/test_astronomy_audit.py tests/test_astronomy_consolidation.py`
- `python3 -m pytest -q`
- `bash scripts/validate-xml.sh`
- `git diff --check`
