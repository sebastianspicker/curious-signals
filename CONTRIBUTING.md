# Contributing

Thanks for looking. This is a small set of teaching artifacts, so the most
useful contributions tend to be corrections, clearer explanations, or a
genuinely missing capability rather than broad rewrites.

Read [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) before you change a boundary
between components. It explains why the firmware, the experiment files, the
preview, and the tooling are kept apart, and which of them may depend on which.

## Set up a working environment

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[test,browser]'
python -m playwright install chromium
```

Run the narrower checks while you work and the full gate before you open a pull
request:

```sh
make lint
make test
make test-browser
make validate
make check-generated
make security
```

## Changing a core experiment

Core experiments are generated. Edit the sources in `src/phyphox/`, plus any
shared fragments under `src/phyphox/includes/`, then rebuild and check parity:

```sh
make build
make check-generated
make validate
git diff -- src/phyphox experiments
```

`make check-generated` has to pass once you are happy with the generated diff.
Never edit a root `experiments/*.phyphox` file directly; the next `make build`
would overwrite it.

## Changing an astronomy experiment

Files in `experiments/astronomy/` are hand-maintained and never pass through the
Arduino generator. Keep English as the root locale and keep the German and
French translations. Preserve the activity's real input path — phone sensor,
SensorTag, HID input, or Owon multimeter — and do not reroute it through
`phyphox-sense`.

`owon_digital_multimeter-debug.phyphox` is an intentional integration helper.
Its name does not make it disposable build output.

```sh
python3 -m pytest tests/experiments/test_astronomy.py
make validate
```

If you change an activity's input path, model, or scope limit, update its note
in [docs/ASTRONOMY_EXPERIMENTS_COMPANION.md](docs/ASTRONOMY_EXPERIMENTS_COMPANION.md)
in the same change.

## Changing the firmware or the protocol

`protocol/contract.json` owns the shared device name, UUIDs, frame layout,
timing, mode numbers, channel meanings, and filenames. When you change a fact
there, update every concrete implementation that depends on it, including the
preview fixtures. The sketch keeps its own literals so it stays a single file;
`tests/firmware/` runs it on the host and fails if any of them disagree with the
contract.

```sh
python3 -m pytest tests/protocol tests/firmware
make validate
make check-generated
make compile
```

`make compile` builds the sketch but never uploads it or tests a connected
board. Report BLE, sensor, electrical, and phyphox-app verification separately
from anything CI can check.

## Changing build, validation, or CI

Keep `make` as the contributor-facing interface and treat
`src/curious_signals/` as an internal implementation detail. CI and validation
must never rewrite tracked artifacts.

```sh
make lint
make test
make validate
make check-generated
make security
```

`make test` compiles the real sketch against controlled BLE, clock, ADC, and
sensor doubles, so it needs a C++17 compiler. The preview fixtures are evaluated
by Node.js 22+. The scientific fixtures check scalar values for the XML formulas
given known inputs; they do not emulate phyphox's buffer scheduling and they do
not establish sensor calibration.

`make test-browser` runs desktop and mobile Chromium checks for interaction,
contrast, reduced motion, and the preview's network, storage, and sensor
boundaries. It fails when Playwright or Chromium is missing, and it is separate
from `make test` but included in `make ci`.

`make provision` installs the versions recorded in
`arduino/toolchain.json` and is the only step that needs the network.
`make compile` verifies those installed versions and builds without refreshing
indexes or installing packages. `make ci` provisions and therefore needs network
access.

## Refreshing the README screenshots

The images in the README come from the preview, not from a phone. Regenerate
them after a visual change:

```sh
PREVIEW_SCREENSHOT_DIR=docs/images make test-browser
```

That writes the desktop and mobile shots plus one chart image per mode.

## Pull requests

Please include:

- what behavior or contract changed;
- which source and generated files are affected;
- the commands you ran and their exact outcomes;
- which hardware or mobile-app checks you did, and which you skipped;
- the compatibility impact;
- anything still uncertain about release or provenance.

Leave generated archives, local environments, caches, analysis state, and
credentials out of the diff.
