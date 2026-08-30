# Astronomy Experiments Companion

The eight files in `experiments/astronomy/` are independent of the Arduino
`phyphox-sense` kit. They use phone sensors, TI SensorTags, a Bluetooth HID
mouse, or an Owon multimeter. Each activity is a classroom model or analogy,
not a calibrated astronomical instrument.

All files use English as the root locale and include German and French
translations. phyphox falls back to the English text for other device
languages.

The files do not identify a TI SensorTag generation. Owon decoder branches are
labeled for B35T and W18B models, but those labels do not establish current
hardware compatibility. Pairing, electrical setup, and live device behavior
still require verification with the equipment in use.

## Experiment guide

### `albedo.phyphox`

Uses a phone or SensorTag light sensor to compare reflected light under fixed
geometry. Its contrast value is a relative reflectance proxy based on the
maximum and minimum signal in one run. It can compare surfaces in a controlled
setup; it cannot determine calibrated planetary albedo.

### `greenhouse.phyphox`

Records temperature from one or two SensorTags for a controlled comparison of
enclosed setups under the same illumination. The useful result is the
difference between warming curves and extrema. The activity does not model a
complete atmosphere or planetary climate.

### `ir-dist_habitable.phyphox`

Plots SensorTag infrared and ambient temperatures against mouse displacement.
Mouse displacement is an uncalibrated distance proxy, so the activity supports
qualitative discussion of distance and heating only. It does not calculate
habitable-zone boundaries or test an inverse-square law quantitatively.

### `missiontomars.phyphox`

Uses a phone or SensorTag pressure sensor to record ambient pressure in `hPa`
and calculate its minimum, maximum, mean, and range. The spaceflight framing
supports discussion of cabin pressure, leakage, and stability; it is not a
measurement of the Martian atmosphere.

### `owon_digital_multimeter-debug.phyphox`

Exposes raw values and decoder helper channels for Owon B35T and W18B paths.
It supports the multimeter input used by the transit activity and is retained
as an integration utility. It is not a stand-alone teaching experiment, and
its model labels are not evidence of current hardware compatibility.

### `pt-star.phyphox`

Records SensorTag pressure and temperature and asks learners to compare their
trends. It is an analogy for reasoning about coupled physical quantities in
star-formation discussions, not a simulation of stellar collapse.

### `tidal-locking.phyphox`

Uses two SensorTags to compare temperature, infrared temperature, ambient
temperature, and illuminance on differently lit sides of a model. It
demonstrates persistent spatial asymmetry; it does not represent the climate of
a tidally locked planet.

### `transitmethode.phyphox`

Accepts relative light signals from a phone, a SensorTag, or a solar cell
connected through an Owon decoder path. Timing logic identifies model transits
and derives their duration and period. The simple radius estimate uses transit
depth proportional to `(R_planet / R_star)^2` and therefore depends on a
user-supplied star radius. The result demonstrates transit reasoning, not real
exoplanet discovery precision.

## Teaching and maintenance

Introduce each activity in this order: the measured quantity, the model
interpretation, and the claim the setup cannot support. This keeps direct
observations separate from inferred or analogical conclusions.

When an astronomy file changes, update its note above if the input path, model,
or scope limit changed. Then run:

```sh
python3 -m pytest tests/test_astronomy_contracts.py
make validate
```
