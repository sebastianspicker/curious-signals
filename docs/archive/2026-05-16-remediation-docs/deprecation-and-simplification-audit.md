# Deprecation and Simplification Audit

Audit date: 2026-05-16.

Scope: live repository files excluding `.git`, Python/Ruff caches, and generated
cache directories. This is an audit-only document. No production code was
changed.

Pre-existing worktree state: `.github/dependabot.yml` is tracked but deleted in
the working tree; `AGENTS.md`, `docs/code-index.md`,
`docs/verification-baseline.md`, and `docs/architecture-map.md` are untracked.

## Checks Run

- `ruff check .`: passed.
- `ruff format --check .`: passed, `14 files already formatted`.
- No dedicated type checker is configured in this repo.
- No production code was modified.

## Summary

No unused Python imports, unused Python functions, or syntax-level dead code were
reported by Ruff. The strongest simplification candidates are not simple
compiler-detectable dead code; they are archived documentation surfaces, optional
local reference material, compatibility behavior, duplicated XML blocks, and
tests/scripts that assert implementation text instead of behavior.

Do not delete anything below without running the listed verification. For items
marked "needs runtime or git-history verification", current usage cannot be
proven from the live tree alone.

## Findings

### DS-001

- Category: unused/obsolete tracked config.
- Location: `.github/dependabot.yml`.
- Evidence: `git ls-files .github/dependabot.yml` reports the file as tracked,
  but `git status --short` shows `D .github/dependabot.yml`, and the file is not
  present for inspection.
- Why it is likely obsolete or harmful: a tracked-but-deleted CI/dependency
  configuration creates ambiguity: either the repo intentionally removed
  Dependabot, or a required automation file is missing.
- What could break if changed: restoring it could re-enable outdated dependency
  update behavior; deleting it permanently could remove intended dependency
  monitoring.
- Suggested action: investigate.
- Risk level: medium.
- Verification needed: inspect git history and GitHub repository settings for
  Dependabot use; if removal is intentional, commit the deletion and document the
  replacement dependency-update policy.

### DS-002

- Category: misleading stale documentation reference.
- Location: `docs/REPO_MAP.md:16`, `.gitignore:11-12`.
- Evidence: `docs/REPO_MAP.md` lists `agent.md` as operator guidance, while
  `.gitignore` marks `agent.md` as an ignored internal guide. No tracked
  `agent.md` exists in the live tree.
- Why it is likely obsolete or harmful: a repo map that points future maintainers
  to an ignored/missing file is a stale navigation path.
- What could break if changed: local operators may have an ignored `agent.md`
  workflow not visible in Git.
- Suggested action: simplify.
- Risk level: low.
- Verification needed: check whether a local `agent.md` exists and whether any
  active workflow depends on it; otherwise remove or reword the repo-map entry.

### DS-003

- Category: deprecated/archive surface.
- Location: `docs/deprecated/audit/*`, especially
  `docs/deprecated/audit/README.md:1-13` and
  `docs/deprecated/audit/PROGRESS.md:3-8`.
- Evidence: the folder is explicitly named `deprecated`; README calls it an
  archived audit workspace; PROGRESS says phase/checkpoint status is complete.
- Why it is likely obsolete or harmful: archived runbooks and ledgers can be
  mistaken for active instructions. They also keep references to optional local
  `reference/phyphox-wiki-core/` material.
- What could break if changed: historical audit traceability and resume context
  for the prior astronomy consolidation campaign.
- Suggested action: keep or archive more aggressively.
- Risk level: low.
- Verification needed: confirm no current docs link readers into these files as
  active procedure; if only history is needed, replace the directory with a short
  summary or keep it clearly archived.

### DS-004

- Category: unused/local ignored file tree.
- Location: `reference/`, `.gitignore:49-52`, deprecated audit docs referencing
  `reference/phyphox-wiki-core/`.
- Evidence: `reference/` is ignored by `.gitignore`; `find reference -type f |
  wc -l` reports 1,758 files; audit docs describe the reference as optional and
  local-only.
- Why it is likely obsolete or harmful: large ignored mirrors can silently drift
  from upstream and influence local work without CI/review visibility.
- What could break if changed: local audit workflows that deliberately use the
  mirrored phyphox wiki when available.
