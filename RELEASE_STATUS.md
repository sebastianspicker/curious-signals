# Release Status

Updated: 2026-07-24  
Status: not ready for public alpha publication

No public release has been published.

## Maintained scope

- Firmware targets the original Arduino Nano 33 BLE Sense using the pinned
  `arduino:mbed_nano@4.5.0` core and sensor libraries.
- Seven core experiments are generated from `src/phyphox/*.phyphox.xml` and
  committed as importable files under `experiments/`.
- Eight astronomy experiments are maintained separately under
  `experiments/astronomy/`; they use phone sensors, TI SensorTags, a Bluetooth
  HID mouse, or Owon multimeter decoder paths rather than the Arduino firmware.

## Local verification

On 2026-07-24, `make ci-local` passed against the local uncommitted working
tree based on commit `212c254e45f23ab356f5cf01df676048f2c98a24`. The run
reported:

- Ruff lint and format checks
- 141 Python tests
- XML parsing, XInclude boundary checks, and phyphox contract validation
- byte-for-byte generated experiment parity
- the pinned Arduino compile for `arduino:mbed_nano:nano33ble`
- the secret, dependency, shell syntax, ShellCheck, and Python syntax checks

The compiled sketch uses 339784 bytes of program storage and 71304 bytes of
dynamic memory.

These checks do not verify physical sensors, BLE radio behavior, analog
electrical behavior, or operation in the phyphox mobile application.

## Publication blockers

- The root license, component license declarations, astronomy content
  authorship, and embedded image provenance have not been reconciled.
- The original supported board still requires owner-run BLE, sensor,
  analog-input, electrical, and phyphox application tests.
- The release candidate must be reconciled with upstream history before a
  release commit or tag is selected.
- A reliable private vulnerability reporting path must be confirmed.

## Follow-up decisions

- Decide whether the Arduino CLI download requires checksum verification.
- Decide whether Python test dependencies require a hash-locked environment.
- Decide whether multi-board classroom use requires a unique advertised device
  identifier.
