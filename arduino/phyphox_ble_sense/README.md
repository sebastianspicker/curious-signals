# phyphox BLE sense sketch

This sketch implements the canonical Bluetooth LE peripheral for the classroom kit and is compatible with the generated files in `experiments/`.

## BLE UUIDs

- Service: `cddf0001-30f7-4671-8b43-5e40ba53514a`
- Data characteristic (notify, 20 bytes): `cddf1002-30f7-4671-8b43-5e40ba53514a`
- Config characteristic (read/write, float32 LE): `cddf1003-30f7-4671-8b43-5e40ba53514a`

The same UUIDs are documented in `experiments/phyphox_constants.json` and validated against the phyphox experiments.

## Data layout

The data characteristic payload is 5x `float32` little-endian:

- **CH0** (phyphox): phyphox-managed packet time from `extra="time"`; it is not read from the BLE payload.
- **CH1**: device time `t` in seconds since boot (first float, offset 0).
- **CH2..CH5**: mode-dependent values.

## Mode mapping

The app writes a float value to the config characteristic. Rounded to the nearest int:

- `1` acceleration: `x,y,z,|a|`
- `2` gyroscope: `x,y,z,|ω|`
- `3` magnetometer: `x,y,z,|B|`
- `4` pressure: `kPa` (converted to `hPa` in the phyphox experiment)
- `5` temperature/humidity: `°C,%rH`
- `6` light/rgb: clear-channel plus `R,G,B` counts from `Arduino_APDS9960`
- `7`, `8` reserved for future experiments (e.g. combined IMU or other sensors); when received, the sketch silently stays on the last valid mode
- `9` analog inputs: `A0,A1,A2` raw ADC readings (converted to mV in the phyphox experiment)

This single mode-switched sketch is the canonical firmware strategy after the repo consolidation.

## Behaviour on failure

If `BLE.begin()` fails in `setup()`, the sketch blocks in an infinite loop with no LED or Serial output. Ensure the board supports BLE and that no other sketch is holding the radio; power-cycle and re-flash if the device does not advertise.

If a selected sensor is unavailable or has no fresh sample, the corresponding active channels are sent as `NaN` so phyphox can distinguish missing data from a real zero.
