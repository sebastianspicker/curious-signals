# Archived Audit Workspace

This workspace is the persistent operator-facing area for the phyphox
astronomy audit campaign.

Current scope:

- `experiments/astronomy/*.phyphox`
- `tools/validate_phyphox.py`
- `arduino/phyphox_ble_sense/phyphox_ble_sense.ino` when a file maps back to
  the shared Arduino classroom firmware
- the optional local phyphox wiki core in `reference/phyphox-wiki-core/` when
  that untracked reference exists locally

## Canonical Reference Order

When `reference/phyphox-wiki-core/` exists locally:

1. `reference/phyphox-wiki-core/file-format.md`
2. `reference/phyphox-wiki-core/analysis-modules.md`
3. `reference/phyphox-wiki-core/commands-and-transport.md`
4. Repo sources and generated artifacts

When it does not exist, start directly with the tracked repo docs and files.

## Workspace Files

- `REMEDIATION_RUNBOOK.md`: operator-facing audit procedure, gates, and resume rules
- `CONSOLIDATION_RUNBOOK.md`: operator-facing merge/consolidation procedure, gates, and resume rules
- `PROGRESS.md`: live inventory and checkpoint ledger
- `DIDACTIC_AUDIT.md`: experiment-by-experiment physics and teaching review
- `PHYSICS_ASTRONOMY_AUDIT.md`: read-only re-audit focused on formulas, physics, and astronomy correctness

Related companion outside the audit workspace:

- [ASTRONOMY_EXPERIMENTS_COMPANION.md](../../ASTRONOMY_EXPERIMENTS_COMPANION.md):
  teacher/operator companion for astronomy experiment method, physics basis,
  didactic goal, and scope limits

## Operating Rule

- Read the runbook first.
- Update the progress ledger before and after each batch.
- Do not mark a checkpoint complete until the matching tests or probes pass.
- Keep the astronomy subtree separate from the earlier classroom-sensor audit
  unless the scope is explicitly widened again.
