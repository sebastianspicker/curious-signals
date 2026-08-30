# Curious Signals

Curious Signals is a classroom kit for collecting sensor data from an original
Arduino Nano 33 BLE Sense in the phyphox mobile app. The repository also
contains a separate set of astronomy classroom experiments and a deterministic
static preview.

## What is included

### Arduino and phyphox kit

The firmware advertises as `phyphox-sense`. A phyphox experiment selects one
sensor mode and receives five little-endian `float32` values per BLE
notification: device time followed by four mode-dependent channels.

| Mode | Experiment | Measurement |
| --- | --- | --- |
| 1 | `accelerometer_plot_v1-2.phyphox` | x, y, z, magnitude |
| 2 | `gyroscope_plot_v1-2.phyphox` | x, y, z, magnitude |
| 3 | `magnetometer_plot_v1-2.phyphox` | x, y, z, magnitude |
| 4 | `pressure_plot_v1-2.phyphox` | pressure |
| 5 | `temperature_plot_v1-2.phyphox` | temperature, humidity |
| 6 | `light_plot_v1-2.phyphox` | clear, red, green, blue |
| 9 | `analog_input_plot_v1-2.phyphox` | A0, A1, A2 |

The importable files are the seven root files in `experiments/`. Their editable
sources are in `src/phyphox/`. The firmware is in
`arduino/phyphox_ble_sense/` and supports the original Nano 33 BLE Sense with
LSM9DS1, HTS221, LPS22HB, and APDS9960 sensors. Rev2 is not supported.

### Astronomy collection

Eight hand-edited files under `experiments/astronomy/` cover reflected light,
comparative warming, thermal response to distance, pressure, pressure and
temperature trends, tidal locking, and transit light curves. They use phone
sensors, TI SensorTags, a Bluetooth HID input, or supported Owon multimeters.
They do not use the Arduino firmware.

See the [astronomy companion](docs/ASTRONOMY_EXPERIMENTS_COMPANION.md) for each
activity's measurement path and interpretation limits.

### Static preview

`demo/` renders deterministic sample traces shaped like the core modes. It does
not use Bluetooth, sensors, storage, or network data and is not evidence of
hardware behavior.

## Use the kit

1. Open `arduino/phyphox_ble_sense/phyphox_ble_sense.ino` in the Arduino IDE.
2. Select the original Arduino Nano 33 BLE Sense and upload the sketch.
3. Transfer one root `experiments/*.phyphox` file to a phone or tablet.
4. Open it in phyphox and start the experiment.

For command-line compilation:

```sh
make compile
arduino-cli upload -p /dev/ttyACM0 \
  --fqbn arduino:mbed_nano:nano33ble arduino/phyphox_ble_sense
```

The compile target installs pinned Arduino packages and compiles but does not
upload or test a connected board.

## Development setup

Requirements:

- Python 3.11 or newer
- `xmllint`
- `arduino-cli` for firmware compilation
- `ripgrep` for the local security check
- `zip` or `unzip` only when inspecting bundles outside the build tooling

Install the Python package and development tools:

```sh
python3 -m pip install -e '.[test]'
```

Use Make as the command interface:

```sh
make lint             # Ruff lint and format checks
make test             # behavior-focused pytest suite
make validate         # protocol, XML, core, and astronomy validation
make check-generated  # non-mutating byte parity check
make build            # update the seven tracked generated files
make compile          # pinned firmware compile, no upload
make security         # secret, pin, shell, and Python sanity checks
make ci               # full checkout-non-mutating local gate
make bundle           # deterministic core experiment ZIP
```

The full gate includes the network-backed firmware compile. Hosted CI runs the
same concerns in separate jobs.

To build into a temporary directory without changing tracked artifacts:

```sh
PYTHONPATH=src python3 -m curious_signals build --output /tmp/phyphox-output
```

The Python module is an internal tooling interface. Contributor documentation
and automation should use Make.

## Source and generated files

Edit `src/phyphox/*.phyphox.xml` and shared fragments under
`src/phyphox/includes/`, then run:

```sh
make build
make check-generated
make validate
```

Do not hand-edit matching root `experiments/*.phyphox` files. Astronomy files
are maintained directly and never pass through the core generator.

`protocol/contract.json` is the normative shared contract for the device name,
UUIDs, frame encoding, mode selection, channel meanings, and distributable
filenames. Firmware and XML remain concrete implementations; validation checks
that they conform.

## BLE contract and limitations

- Device and local name: `phyphox-sense`.
- Data characteristic: notify-only, 20 bytes, five little-endian `float32`
  values.
- Config characteristic: readable/writable, one little-endian `float32` mode.
- Minimum notification interval: 50 ms.
- Modes 7 and 8 are reserved.
- Unavailable sensor channels are sent as `NaN`.
- Every board uses the same name and UUIDs, so multi-board discovery is not
  supported.
- BLE initialization failure stops the sketch; no detailed status
  characteristic, serial diagnostic, or LED error protocol exists.

Automated checks do not verify physical sensors, BLE radio behavior, analog
electrical behavior, calibration, phyphox mobile import/rendering, content
rights, or classroom safety.

## Repository map

| Path | Responsibility |
| --- | --- |
| `protocol/contract.json` | Normative cross-component protocol and mode data |
| `arduino/phyphox_ble_sense/` | Firmware and hardware notes |
| `src/phyphox/` | Editable core experiment sources |
| `experiments/*.phyphox` | Generated importable core artifacts |
| `experiments/astronomy/` | Hand-edited astronomy collection |
| `demo/` | Deterministic static preview |
| `src/curious_signals/` | Internal build and validation package |
| `tests/` | Observable behavior and contract checks |
| `scripts/` | Firmware compile and shell-native security checks |

The dependency rules and rationale are in
[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md). Contributor workflows are in
[CONTRIBUTING.md](CONTRIBUTING.md), and hosted checks are documented in
[docs/ci.md](docs/ci.md).

## License and attribution

See [LICENSE](LICENSE) for the repository license. Component provenance and
distribution rights are not yet fully reconciled; do not infer release
readiness from the presence of a root license. Core phyphox attribution notes
are in [src/phyphox/README.md](src/phyphox/README.md).
