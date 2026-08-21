# Astronomy Experiments Companion

The eight files in `experiments/astronomy/` are separate from the Arduino
`phyphox-sense` path. They use phone sensors, TI SensorTags, a Bluetooth HID
mouse, or an Owon multimeter. This document records the measurement method,
physical model, teaching purpose, and interpretation limits of each file.

The files do not identify a specific TI SensorTag generation. Owon decoder
branches are labeled for B35T and W18B models. Those labels describe the
implemented parsing paths, not current hardware-test evidence. Pairing,
electrical setup, and live device compatibility still require maintainer
verification.

## Localization

All astronomy `.phyphox` files currently use:

- English as the root phyphox locale
- German translation support
- French translation support

If the phone language is not `en`, `de`, or `fr`, phyphox falls back to the
English root strings.

## Experiment map

| File | Primary measurement path | Classroom topic | Didactic status |
| --- | --- | --- | --- |
| `albedo.phyphox` | phone light sensor or TI SensorTag light sensor | reflected light and relative reflectance | bounded qualitative analogue |
| `greenhouse.phyphox` | one or two TI SensorTags | comparative warming in enclosed gas setups | bounded comparative analogue |
| `ir-dist_habitable.phyphox` | TI SensorTag IR + ambient temperature and uncalibrated mouse distance | distance, heating, and qualitative habitable-zone discussion | qualitative only |
| `missiontomars.phyphox` | phone pressure sensor or TI SensorTag pressure sensor | cabin atmosphere and pressure safety analogy | bounded pressure analogue |
| `owon_digital_multimeter-debug.phyphox` | Owon B35T or W18B decoder path | measurement helper for hardware integration | not a teaching experiment |
| `pt-star.phyphox` | TI SensorTag pressure and temperature | analogy for coupled physical trends in star-formation discussions | bounded analogy with explicit scaffolding |
| `tidal-locking.phyphox` | two TI SensorTags | day-side versus night-side comparison | bounded comparative analogue |
| `transitmethode.phyphox` | phone light sensor, TI SensorTag, or solar cell on an Owon B35T or W18B decoder path | transit light curves and derived orbital quantities | bounded model experiment |

## Experiment notes

### `albedo.phyphox`

#### Method — `albedo.phyphox`

- Measures reflected light under fixed geometry.
- Supports either the phone light sensor or the TI SensorTag light sensor.
- Reports a relative reflected-light level and a reflectance proxy.

#### Physics basis — `albedo.phyphox`

- The encoded proxy is the fractional contrast between the maximum and minimum
  reflected signal within one run.
- Comparing different surfaces therefore requires separate runs under matched
  geometry.
- This is not a calibrated albedo measurement.
- The output depends on geometry, source intensity, surface orientation, and
  sensor response.

#### Didactic goal — `albedo.phyphox`

- Introduce the idea that brighter reflected signals can stand in for higher
  reflectivity.
- Support classroom discussion of why real astronomical albedo work requires
  calibration, geometry control, and model assumptions.

#### Scope limits — `albedo.phyphox`

- Safe claim: relative comparison between surfaces in one setup.
- Unsafe claim: direct planetary albedo determination.

### `greenhouse.phyphox`

#### Method — `greenhouse.phyphox`

- Uses one or two TI SensorTags to record temperature over time.
- Supports either a single setup or a direct comparison of two enclosed gas
  setups under the same illumination.

#### Physics basis — `greenhouse.phyphox`

- Encodes temperature logging only.
- The meaningful variable is the comparative temperature trend between setups,
  not an absolute climate model.

#### Didactic goal — `greenhouse.phyphox`

- Teach controlled comparison:
  - same illumination
  - different enclosure or gas condition
  - compare warming curves and extrema

#### Scope limits — `greenhouse.phyphox`

- Safe claim: relative warming comparison in a classroom model.
- Unsafe claim: complete atmospheric or planetary greenhouse modelling.

### `ir-dist_habitable.phyphox`

#### Method — `ir-dist_habitable.phyphox`

- Uses TI SensorTag IR and ambient temperature channels.
- Uses mouse displacement as an uncalibrated distance proxy.
- Plots IR temperature signal and ambient temperature against that uncalibrated
  distance.

#### Physics basis — `ir-dist_habitable.phyphox`

- The file is intentionally qualitative.
- It supports discussion of how changing distance affects a heating-related
  signal.
- It does not encode a physically calibrated habitable-zone law.

#### Didactic goal — `ir-dist_habitable.phyphox`

- Show that “closer” and “farther” can be discussed through changing thermal
  response without pretending the setup is an astronomical calculator.
- Make students separate:
  - signal trend
  - ambient condition
  - true astrophysical interpretation

#### Scope limits — `ir-dist_habitable.phyphox`

- Safe claim: qualitative distance-versus-heating discussion.
- Unsafe claim: quantitative habitable-zone boundaries or inverse-square-law
  validation from this file alone.

### `missiontomars.phyphox`

#### Method — `missiontomars.phyphox`

- Uses either the phone pressure sensor or the TI SensorTag pressure sensor.
- Records air pressure over time and reports maximum, minimum, mean, and
  pressure range.

#### Physics basis — `missiontomars.phyphox`

