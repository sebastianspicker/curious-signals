# CI Decision

Date: 2026-02-05

## Decision
FULL CI.

## Why this repo benefits from FULL CI
- The repo contains executable code (Arduino sketch) and generated artifacts (compiled `*.phyphox` files). Both can regress silently without automated checks.
- Validation is deterministic and does not require secrets or live infrastructure.
- The compile step is a meaningful safety net for the Arduino sketch and is reproducible on GitHub-hosted runners with pinned dependencies.

## What runs where
- `push` to default branch: all jobs (Python quality checks, XML/phyphox validation + build freshness, Arduino compile, security baseline).
- `pull_request` (including forks): all jobs; no secrets required.
- `workflow_dispatch`: manual runs of the same jobs.

There are no scheduled or secret-requiring jobs.

## Threat model for CI
- Fork PRs are untrusted. We use `pull_request` (not `pull_request_target`) and do not expose secrets.
- `GITHUB_TOKEN` is read-only (`contents: read`, plus cache access), reducing blast radius.
- No deploy steps, no environment writes, no access to production systems.
- Caches only store toolchain artifacts (Arduino cores/libs), not repository secrets.

## If we later want *more* CI coverage
We would need:
- Hardware-in-the-loop tests on a self-hosted runner with attached Arduino hardware.
- Explicit isolation of hardware secrets/credentials, and a strict separation of untrusted PR jobs.
- Longer-running scheduled tests for device-level validation.
