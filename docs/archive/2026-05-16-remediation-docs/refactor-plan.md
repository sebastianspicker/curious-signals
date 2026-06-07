# Refactor and Code-Quality Plan

Created: 2026-05-16.

Inputs: `AGENTS.md`, `docs/code-index.md`,
`docs/verification-baseline.md`, `docs/architecture-map.md`,
`docs/deprecation-and-simplification-audit.md`, and
`docs/logic-and-correctness-audit.md`.

This is an implementation plan only. It does not change production code. The
sequence favors verification infrastructure, silent wrong-result fixes, and
bounded runtime/protocol changes before style cleanup.

## Current Baseline

- Current automated green checks: `ruff check .`, `ruff format --check .`,
  `pytest`, and `bash scripts/validate-xml.sh`.
- Stronger baseline from `docs/verification-baseline.md`: generated-clean,
  temp-output build, security scripts, SAST, and Arduino compile passed when run
  in an environment with the required tools and package/index access.
- Known caveats: `ci-local` can rewrite generated files in place; astronomy XML
  is not covered by the main semantic validator; no live BLE, phyphox app,
  SensorTag, Owon, or phone runtime probes have been run.
- Worktree caveat: `.github/dependabot.yml` is tracked but deleted in the live
  working tree before this plan.

## Slice R01

- ID: R01.
- Title: Make generated-file verification fail before mutating artifacts.
- Problem: `scripts/ci-local.sh` rebuilds `experiments/*.phyphox` in place
  before `scripts/check-generated-clean.sh`, so stale generated artifacts can be
  silently repaired and reported green.
- Findings addressed: LC-003, DS-014, verification-baseline command-trust note.
- Files affected: `scripts/ci-local.sh`, `tests/test_repo_guardrails.py` or a
  new targeted script test.
- Behavior affected: local CI should fail or report a dirty generated state
  before modifying committed generated artifacts.
- Public contracts affected: strengthens the generated artifact contract; no
  runtime API change.
- Storage/migration impact: none.
- Tests to add or update: add a subprocess test using a temp copy or temp output
  that proves stale generated files are detected without relying on literal
  script text.
- Verification commands: `pytest tests/test_repo_guardrails.py`, full `pytest`,
  `bash scripts/check-generated-clean.sh`, temp-output
  `bash scripts/build-phyphox.sh "$tmpdir"`.
- Rollback strategy: restore the old script order and test if the new guard is
  too disruptive.
- Risk level: medium.
- Ordering rationale: this removes a false-green verification path before any
  generated XML or script cleanup.
- Definition of Done: stale generated artifacts are caught by a behavior-level
  test and the canonical local script no longer masks them.

## Slice R02

- ID: R02.
- Title: Make empty source builds fail.
- Problem: `scripts/build-phyphox.sh` exits `0` when no
  `src/phyphox/*.phyphox.xml` files exist.
- Findings addressed: LC-004.
- Files affected: `scripts/build-phyphox.sh`, targeted script test.
- Behavior affected: missing source XML becomes a failed build instead of a
  successful zero-file build.
- Public contracts affected: build command failure semantics only.
- Storage/migration impact: none.
- Tests to add or update: subprocess test in a temporary repo/tree with no
  source XML.
- Verification commands: targeted script test, full `pytest`,
  `bash scripts/build-phyphox.sh "$tmpdir"`,
  `bash scripts/check-generated-clean.sh`.
- Rollback strategy: restore exit `0` if a documented workflow truly depends on
  zero-source success, and document that exception.
- Risk level: low.
- Ordering rationale: small verification hardening that protects later XML work.
- Definition of Done: no-source builds exit non-zero and normal source builds
  still produce seven core files.

## Slice R03

- ID: R03.
- Title: Add astronomy XML semantic guardrails.
- Problem: `bash scripts/validate-xml.sh` checks astronomy XML syntax but does
  not apply duplicate-container or unknown-reference semantic checks; the
  duplicate `factor2` container in `tidal-locking.phyphox` currently passes.
- Findings addressed: LC-001, LC-002, DS-011.
- Files affected: a focused astronomy semantic test or validator helper,
  `tests/test_astronomy_semantics.py`, possibly `tools/validate_phyphox.py` only
  if the existing validator is extended.
- Behavior affected: no runtime behavior in this slice; it should expose current
  semantic failures first.