- Suggested action: investigate.
- Risk level: low for the tracked repo, medium for local operator workflows.
- Verification needed: decide whether the local mirror is still used; if not,
  delete it locally. If it is used, document refresh provenance and do not treat
  it as current without checking upstream.

### DS-005

- Category: auxiliary/debug file in user-facing experiment tree.
- Location: `experiments/astronomy/owon_digital_multimeter-debug.phyphox:1-4`,
  `docs/ASTRONOMY_EXPERIMENTS_COMPANION.md:38`,
  `tests/test_astronomy_audit.py:111-114`.
- Evidence: the file description says it is a debug utility and not an astronomy
  teaching experiment; the companion also marks it as a measurement helper, not a
  teaching experiment; tests assert that wording.
- Why it is likely obsolete or harmful: debug-named utility files in the
  importable astronomy experiment directory can confuse classroom users and make
  the public experiment inventory less clean.
- What could break if changed: the multimeter-supported transit path may need
  this file for hardware integration/debugging.
- Suggested action: investigate.
- Risk level: medium.
- Verification needed: run or document an Owon workflow. If no active workflow
  needs the standalone debug file, move it out of the user-facing astronomy
  inventory or archive it with tests/docs updated.

### DS-006

- Category: obsolete compatibility branch.
- Location: `arduino/phyphox_ble_sense/phyphox_ble_sense.ino:70-96`,
  `experiments/phyphox_constants.json:16`,
  `arduino/phyphox_ble_sense/README.md:31`.
- Evidence: firmware accepts raw config values `1..9`, active modes omit `7` and
  `8`, and the default branch silently keeps the current mode for reserved
  values.
- Why it is likely obsolete or harmful: reserved future modes are a permanent
  compatibility path unless an actual future experiment exists. The silent
  keep-current-mode behavior can make a wrong config look like success.
- What could break if changed: any existing app-side experiment or local file
  that writes mode `7` or `8` and expects the old mode to remain active.
- Suggested action: investigate.
- Risk level: high.
- Verification needed: search git history and distributed experiment files for
  mode `7`/`8`; perform a live app probe for invalid/reserved config behavior;
  if unused, replace silent compatibility with explicit invalid-mode behavior and
  update tests/docs.

### DS-007

- Category: single-use defensive helper / weak error behavior.
- Location: `arduino/phyphox_ble_sense/phyphox_ble_sense.ino:59-68` and
  `arduino/phyphox_ble_sense/phyphox_ble_sense.ino:221-228`.
- Evidence: `readFloat32LE` has null/short-buffer fallback returning `0.0f`, but
  the only live call passes a local `uint8_t buf[4]` and `sizeof(buf)` after
  `configCharacteristic.readValue(...)`.
- Why it is likely obsolete or harmful: the fallback converts malformed input to
  mode `0.0f` semantics instead of surfacing invalid data. It also carries a
  generic helper shape for one fixed call site.
- What could break if changed: future callers might rely on the helper's
  defensive behavior; current firmware code appears to have only one call site.
- Suggested action: inline or simplify.
- Risk level: medium.
- Verification needed: compile firmware; add/keep a focused test or hardware
  probe for valid and malformed config writes if a test seam exists.

### DS-008

- Category: endless if/else branching.
- Location: `arduino/phyphox_ble_sense/phyphox_ble_sense.ino:107-173`.
- Evidence: `readChannels` is a long sequence of mode-specific `if` blocks with
  repeated sensor-read shape for IMU modes and early returns for every branch.
- Why it is likely obsolete or harmful: adding or changing a mode requires
  editing a long runtime-critical branch chain, increasing risk of wrong channel
  mapping.
- What could break if changed: real-time sensor read behavior, NaN-on-missing
  behavior, and payload ordering.
- Suggested action: simplify.
- Risk level: high.
- Verification needed: compile firmware, rerun XML/protocol tests, and perform
  live mode-by-mode sensor probes. Prefer a direct `switch` or small local helper
  only if it reduces the existing branch chain without adding a framework.

### DS-009

- Category: duplicated source XML / copy-paste code.
- Location: `src/phyphox/accelerometer_plot_v1-2.phyphox.xml:47-170`,
  `src/phyphox/gyroscope_plot_v1-2.phyphox.xml:47-171`,
  `src/phyphox/magnetometer_plot_v1-2.phyphox.xml:45-120`.
