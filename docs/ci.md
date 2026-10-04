# Continuous integration

`.github/workflows/ci.yml` runs on every push, pull request, and manual dispatch.
It asks for read-only repository permissions and cancels superseded runs on the
same ref, so a branch that is pushed twice only tests once.

## XML and Python

The first job installs Python 3.11, the `test` extra, `xmllint`, ShellCheck, and `ripgrep`, then runs:

```sh
make lint
make validate
make check-generated
```

Validation covers the protocol catalog, source inventory, XInclude safety, core
XML, the expanded core experiments, the committed generated artifacts, and the
astronomy XML and locales.

`make check-generated` rebuilds in a temporary directory and compares bytes. CI
never runs `make build`, so a job can fail on drift but can never rewrite a
tracked artifact.

## Firmware

The Arduino job downloads Arduino CLI 1.4.1 and verifies the SHA-256 of the
pinned Linux archive before unpacking it. It sets up Python 3.11 for the
repository tooling, restores the Arduino package cache, runs `make provision` to
install the Nano core and the sensor libraries pinned in
`arduino/toolchain.json`, then runs `make compile` to verify the
installed versions and build for `arduino:mbed_nano:nano33ble` without
refreshing indexes or installing anything new.

This job never uploads firmware or runs it on a physical board, and the
package-index, core, and library downloads remain a separate trust boundary from
the checksum-verified CLI archive.

## Security

The security job installs `ripgrep`, then runs `make security`. That gate
searches tracked and untracked files for a narrow set of credential patterns in
bounded batches. A scanner that cannot run fails the gate; when it does find something, the report carries filenames and line numbers
but never the matched credential contents.

These are repository guardrails. They do not replace supply-chain review,
firmware review, hardware or electrical testing, or content-provenance review.

## Preview deployment

`.github/workflows/pages.yml` publishes the static preview in `demo/` to GitHub
Pages. It triggers on pushes to `main` that touch `demo/` or the workflow
itself, and it can also be started by hand.

This workflow needs a one-time repository setup: under **Settings → Pages**, set
**Source** to **GitHub Actions**. Once that is done, the preview is served at
`https://<owner>.github.io/curious-signals-phyphox/`. The job uploads the `demo/`
directory as a Pages artifact, so the published site contains only the preview
and nothing else from the repository.

## Running the same checks locally

```sh
make ci
```

The full local target does not rewrite your checkout, but it does include the
network-backed provisioning step and may update user-level Arduino CLI state. If
you already have the pinned packages installed and just want a build, use
`make compile` instead.