- Public contracts affected: establishes the astronomy XML semantic contract.
- Storage/migration impact: none.
- Tests to add or update: duplicate container detection and unknown reference
  detection over every `experiments/astronomy/*.phyphox`.
- Verification commands: `pytest tests/test_astronomy_semantics.py`, full
  `pytest`, `bash scripts/validate-xml.sh`.
- Rollback strategy: disable only the new failing assertion while preserving the
  helper and documenting the runtime uncertainty.
- Risk level: low for tests, medium for follow-up fixes.
- Ordering rationale: create proof before editing high-risk hand-authored XML.
- Definition of Done: tests fail on duplicate containers and unknown references,
  and all current failures are explicitly known.

## Slice R04

- ID: R04.
- Title: Fix the confirmed tidal-locking duplicate container.
- Problem: `experiments/astronomy/tidal-locking.phyphox` declares `factor2`
  twice, which can produce ambiguous runtime state.
- Findings addressed: LC-001, DS-011.
- Files affected: `experiments/astronomy/tidal-locking.phyphox`,
  `tests/test_astronomy_semantics.py` if the guard from R03 needs adjustment.
- Behavior affected: one SensorTag/light calculation path may change if the
  duplicate was masking state.
- Public contracts affected: astronomy import/runtime behavior for tidal locking.
- Storage/migration impact: none.
- Tests to add or update: keep the duplicate-container test; add a targeted
  graph/input assertion only if the intended container split is clear from code.
- Verification commands: `pytest tests/test_astronomy_semantics.py`,
  `pytest tests/test_astronomy_audit.py tests/test_astronomy_consolidation.py`,
  full `pytest`, `bash scripts/validate-xml.sh`, manual phyphox import when
  available.
- Rollback strategy: revert the XML change and keep the duplicate documented as
  requiring runtime investigation.
- Risk level: medium.
- Ordering rationale: fix the confirmed semantic error after guardrails exist.
- Definition of Done: no duplicate containers remain in astronomy XML and
  tidal-locking still imports and passes existing astronomy tests.

## Slice R05

- ID: R05.
- Title: Tighten core mode and payload-offset validation.
- Problem: `tools/validate_phyphox.py` accepts arbitrary numeric config values
  and truncates source mode values with `int(float(...))`; it also uses a set for
  payload offsets, so duplicate offsets can be hidden.
- Findings addressed: LC-005, LC-006, DS-012.
- Files affected: `tools/validate_phyphox.py`, `tests/test_phyphox_validate.py`,
  possibly `tests/test_phyphox_file_contracts.py`.
- Behavior affected: invalid or ambiguous core experiment XML fails validation
  earlier.
- Public contracts affected: mode IDs must be exact active integer IDs; BLE
  payload offsets must be unique and complete.
- Storage/migration impact: none.
- Tests to add or update: fractional modes `1.1` and `1.9`, reserved modes `7`
  and `8`, out-of-range modes, duplicate offsets, and one-good-path regression.
- Verification commands: `pytest tests/test_phyphox_validate.py`,
  `pytest tests/test_phyphox_file_contracts.py`, full `pytest`,
  `bash scripts/validate-xml.sh`.
- Rollback strategy: revert validator tightening only if a real shipped
  experiment requires a fractional/reserved value, then document that contract.
- Risk level: medium.
- Ordering rationale: protocol validation should become reliable before
  firmware mode behavior changes.
- Definition of Done: validator rejects fractional/reserved/out-of-range core
  mode configs and duplicate offsets while current valid core files still pass.

## Slice R06

- ID: R06.
- Title: Replace brittle guardrail tests with behavior checks.
- Problem: some tests assert literal script text or cleanup strings instead of
  the behavior users rely on.
- Findings addressed: LC-008, DS-013, DS-014, DS-019.
- Files affected: `tests/test_repo_guardrails.py`,
  `tests/test_phyphox_validate.py`, selected astronomy tests.
- Behavior affected: test behavior only.
- Public contracts affected: none directly; tests should describe contracts more
  clearly.
- Storage/migration impact: none.
- Tests to add or update: replace literal `ci-local`/workflow text assertions
  with subprocess behavior; remove private-helper tests only after equivalent
  public validator cases exist.
- Verification commands: changed test files, full `pytest`, `ruff check .`,
  `ruff format --check .`.
- Rollback strategy: restore any removed assertion that catches a real contract
  not covered by the new behavior test.