- Evidence: accelerometer and gyroscope repeat the same CH2..CH5 container,
  Graph/Absolute/Multi/Simple/Raw Data, and four-formula normalization structure
  with different labels/units/formulas; magnetometer repeats the same 3-axis
  graph/value layout without normalization.
- Why it is likely obsolete or harmful: copy-paste XML makes UI/channel changes
  easy to apply to one sensor and miss another.
- What could break if changed: generated file parity, phyphox UI layout, unit
  conversions, and classroom import compatibility.
- Suggested action: deduplicate.
- Risk level: medium.
- Verification needed: create no broad abstraction unless the repeated shape is
  proven stable; if deduplicating, use the existing XInclude/build mechanism or a
  small generator, then run `bash scripts/build-phyphox.sh`,
  `bash scripts/check-generated-clean.sh`, `pytest`, and import at least one
  generated file in phyphox.

### DS-010

- Category: boilerplate / generated-by-hand pattern.
- Location: `experiments/astronomy/transitmethode.phyphox:450-844` and
  `experiments/astronomy/transitmethode.phyphox:1110-1147`.
- Evidence: the transit stopwatch section repeats near-identical
  rangefilter/min/first/trigger blocks for numbered `on0/off0` through
  `on5/off5`, and the trigger configuration UI exposes only two thresholds that
  feed all repeated blocks.
- Why it is likely obsolete or harmful: hand-unrolled repeated XML makes it hard
  to audit whether every numbered transit behaves identically. A one-line drift
  can produce a wrong transit duration while the file remains valid XML.
- What could break if changed: transit timing behavior, trigger semantics, and
  classroom worksheets built around the current six-event limit.
- Suggested action: investigate or replace with generated XML.
- Risk level: high.
- Verification needed: needs runtime or git-history verification. Identify why
  six transit slots exist; if a generator is introduced, compare generated XML
  against current behavior and run `pytest`, XML validation, and a live phyphox
  transit-timing probe.

### DS-011

- Category: copy-paste code / mixed measurement responsibilities.
- Location: `experiments/astronomy/tidal-locking.phyphox:93-183` and
  `experiments/astronomy/tidal-locking.phyphox:186-362`.
- Evidence: the file carries parallel SensorTag #1 and #2 container/input blocks
  and repeated temperature/IR/light conversion logic with suffixed container
  names.
- Why it is likely obsolete or harmful: duplicated sensor branches can drift in
  formula, unit, or output naming while still producing valid XML.
- What could break if changed: two-SensorTag classroom comparison behavior and
  tests that assert specific graph wiring.
- Suggested action: keep or deduplicate cautiously.
- Risk level: medium.
- Verification needed: live two-SensorTag workflow or git-history verification
  of why this was hand-unrolled; then rerun astronomy semantic tests and a
  phyphox import/runtime probe.

### DS-012

- Category: mixed responsibilities / brittle compatibility shim.
- Location: `tools/validate_phyphox.py:14-29`,
  `tools/validate_phyphox.py:65-217`, `tools/validate_phyphox.py:220-468`.
- Evidence: one validator file parses firmware text with regex, loads constants
  JSON, reads source XML mode config, validates generated XML structure, checks
  BLE offsets, and exposes the CLI.
- Why it is likely obsolete or harmful: the validator is doing several jobs at
  once, and regex coupling to firmware syntax can fail when firmware constants
  move even if behavior is unchanged.
- What could break if changed: CI validation and many tests import private helper
  functions from this module.
- Suggested action: simplify.
- Risk level: medium.
- Verification needed: keep behavior first. Before refactoring, preserve CLI
  output and public `validate_phyphox` behavior with tests; consider replacing
  firmware regex checks with a smaller explicit contract source only if that does
  not weaken UUID/mode drift detection.

### DS-013

- Category: implementation-trivial tests / test boilerplate.
- Location: `tests/test_phyphox_validate.py:90-172`.
- Evidence: many tests assert private helper behavior for `_local_name`,
  `_child`, `_children`, and `_text`, including XML snippets such as
  `<root><child/></root>`.
