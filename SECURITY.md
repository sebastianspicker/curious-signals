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

GitHub private vulnerability reporting is enabled for this repository. Use the
repository's Security tab and select **Report a vulnerability**. Do not open a
public issue as a substitute for the private report.

Include the affected component, reproduction conditions, impact, and the
smallest safe proof needed to understand the issue.

Maintainers should keep private-report notifications enabled and review new
reports through the repository's private vulnerability reporting queue.

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