- The encoded quantity is ambient air pressure in `hPa`.
- The lesson is framed as spaceship atmosphere or cabin safety, not direct Mars
  atmosphere measurement.

#### Didactic goal — `missiontomars.phyphox`

- Use a spaceflight narrative to motivate pressure measurement and safety
  thresholds.
- Let students reason about stability, leakage, pressure loss, and reference
  values in a bounded analogue.

#### Scope limits — `missiontomars.phyphox`

- Safe claim: cabin-pressure or prototype-atmosphere analogy.
- Unsafe claim: direct Mars environmental measurement.

### `owon_digital_multimeter-debug.phyphox`

#### Method — `owon_digital_multimeter-debug.phyphox`

- Contains decoder paths labeled for Owon B35T and W18B digital multimeters.
- Exposes raw values and helper channels for debugging.

#### Physics basis — `owon_digital_multimeter-debug.phyphox`

- No astronomy model is encoded here.
- This is an instrumentation helper for the multimeter-supported transit path.

#### Didactic goal — `owon_digital_multimeter-debug.phyphox`

- None as a stand-alone classroom astronomy experiment.

#### Scope limits — `owon_digital_multimeter-debug.phyphox`

- Treat as a debug and integration utility only.
- Do not treat the model labels as current hardware compatibility evidence.

### `pt-star.phyphox`

#### Method — `pt-star.phyphox`

- Uses TI SensorTag pressure and temperature channels.
- Logs both quantities over time.
- Includes in-file questions that ask learners to compare how both quantities
  change together.

#### Physics basis — `pt-star.phyphox`

- The encoded file measures only pressure and temperature.
- The astronomy connection is analogical, not a star-formation simulation.

#### Didactic goal — `pt-star.phyphox`

- Train students to think about coupled variables and trends.
- Use the analogy to discuss why astrophysical stories often involve linked
  physical quantities without pretending the classroom setup reproduces stellar
  collapse.

#### Scope limits — `pt-star.phyphox`

- Safe claim: structured analogy for comparison and discussion.
- Unsafe claim: direct model of star formation.

### `tidal-locking.phyphox`

#### Method — `tidal-locking.phyphox`

- Uses two TI SensorTags.
- Compares temperature, IR temperature, ambient temperature, and illuminance
  across differently illuminated model sides.

#### Physics basis — `tidal-locking.phyphox`

- Encodes side-by-side sensor comparison.
- The relevant physical idea is persistent asymmetry between differently
  illuminated sides.

#### Didactic goal — `tidal-locking.phyphox`

- Support discussion of day-side versus night-side differences in a
  tidally-locked framing.
- Emphasize comparison across two simultaneously measured model conditions.

#### Scope limits — `tidal-locking.phyphox`

- Safe claim: comparative analogue for persistent illuminated versus shaded
  sides.
- Unsafe claim: full climate model of a tidally locked exoplanet.

### `transitmethode.phyphox`

#### Method — `transitmethode.phyphox`

- Supports three measurement paths:
  - phone light sensor
  - TI SensorTag light sensor
  - solar cell on an Owon B35T or W18B decoder path
- Treats all three as a relative signal over time.
- Uses phyphox timing logic to identify transits and derive duration and period.

#### Physics basis — `transitmethode.phyphox`

- The core observable is a relative light-curve dip.
- In the simple model used here, transit depth scales like
  `(R_planet / R_star)^2`.
- The inferred planet radius therefore depends on the measured dip and on a
  user-provided star radius.
- The displayed relative planet size is a radius ratio, not an area ratio or a
  volume ratio.
- This is a model experiment that encodes the logic of transit reasoning, not a
  telescope pipeline.

#### Didactic goal — `transitmethode.phyphox`

- Show how a dimming event can imply:
  - transit depth
  - transit duration
  - orbital period
  - estimated planet radius in a model system
- Help students distinguish measured quantities from inferred quantities.

#### Scope limits — `transitmethode.phyphox`

- Safe claim: transit-light-curve logic in a classroom model.
- Unsafe claim: real exoplanet discovery precision or physically calibrated
  stellar and planetary parameters from this setup alone.

## Teaching use

Use this order when introducing an experiment:

1. observable quantity
2. model interpretation
3. scope limit

For example:

- `What do we measure?`
- `What can this stand in for?`
- `What does this experiment not prove on its own?`

The files present:

- visible quantity first
- astronomy interpretation second
- explicit limit or analogue boundary third

## Suggested pairings

- `albedo.phyphox` + `transitmethode.phyphox`
  - reflected light versus transmitted/blocked light
- `greenhouse.phyphox` + `ir-dist_habitable.phyphox`
  - comparative warming versus qualitative distance-heating discussion
- `missiontomars.phyphox` + `pt-star.phyphox`
  - careful use of analogy in two different physical contexts
- `tidal-locking.phyphox` + `ir-dist_habitable.phyphox`
  - spatial asymmetry versus distance-dependent thermal trends

## Maintenance

If any astronomy file changes:

1. Update the corresponding section if the measurement, model, or scope limit
   changed.
2. Run the astronomy contract tests documented in
   [the development runbook](RUNBOOK.md).
3. Run `bash scripts/validate-xml.sh`.