- Why it is likely obsolete or harmful: these tests mirror helper
  implementation details and make internal refactors noisier without directly
  proving user-visible validation behavior.
- What could break if changed: loss of fine-grained diagnostics for namespace and
  XML helper behavior.
- Suggested action: simplify or delete after replacement coverage.
- Risk level: low.
- Verification needed: keep or add behavior-level validator tests for namespaced
  XML and missing/empty containers, then remove private-helper-only tests and run
  `pytest`.

### DS-014

- Category: duplicate logic / implementation-coupled guardrail test.
- Location: `tests/test_repo_guardrails.py:27-33`.
- Evidence: the test asserts literal strings in `scripts/ci-local.sh`,
  `.github/workflows/ci.yml`, and `scripts/check-generated-clean.sh`.
- Why it is likely obsolete or harmful: the check can fail for harmless command
  restructuring while missing semantically equivalent generated-clean behavior.
- What could break if changed: CI could stop running generated-clean without a
  test noticing, if replacement coverage is weaker.
- Suggested action: replace.
- Risk level: medium.
- Verification needed: replace text assertions with a behavior-level check that
  modifies a generated artifact in a temp workspace or verifies workflow command
  execution more structurally; run `pytest` and CI/local verification.

### DS-015

- Category: duplicated documentation.
- Location: `docs/ci.md:1-27`, `docs/ci/README.md:1-7`,
  `docs/ci/ci.md:1-78`, `docs/ci/ci-decision.md:1-30`.
- Evidence: root `docs/ci.md` and `docs/ci/ci.md` both describe the same CI
  jobs and local reproduction, while `docs/ci/README.md` is a router page.
- Why it is likely obsolete or harmful: multiple CI docs create drift risk; the
  current workflow already has a single source in `.github/workflows/ci.yml` and
  `scripts/ci-local.sh`.
- What could break if changed: external links to either CI doc path.
- Suggested action: deduplicate.
- Risk level: low.
- Verification needed: check inbound links with `rg "docs/ci|ci.md"`; keep one
  canonical CI doc and make the other paths short redirects/routers if link
  compatibility matters.

### DS-016

- Category: duplicated script logic.
- Location: `scripts/build-phyphox.sh:24-45`,
  `scripts/check-generated-clean.sh:7-35`, `scripts/validate-xml.sh:18-60`.
- Evidence: source/generated file discovery, temp directory handling, XInclude
  expansion, post-processing, and generated comparison logic are split across
  three scripts.
- Why it is likely obsolete or harmful: drift between build, validation, and
  generated-clean behavior can let one path pass while another fails.
- What could break if changed: Make/CI/local CI command contracts and generated
  artifact paths.
- Suggested action: simplify.
- Risk level: medium.
- Verification needed: avoid a large shell framework. If simplifying, make one
  script call the existing smaller script paths, then run `ruff check .`,
  `pytest`, `bash scripts/validate-xml.sh`, `bash scripts/check-generated-clean.sh`,
  and `bash scripts/build-phyphox.sh "$tmpdir"`.

### DS-017

- Category: brittle parser / wrapper that adds limited value.
- Location: `scripts/deps-scan.sh:7-75`.
- Evidence: the script parses `scripts/compile-arduino.sh` with grep and shell
  token splitting to infer whether Arduino cores/libs are pinned; it separately
  parses `requirements-test.txt` by text.
- Why it is likely obsolete or harmful: restructuring the compile script can
  break the scanner even if dependencies remain pinned, or bypass it if the
  command text changes shape.
- What could break if changed: lightweight CI assurance that dependencies are
  constrained.
- Suggested action: replace or keep with clearer scope.
- Risk level: medium.
- Verification needed: if replacing, prefer a simple explicit manifest or
  machine-readable dependency list already used by compile/install scripts; run
  `bash scripts/deps-scan.sh`, `bash scripts/compile-arduino.sh`, and CI.

### DS-018

- Category: limited custom scanner / no-value-wrapper risk.
- Location: `scripts/secret-scan.sh:17-27` and
  `scripts/secret-scan.sh:37-50`.
- Evidence: the script states the pattern list is intentionally tight and notes
  filenames containing colons may be misparsed; it scans every file once per
  pattern.
- Why it is likely obsolete or harmful: a custom minimal scanner can create a
  false sense of security while missing common secret formats.
