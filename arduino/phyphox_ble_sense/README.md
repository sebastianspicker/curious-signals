# phyphox BLE Sense firmware

`phyphox_ble_sense.ino` turns an original Arduino Nano 33 BLE Sense into the
Bluetooth peripheral that the seven generated experiments in `experiments/`
expect. Flash it once, and the board advertises as `phyphox-sense`.

## Hardware

The sketch targets the original Nano 33 BLE Sense and its onboard sensors:

- LSM9DS1 — acceleration, angular velocity, and magnetic field
- HTS221 — temperature and humidity
- LPS22HB — pressure
- APDS9960 — light and color

The Rev2 board uses different sensor libraries and is not supported.

## BLE service

| Field | Value |
| --- | --- |
| Device and local name | `phyphox-sense` |
| Service | `cddf0001-30f7-4671-8b43-5e40ba53514a` |
| Data characteristic | `cddf1002-30f7-4671-8b43-5e40ba53514a` |
| Config characteristic | `cddf1003-30f7-4671-8b43-5e40ba53514a` |

The data characteristic is notify-only and its value is 20 bytes. The config
characteristic is readable and writable and its value is four bytes.

One powered board within discovery range at a time is the supported setup.
Multi-board discovery does not work: every board uses the same name and UUIDs,
and the protocol exposes no unique identifier for choosing between them.

## Data packet

Each notification carries five little-endian `float32` values:

| Offset | phyphox channel | Value |
| --- | --- | --- |
| 0 | CH1 | seconds since firmware start |
| 4 | CH2 | first mode value |
| 8 | CH3 | second mode value |
| 12 | CH4 | third mode value |
| 16 | CH5 | fourth mode value |

CH0 is the packet time that phyphox manages through the experiment's
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

Writes that are invalid, non-finite, reserved, or the wrong size leave the
active mode alone. After any write attempt the characteristic holds the
normalized active integer mode. The board starts in mode 1.

## Runtime behavior

The loop polls BLE continuously. While a central is connected it notifies no
more often than every 50 ms, and it reads only the inputs for the active mode.

Sensor initialization results are captured during `setup()`. If a required
sensor did not initialize, or has no fresh sample, its output channels stay
`NaN`. Analog mode reads A0, A1, and A2 for every sample.

Device time comes from unsigned `millis()` subtraction, so the transmitted time
restarts after the roughly 49-day `millis()` wrap.

If `BLE.begin()` fails, the sketch drops into an infinite delay loop with no
serial message and no LED code to tell you why.

## Compile and upload

From the repository root:

```sh
make provision
make compile
```

Provisioning installs the core and libraries pinned in
`scripts/arduino-toolchain.json`. The compile script verifies the installed
versions without installing anything, then builds the sketch. It does not
upload it or test a connected board.

To flash a board:

```sh
arduino-cli board list
arduino-cli upload -p <serial-port> \
  --fqbn arduino:mbed_nano:nano33ble \
  arduino/phyphox_ble_sense
```

Uploading needs physical hardware and is not covered by automated tests.