- Risk level: low.
- Ordering rationale: after R01-R05 establish stronger checks, old brittle tests
  can be simplified safely.
- Definition of Done: tests fail for meaningful behavior regressions and do not
  require a specific internal script spelling unless that spelling is the
  contract.

## Slice R07

- ID: R07.
- Title: Align firmware initial config state with default mode.
- Problem: firmware starts in acceleration mode but initializes the readable
  config characteristic to zero, which is not an active mode.
- Findings addressed: LC-010.
- Files affected: `arduino/phyphox_ble_sense/phyphox_ble_sense.ino`, possibly a
  firmware/protocol static test.
- Behavior affected: BLE config readback before an app write should match the
  actual default mode or become intentionally unavailable.
- Public contracts affected: BLE config characteristic read semantics.
- Storage/migration impact: none.
- Tests to add or update: static/protocol test asserting default config bytes
  encode `1.0` if the characteristic remains readable.
- Verification commands: targeted pytest, full `pytest`,
  `bash scripts/validate-xml.sh`, `bash scripts/compile-arduino.sh`, live BLE
  readback when hardware is available.
- Rollback strategy: revert to zero config if a real phyphox app workflow
  requires zero before writing, and document the mismatch.
- Risk level: medium.
- Ordering rationale: fixes a silent state mismatch before changing reserved or
  failed-sensor behavior.
- Definition of Done: firmware initial readable config and actual mode are
  consistent, and compile plus protocol checks pass.

## Slice R08

- ID: R08.
- Title: Define and enforce reserved-mode behavior.
- Problem: modes `7` and `8` are reserved but accepted by range checks and then
  silently leave the current mode active.
- Findings addressed: LC-011, DS-006.
- Files affected: `arduino/phyphox_ble_sense/phyphox_ble_sense.ino`,
  `experiments/phyphox_constants.json` only if the public contract changes,
  tests documenting the contract.
- Behavior affected: writes of reserved mode IDs should be explicitly rejected,
  ignored with documented state, or removed from accepted runtime range.
- Public contracts affected: BLE config mode contract.
- Storage/migration impact: none.
- Tests to add or update: static or unit-style contract test for active,
  reserved, non-finite, and out-of-range config writes; live BLE probe when
  available.
- Verification commands: targeted pytest, full `pytest`,
  `bash scripts/validate-xml.sh`, `bash scripts/compile-arduino.sh`, live config
  writes for modes `7` and `8`.
- Rollback strategy: restore silent keep-current behavior only if git history or
  deployed experiments prove it is required.
- Risk level: high.
- Ordering rationale: high-risk runtime protocol fix after the validator already
  rejects reserved app-side configs.
- Definition of Done: reserved mode handling is explicit, tested, documented if
  compatibility changes, and does not alter active mode behavior.

## Slice R09

- ID: R09.
- Title: Surface unavailable sensor modes instead of streaming ambiguous NaNs.
- Problem: sensor init failure leaves BLE advertising active, and selected modes
  can keep sending samples with NaN channels while appearing connected.
- Findings addressed: LC-009.
- Files affected: `arduino/phyphox_ble_sense/phyphox_ble_sense.ino`,
  possibly README/runbook documentation if user-visible failure behavior changes.
- Behavior affected: runtime failure reporting for missing sensors or inactive
  sensor modes.
- Public contracts affected: BLE streaming semantics and user-visible state.
- Storage/migration impact: none.
- Tests to add or update: static/protocol test for explicit unavailable-mode
  handling if feasible; otherwise document manual hardware test steps.
- Verification commands: `bash scripts/compile-arduino.sh`, full `pytest`,
  `bash scripts/validate-xml.sh`, live mode probes with each sensor and an
  induced or documented sensor-failure path.
- Rollback strategy: revert to current NaN streaming if phyphox cannot display
  the explicit failure path, and document the limitation.
- Risk level: high.
- Ordering rationale: silent wrong runtime behavior outranks style and XML
  deduplication.
- Definition of Done: unavailable sensor states cannot be mistaken for valid
  measurements, and skipped hardware checks are explicitly documented if not run.

## Slice R10

- ID: R10.
- Title: Add guards for zero and incomplete astronomy calculations.
- Problem: albedo and transit formulas divide by maximum signal, and transit
  averages can consume zero/incomplete timing values before enough events exist.
