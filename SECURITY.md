# Security Policy

## Supported versions

Security fixes are applied to the default development branch for the consolidated classroom kit.

## Reporting a vulnerability

Do not open a public issue with sensitive details.

Preferred path:

1. Use GitHub Security Advisories for this repository if they are enabled.
2. If private reporting is unavailable, open a minimal issue that states the problem is security-sensitive and omit exploit details.

## Local security baseline

The repository keeps a small local security matrix:

```sh
bash scripts/secret-scan.sh
bash scripts/deps-scan.sh
bash scripts/sast-minimal.sh
```

CI runs the same baseline on every push and pull request.
