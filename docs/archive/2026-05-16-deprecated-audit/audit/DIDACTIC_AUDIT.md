# Didactic Astronomy Audit: Closure Re-Check

Scope:

- `experiments/astronomy/*.phyphox`
- the optional local phyphox wiki core in `reference/phyphox-wiki-core/` when
  present

Method:

- read the current experiment XML directly
- compare the encoded measurement path and outputs with the stated classroom story
- focus on the learner-facing contract: title, description, views, labels, and exports
- verify the remediations with `tests/test_astronomy_audit.py`

## Remediations Applied

1. `pt-star.phyphox`

- renamed the main view to `Analogy Comparison`
- added in-file `info` blocks that explain the analogy boundary and the intended comparison question

2. `missiontomars.phyphox`

- changed the root title from `Die Reise zum Mars` to `Raumschiffatmosphäre prüfen`
- changed the English title from `Mission to Mars` to `Checking a Spaceship Atmosphere`

3. `ir-dist_habitable.phyphox`

- renamed the file title toward `IR Temperature Signal and Distance`
- aligned the description, view labels, graph labels, and help text around `IR temperature signal` and `ambient temperature`
- kept the radiation framing only as explanatory context

4. `tidal-locking.phyphox`

- replaced the learner-facing `2in1` labels with `Combined comparison`

5. `transitmethode.phyphox`

- fixed the visible `Dritter Transit` typo
- fixed the `näherungsweise` typo in both the learner-facing text and the translation string contract

6. `greenhouse.phyphox`

- changed the export columns from duplicate `Temperature (°C)` labels to `Temperature 1 (°C)` and `Temperature 2 (°C)`

## Per-Experiment Verdict

| File | Physics/method | Didactics | Verdict |
| --- | --- | --- | --- |
| `albedo.phyphox` | bounded and consistent | clear | green |
| `greenhouse.phyphox` | bounded and consistent | clear | green |
| `ir-dist_habitable.phyphox` | qualitative only and bounded | clear and consistently framed as qualitative | green |
| `missiontomars.phyphox` | bounded and consistent | clear cabin-pressure framing | green |
| `owon_digital_multimeter-debug.phyphox` | helper/debug only | not a teaching file | n/a |
| `pt-star.phyphox` | bounded analogy only | now scaffolded sufficiently in-file | green |
| `tidal-locking.phyphox` | bounded and consistent | clear comparison wording | green |
| `transitmethode.phyphox` | bounded and consistent | clear, no known visible wording defects | green |

## Residual Note

- This closure means the remaining learner-facing issues from the prior didactic re-check were resolved.
- It does not claim that every experiment is pedagogically optimal for every classroom without external worksheets.
- If the astronomy subtree changes again, rerun the targeted audit tests and then refresh this note.

## Overall Verdict

- The astronomy subtree is currently consistent with its encoded classroom methods and bounded physical claims.
- The previously open didactic wording, framing, scaffolding, and export-clarity issues have been remediated.