- Findings addressed: LC-007, LC-012, DS-010.
- Files affected: `experiments/astronomy/albedo.phyphox`,
  `experiments/astronomy/transitmethode.phyphox`, targeted astronomy tests.
- Behavior affected: display/output behavior for zero signal, negative depth,
  and not-yet-ready transit averages.
- Public contracts affected: astronomy experiment results and exported values.
- Storage/migration impact: none.
- Tests to add or update: semantic tests for guarded formulas and labels that
  explain not-ready states; runtime/import checks when possible.
- Verification commands: targeted astronomy tests, full `pytest`,
  `bash scripts/validate-xml.sh`, manual/simulated phyphox runs with zero,
  constant, and normal sample data.
- Rollback strategy: revert individual formula guard if phyphox expression
  semantics differ from expectation, preserving a documented runtime note.
- Risk level: medium.
- Ordering rationale: fixes silent wrong educational results before cosmetic
  cleanup of astronomy files.
- Definition of Done: zero/incomplete inputs do not present plausible but wrong
  numeric results, and normal examples still calculate expected values.

## Slice R11

- ID: R11.
- Title: Clarify auxiliary and stale documentation surfaces.
- Problem: public docs mix teaching experiments with the Owon debug helper, CI
  docs are duplicated, `agent.md` is stale/missing, and deprecated audit docs are
  easy to mistake for current authority.
- Findings addressed: DS-002, DS-003, DS-005, DS-015, DS-020.
- Files affected: `README.md`, `docs/REPO_MAP.md`, `.gitignore`,
  `docs/ci.md`, `docs/ci/README.md`, `docs/ci/ci.md`,
  `docs/ci/ci-decision.md`, possibly `docs/deprecated/audit/README.md`.
- Behavior affected: documentation only.
- Public contracts affected: published documentation and discoverability.
- Storage/migration impact: none.
- Tests to add or update: none unless docs links are tested.
- Verification commands: `rg "agent.md|docs/ci|ci-decision|deprecated/audit|owon"`
  to check links/references, `ruff check .`, and full `pytest` only if tests or
  tested wording change.
- Rollback strategy: restore any doc path that external docs or README links
  require.
- Risk level: low.
- Ordering rationale: after correctness risks are queued, low-risk docs cleanup
  can reduce confusion without touching runtime.
- Definition of Done: one current CI documentation path exists, stale `agent.md`
  references are resolved, and Owon/debug material is clearly auxiliary.

## Slice R12

- ID: R12.
- Title: Decide the tracked Dependabot config state.
- Problem: `.github/dependabot.yml` is tracked but deleted in the live worktree,
  so the repository has an unresolved config state.
- Findings addressed: DS-001, code-index coverage gap.
- Files affected: `.github/dependabot.yml` or repository docs if intentionally
  removed.
- Behavior affected: GitHub dependency update behavior.
- Public contracts affected: repository maintenance automation.
- Storage/migration impact: none.
- Tests to add or update: none.
- Verification commands: inspect `git log -- .github/dependabot.yml`,
  `git show HEAD:.github/dependabot.yml` if present, and GitHub repository
  settings if available; run `git status --short`.
- Rollback strategy: restore the tracked file from `HEAD` if removal is not
  intentional.
- Risk level: medium.
- Ordering rationale: config state should be resolved separately from code
  cleanup because it affects automation, not runtime.
- Definition of Done: the file is either restored with known purpose or removed
  intentionally with documented impact.

## Slice R13

- ID: R13.
- Title: Simplify build/security script internals without changing behavior.
- Problem: script logic is duplicated or brittle, especially source-file loops,
  dependency pin parsing, and the limited custom secret scanner.
- Findings addressed: DS-016, DS-017, DS-018.
- Files affected: `scripts/build-phyphox.sh`,
  `scripts/check-generated-clean.sh`, `scripts/validate-xml.sh`,
  `scripts/deps-scan.sh`, `scripts/secret-scan.sh`, script tests if added.
- Behavior affected: none intended.
- Public contracts affected: command outputs and exit codes should remain stable
  unless documented.
- Storage/migration impact: none.
- Tests to add or update: only behavior-level subprocess tests for any changed
  script behavior; avoid adding a shell framework.
- Verification commands: `bash scripts/sast-minimal.sh`,
  `shellcheck scripts/*.sh`, `bash scripts/validate-xml.sh`,
  `bash scripts/check-generated-clean.sh`, temp-output
  `bash scripts/build-phyphox.sh "$tmpdir"`, `bash scripts/deps-scan.sh`,
  `bash scripts/secret-scan.sh`.
