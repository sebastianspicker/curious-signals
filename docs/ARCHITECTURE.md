# Architecture

Curious Signals is an artifact repository, not a single runtime application. It
ships two classroom experiment families and the firmware used by one of them.
Repository tooling exists only to keep those artifacts reproducible and
compatible.

## Product boundaries

### Arduino classroom kit

The kit is one protocol implemented by two independently deployed components:

- `arduino/phyphox_ble_sense/` acquires Nano 33 BLE Sense sensor samples and
  exposes them over Bluetooth Low Energy.
- `src/phyphox/` contains the editable phyphox experiment definitions.
- `experiments/*.phyphox` contains the generated files imported by learners.

`protocol/contract.json` owns the facts shared across those components: device
identity, UUIDs, wire encoding, frame fields, timing, modes, channel meanings,
and distributable filenames. Firmware and XML remain concrete, independently
inspectable implementations. Validation enforces their conformance to the
contract.

### Astronomy collection

`experiments/astronomy/` is hand maintained. Its files use phone sensors, TI
SensorTags, a Bluetooth HID input, or Owon multimeters. They do not depend on
the Arduino protocol or pass through the core experiment generator.

### Static preview

`demo/` is a deterministic browser simulation. It demonstrates the shape of
the core modes but performs no Bluetooth, sensor, storage, or network work. It
is not a runtime client or a scientific-data fixture.

## Tooling boundary

`src/curious_signals/` owns repository automation:

- loading and validating the protocol contract;
- checking safe local XInclude references;
- expanding and post-processing core experiment sources;
- validating core and astronomy experiment contracts;
- comparing generated artifacts without mutating the checkout;
- building the core experiment bundle.

The package is an internal implementation boundary. `make` is the documented
contributor interface. Shell remains only for work that is inherently
shell-oriented, such as installing and compiling the pinned Arduino toolchain
and lightweight repository security checks.

## Dependency direction

```text
protocol/contract.json
    |-- firmware conformance
    |-- core experiment conformance
    `-- preview conformance

src/phyphox/ --generate--> experiments/*.phyphox

src/curious_signals/ --> protocol and repository artifacts
tests/               --> public tooling seams and observable artifacts
```

Firmware, astronomy experiments, and the preview never import repository
tooling. Generated core experiments never become source inputs. The astronomy
collection never enters the Arduino generation pipeline.

## Change rules

- Change shared wire or mode facts in `protocol/contract.json`, then update
  every concrete implementation and run conformance checks.
- Edit core experiments in `src/phyphox/`; rebuild rather than hand-editing the
  matching root artifacts.
- Edit astronomy files directly and retain their English root locale plus
  German and French translations.
- Keep validation checkout-non-mutating. `make check-generated` must detect
  drift before `make build` is used to update tracked artifacts.
- Add abstractions only when they protect a real boundary above. The project
  does not need service, plugin, or framework layers.
