# phyphox BLE Sense Firmware

The sketch in this directory provides the BLE peripheral used by the seven
generated core experiments in `experiments/`.

## Hardware target

The firmware supports the original Arduino Nano 33 BLE Sense with these
sensors:

- LSM9DS1 inertial and magnetic sensor
- HTS221 temperature and humidity sensor
- LPS22HB pressure sensor
- APDS9960 light and color sensor

Nano 33 BLE Sense Rev2 uses different sensor libraries and is not supported.

## BLE service

| Field | Value |
| --- | --- |
| Device and local name | `phyphox-sense` |
| Service | `cddf0001-30f7-4671-8b43-5e40ba53514a` |
| Data characteristic | `cddf1002-30f7-4671-8b43-5e40ba53514a` |
| Config characteristic | `cddf1003-30f7-4671-8b43-5e40ba53514a` |

The data characteristic is notify-only with a 20-byte value. The config
characteristic is readable and writable with a four-byte value.

The supported topology is one powered board within discovery range at a time.
Multi-board discovery is not supported: all boards use the same name and UUIDs,
and the protocol does not expose a unique device identifier for selecting among
nearby boards.

## Data packet

Each notification contains five little-endian `float32` values:

| Offset | phyphox channel | Value |
| --- | --- | --- |
| 0 | CH1 | seconds since firmware start |
| 4 | CH2 | first mode value |
| 8 | CH3 | second mode value |
| 12 | CH4 | third mode value |
| 16 | CH5 | fourth mode value |

CH0 is phyphox-managed packet time configured by the experiment's
`extra="time"` mapping. It is not part of the notification.

## Modes

The app writes a little-endian `float32` to the config characteristic. Finite
values from 0.5 inclusive to 9.5 exclusive are rounded to the nearest integer.

| Mode | Values |
| --- | --- |
| 1 | acceleration x, y, z, magnitude |
| 2 | angular velocity x, y, z, magnitude |
| 3 | magnetic field x, y, z, magnitude |
| 4 | pressure in kPa, followed by three `NaN` values |
| 5 | temperature in degrees Celsius, relative humidity, two `NaN` values |
| 6 | clear, red, green, blue APDS9960 counts |
| 7, 8 | reserved and ignored |
| 9 | raw A0, A1, A2 ADC readings, followed by `NaN` |

Invalid, non-finite, reserved, or incorrectly sized writes leave the active
mode unchanged. After a write attempt, the characteristic contains the
normalized active integer mode. The initial mode is 1.

## Runtime behavior

The loop polls BLE continuously. While a central is connected, it sends a
notification no more frequently than every 50 ms and reads only the active
mode's inputs.

Sensor initialization results are stored during setup. If a required sensor did
not initialize or has no fresh sample, its output channels remain `NaN`.
Analog mode reads A0, A1, and A2 for every sample.

Device time is derived from unsigned `millis()` subtraction. The transmitted
float time restarts after the approximately 49-day `millis()` wrap.

If `BLE.begin()` fails, the sketch enters an infinite delay loop without a
serial message or LED code.

## Compile and upload

From the repository root:

```sh
make compile
```

The compile script installs the pinned board core and libraries, then compiles
the sketch. It does not upload or test a connected board.

To upload:

```sh
arduino-cli board list
arduino-cli upload -p <serial-port> \
  --fqbn arduino:mbed_nano:nano33ble \
  arduino/phyphox_ble_sense
```

The upload path requires physical hardware and is not covered by automated
tests.