- Rollback strategy: revert the specific script touched if output or exit-code
  compatibility breaks.
- Risk level: medium.
- Ordering rationale: do after verification false-greens are fixed so script
  refactors cannot hide regressions.
- Definition of Done: scripts are simpler or better scoped, all previous command
  contracts still pass, and no unrelated generated files change.

## Slice R14

- ID: R14.
- Title: Simplify firmware mode dispatch only after runtime behavior is covered.
- Problem: `readChannels()` is a long mode branch in a runtime-critical loop,
  and `readFloat32LE()` silently converts short/null input to `0.0f`.
- Findings addressed: DS-007, DS-008, LC-009, LC-011.
- Files affected: `arduino/phyphox_ble_sense/phyphox_ble_sense.ino`, firmware
  tests or docs if added.
- Behavior affected: none intended beyond any explicit failure behavior already
  decided in R08/R09.
- Public contracts affected: BLE payload and mode semantics must not change.
- Storage/migration impact: none.
- Tests to add or update: only add tests or probes that verify active modes map
  to the same channels and invalid config writes do not become valid modes.
- Verification commands: `bash scripts/compile-arduino.sh`,
  `bash scripts/validate-xml.sh`, full `pytest`, live phyphox BLE probes for all
  active modes.
- Rollback strategy: revert the firmware-only refactor if any mode payload,
  timing, or compile behavior changes unexpectedly.
- Risk level: high.
- Ordering rationale: style-level firmware simplification waits until the
  higher-risk behavior problems have explicit coverage.
- Definition of Done: mode dispatch is clearer, payload bytes and active mode
  behavior are unchanged, and any skipped hardware probe is called out.

## Slice R15

- ID: R15.
- Title: Evaluate XML deduplication only where generation already exists.
- Problem: core XML and astronomy XML contain repeated blocks; some repetition
  is generated-artifact contract, while hand-edited astronomy repetition may be
  runtime-sensitive.
- Findings addressed: DS-009, DS-010, DS-011.
- Files affected: likely `src/phyphox/*.phyphox.xml` and
  `src/phyphox/includes/*.xml` first; astronomy files only after runtime proof.
- Behavior affected: none intended.
- Public contracts affected: generated core `.phyphox` artifacts must remain
  importable and match source output.
- Storage/migration impact: none.
- Tests to add or update: generated parity and focused physics/unit assertions
  for any source XML touched.
- Verification commands: `bash scripts/build-phyphox.sh`,
  `bash scripts/check-generated-clean.sh`, `bash scripts/validate-xml.sh`, full
  `pytest`, phyphox import spot-checks.
- Rollback strategy: revert the XML/include change if generated output changes
  beyond intended mechanical expansion.
- Risk level: medium for core generated XML, high for astronomy XML.
- Ordering rationale: deduplication is last because it is mostly maintainability
  and can create broad diffs.
- Definition of Done: any deduplication reduces real repeated source while
  preserving generated artifacts and import/runtime contracts.

## Deferred Until Evidence Exists

- Deleting `reference/`: usage is local and ignored; remove only after explicit
  operator confirmation or git-history/workflow proof. Findings: DS-004.
- Removing `experiments/astronomy/owon_digital_multimeter-debug.phyphox`: keep
  as auxiliary until Owon classroom/runtime use is verified absent. Findings:
  DS-005, DS-020.
- Deleting `docs/deprecated/audit/*`: safe only after current docs no longer
  route readers there as authority. Findings: DS-003.
- Broad architecture rewrites, new generators for hand-edited astronomy XML, or
  new abstractions for single-use code: out of scope unless a later slice proves
  at least two real call sites need them now.

## Suggested PR Grouping

1. PR 1: R01-R02 verification false-green fixes.
2. PR 2: R03-R04 astronomy semantic guardrail and confirmed duplicate fix.
3. PR 3: R05 validator correctness.
4. PR 4: R06 test-quality cleanup.
5. PR 5: R07-R09 firmware/runtime correctness, split further if hardware
   verification is slow.
6. PR 6: R10 astronomy formula/state guards.
7. PR 7: R11-R12 docs/config cleanup.
8. PR 8+: R13-R15 simplification-only work, one subsystem at a time.