- What could break if changed: current CI has a dependency-free secret baseline;
  adding a real scanner introduces tooling/version management.
- Suggested action: keep or replace.
- Risk level: low.
- Verification needed: if stronger scanning is required, evaluate an approved
  scanner separately; otherwise document this as a minimal guard only and keep
  the existing untracked-file regression test.

### DS-019

- Category: duplicate helper/test code.
- Location: `tests/test_astronomy_audit.py:22-27`,
  `tests/test_astronomy_consolidation.py:10-11`,
  `tests/test_astronomy_semantics.py:13-31`.
- Evidence: three astronomy test files repeat small file-loading/text/parsing
  helpers and path constants for the same `experiments/astronomy` surface.
- Why it is likely obsolete or harmful: minor duplication increases maintenance
  churn when astronomy file loading changes.
- What could break if changed: low-level test readability; shared test helpers
  can also become an abstraction if they grow too much.
- Suggested action: keep or inline consistently.
- Risk level: low.
- Verification needed: because helpers are tiny, do not add a new abstraction
  unless another edit already touches these tests. If touched, either keep the
  duplication explicit or consolidate only the path constant and loader, then run
  `pytest tests/test_astronomy_audit.py tests/test_astronomy_consolidation.py tests/test_astronomy_semantics.py`.

### DS-020

- Category: misleading names / mixed public inventory.
- Location: `README.md:43-53`,
  `experiments/astronomy/owon_digital_multimeter-debug.phyphox:1-4`,
  `docs/ASTRONOMY_EXPERIMENTS_COMPANION.md:158-176`.
- Evidence: README lists the debug multimeter file alongside astronomy
  experiments; the file and companion both say it is a debug/integration utility
  and not a teaching experiment.
- Why it is likely obsolete or harmful: the public import list mixes classroom
  experiments with a debug helper.
- What could break if changed: users who currently discover the Owon helper from
  README.
- Suggested action: simplify.
- Risk level: low.
- Verification needed: separate the README list into "teaching experiments" and
  "auxiliary hardware helpers", or move the helper after runtime verification.
  Run astronomy tests and inspect docs links.

## No Finding / Keep Notes

- `experiments/*.phyphox` are duplicated with `src/phyphox/*.phyphox.xml`, but
  this is an intentional generated-artifact contract so clone-and-import works
  without a build step. Do not delete without changing the published workflow.
- `src/phyphox/includes/*.xml` are not single-use; all seven generated source
  experiments include them, so they are justified.
- `requirements-test.txt` contains only `pytest` and `ruff`; both are used by
  Makefile, CI, and local verification.
- No stale feature flags were found besides firmware reserved modes `7` and `8`.
- No deprecated third-party library APIs were proven from static inspection.

## Recommended Safe Order

1. Low-risk docs cleanup: DS-002, DS-015, DS-020.
2. Clarify auxiliary/local surfaces: DS-003, DS-004, DS-005.
3. Test cleanup: DS-013, DS-014, DS-019.
4. Script simplification: DS-016, DS-017, DS-018.
5. Runtime/protocol simplification only after hardware or history evidence:
   DS-006, DS-007, DS-008.
6. XML deduplication only after deciding whether to generate repeated XML:
   DS-009, DS-010, DS-011.

## Verification Matrix for Any Follow-Up

- Docs-only cleanup: `rg` link checks plus `ruff check .` if test files are not
  touched.
- Test cleanup: targeted `pytest` for touched test files, then full `pytest`.
- Script cleanup: `shellcheck scripts/*.sh`, `bash scripts/validate-xml.sh`,
  `bash scripts/check-generated-clean.sh`, and temp-output
  `bash scripts/build-phyphox.sh "$tmpdir"`.
- Core XML cleanup: `bash scripts/build-phyphox.sh`,
  `bash scripts/check-generated-clean.sh`, `bash scripts/validate-xml.sh`, and
  full `pytest`.
- Firmware cleanup: `bash scripts/compile-arduino.sh`, full XML/protocol tests,
  and live phyphox BLE mode probes.
- Astronomy runtime cleanup: relevant astronomy pytest files, XML syntax checks,
  phyphox import checks, and device-path probes for phone/SensorTag/Owon where
  applicable.
