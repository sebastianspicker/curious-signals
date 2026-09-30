# Astronomy Experiments Companion

The eight files in `experiments/astronomy/` are independent of the Arduino
`phyphox-sense` kit. They read from phone sensors, TI SensorTags, a Bluetooth HID
mouse, or an Owon multimeter. Treat every one of them as a classroom model or
analogy rather than a calibrated astronomical instrument.

All of them use English as the root locale and include German and French
translations; phyphox falls back to the English text on any other device
language.

A few things the files themselves do not settle:

- They do not say which TI SensorTag generation they expect.
- The Owon decoder branches are labeled for B35T and W18B models, but those
  labels are not a statement that the current hardware still matches.
- Pairing, wiring, and live device behavior still need to be checked against the
  equipment you actually have in the room.

## The activities

### `albedo.phyphox`

Compares reflected light from a phone or SensorTag light sensor under fixed
geometry. Its contrast value is a relative reflectance proxy derived from the
maximum and minimum signal in a single run. That is enough to compare surfaces
in a controlled setup; it is not a calibrated planetary albedo.

### `greenhouse.phyphox`

Records temperature from one or two SensorTags so that enclosed setups can be
compared under the same illumination. The interesting result is the difference
between the warming curves and their extrema. It does not model a complete
atmosphere or a planetary climate.

### `ir-dist_habitable.phyphox`

Plots SensorTag infrared and ambient temperature against mouse displacement.
Because mouse displacement is only an uncalibrated distance proxy, the activity
supports a qualitative discussion of distance and heating. It does not compute
habitable-zone boundaries or test an inverse-square law quantitatively.

### `missiontomars.phyphox`

Uses a phone or SensorTag pressure sensor to record ambient pressure in `hPa`
and report its minimum, maximum, mean, and range. The spaceflight framing is a
way into cabin pressure, leakage, and stability. It is not a measurement of the
Martian atmosphere.

### `owon_digital_multimeter-debug.phyphox`

Exposes raw values and decoder helper channels for the Owon B35T and W18B paths.
It supports the multimeter input used by the transit activity and is kept as an
integration utility. It is not a stand-alone teaching experiment, and its model
labels are not evidence of current hardware compatibility.

### `pt-star.phyphox`

Records SensorTag pressure and temperature and asks learners to compare the two
trends. It is an analogy for reasoning about coupled physical quantities in
star-formation discussions, not a simulation of stellar collapse.

### `tidal-locking.phyphox`

Uses two SensorTags to compare temperature, infrared temperature, ambient
temperature, and illuminance on differently lit sides of a model. It shows
persistent spatial asymmetry; it does not represent the climate of a tidally
locked planet.

### `transitmethode.phyphox`

Accepts a relative light signal from a phone, a SensorTag, or a solar cell wired
through an Owon decoder path. Timing logic identifies model transits and derives
their duration and period. The simple radius estimate assumes transit depth is
proportional to `(R_planet / R_star)^2`, so it depends on a star radius the user
supplies. The result demonstrates transit reasoning, not real exoplanet
discovery precision.

## Teaching and maintenance

Introduce each activity in this order: the measured quantity, the model
interpretation, and the claim the setup cannot support. That keeps direct
observations separate from inferred or analogical conclusions.

When you change a file here, update its note above if the input path, the model,
or the scope limit moved, then run:

```sh
python3 -m pytest tests/experiments/test_astronomy.py
make validate
```
