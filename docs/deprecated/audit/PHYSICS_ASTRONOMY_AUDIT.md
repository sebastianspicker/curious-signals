# Physics and Astronomy Re-Audit: Consolidated State

This note records the post-remediation re-audit of the consolidated astronomy
subtree.

Scope:

- `experiments/astronomy/*.phyphox`
- the optional local phyphox reference in `reference/phyphox-wiki-core/` when
  present

Method:

- inspect the actual `analysis` blocks, inputs, views, and exports
- confirm that astronomy claims are bounded to what the formulas really encode
- confirm that the merged files still parse and satisfy the local contract tests

## Findings

No open red findings remain in the current consolidated subtree.

## Family Review

| Family | Outcome | Notes |
| --- | --- | --- |
| Relative reflected light | green | compares reflected-light signals under fixed geometry and no longer claims calibrated albedo output |
| Greenhouse effect | green | comparative classroom analogue remains internally consistent |
| Habitable-zone analogue | green | qualitative distance/radiation discussion only; invalid log-Celsius surface removed |
| Mission to Mars | green | pressure math is sound and the astronomy framing is bounded to a cabin-pressure analogue |
| Star-formation analogy | green | sensor math is sound and the title/description no longer imply a direct star-formation model |
| Tidal locking | green | multi-sensor conversions and IR/ambient views remain internally consistent |
| Transit method | green | one shared multisource transit pipeline; radius ratio output is now linear instead of mislabeled cube-law output |
| Debug multimeter | n/a | helper file, not an astronomy lesson |

## Physics Notes

### `albedo.phyphox`

- The file now behaves as a reflected-light comparison experiment.
- It still does not compute calibrated albedo, and it no longer claims to.

### `ir-dist_habitable.phyphox`

- The file remains uncalibrated in distance.
- That is acceptable because the claim is now qualitative and the misleading log-law teaching surface is gone.

### `missiontomars.phyphox`

- Pressure conversion and summary values are correct for the supported phone and SensorTag paths.
- Earth sea-level values are now retained only as familiar reference points for cabin-pressure discussion.

### `pt-star.phyphox`

- The file still logs only pressure and temperature.
- That is acceptable because the claim is explicitly analogical, not a direct astrophysical model.

### `transitmethode.phyphox`

- The downstream transit-depth and radius reconstruction logic is shared across all supported sources.
- The relative-size output is now a linear radius ratio percentage, which matches the UI label.

## Re-Audit Verdict

- The astronomy subtree is physically bounded, astronomy-bounded, and structurally consolidated.
- The remaining risks are normal maintenance risks such as future drift after content edits, not unresolved baseline science defects.
