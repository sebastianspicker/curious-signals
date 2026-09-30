# Security Policy

## Supported versions

Nothing has been released publicly yet, so there is no supported release line.

| Ref | Security fixes |
| --- | --- |
| Default development branch | Accepted |
| Tags and release archives | Not supported |

## Reporting a vulnerability

Please do not open a public issue with exploit details, credentials, private
device identifiers, or anything else sensitive.

Use GitHub's private vulnerability reporting: open the repository's **Security**
tab and choose **Report a vulnerability**. No alternative private reporting
address is committed to this repository, and a public issue is not a substitute
for a private report. If that button is unavailable, the maintainer needs to
enable private reporting before a report can be filed.

A useful report covers the affected component, the conditions that reproduce the
issue, the impact you expect, and the smallest safe proof that makes it
understandable.

Maintainers: keep private reporting enabled, keep its notifications on, and work
new reports through that queue rather than in public issues.

## What this repository is

Curious Signals builds local XML files and Arduino firmware. It does not deploy
a service and needs no secrets at runtime, so there is no server, database, or
credential store to attack.

The one input-parsing boundary worth knowing about is XInclude. Core experiment
sources may include repository-owned fragments below `src/phyphox/includes/`,
and nothing else. Before `xmllint` runs, the validator in
`src/curious_signals/` rejects URLs, absolute paths, parent traversal, queries,
fragments, missing targets, and any resolved path that escapes that directory.

Run the local checks with:

```sh
make security
```

That target scans for credential patterns, sanity-checks dependencies and
Arduino pins, checks shell syntax (including ShellCheck when installed), and
compiles Python without writing bytecode. It is a guardrail, not a replacement
for dependency advisory review, firmware review, hardware testing, or electrical
safety review.

## Reports about hardware

For firmware or BLE issues, include the exact board revision, Arduino core
version, library versions, phyphox version, and whether an external circuit was
connected. The current firmware supports only the original Nano 33 BLE Sense.
