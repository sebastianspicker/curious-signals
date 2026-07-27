# Security Policy

## Supported versions

No public release has been published.

| Ref | Security fixes |
| --- | --- |
| Default development branch | Accepted |
| Tags and release archives | Not supported |

## Reporting a vulnerability

Do not open a public issue containing exploit details, credentials, private
device identifiers, or other sensitive material.

Use GitHub private vulnerability reporting if this repository offers a private
report action. If it is unavailable, open a minimal public issue stating only
that the matter is security-sensitive so a maintainer can arrange a private
channel.

Include the affected component, reproduction conditions, impact, and the
smallest safe proof needed to understand the issue.

The maintainers still need to confirm a reliable private reporting path before
publishing a release.

## Security boundary

This repository builds local XML files and Arduino firmware. It does not deploy
a service and does not require repository secrets at runtime.

Core source experiments may use XInclude only for repository-owned fragments
below `src/phyphox/includes/`. `tools/validate_xinclude_paths.py` rejects URLs,
absolute paths, parent traversal, queries, fragments, missing targets, and
resolved paths outside that directory before XInclude expansion.

Run the local security checks with:

```sh
make security
```

This target runs the repository secret-pattern scan, dependency constraint
checks, shell syntax checks, ShellCheck when installed, and Python bytecode
compilation. These checks do not replace dependency advisory review, firmware
review, hardware testing, or electrical safety review.

## Hardware reports

For firmware or BLE reports, include the exact board revision, Arduino core,
library versions, phyphox version, and whether an external circuit was
connected. The current firmware supports only the original Nano 33 BLE Sense.
