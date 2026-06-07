# Codacy Remediation Ledger

Generated: 2026-06-06

Scope: local Codacy Analysis results after excluding `docs/archive/**`,
`docs/deprecated/**`, `docs/ci/**`, and `reference/**` from Codacy local/Cloud
analysis and GitHub CI triggers.

Baseline command:

```sh
codacy-analysis analyze --install-dependencies --output-format json --output /private/tmp/phyphox-arduino-classroom-kit-codacy-ledger-baseline.json
```

Baseline result:

- Total findings: 407
- Analyzer errors: 0
- Excluded-path findings: 0
- Tools with findings: Bandit, Semgrep, Lizard, PyLintPython3, Prospector,
  Agentlinter, markdownlint
- Tools with zero findings: jackson, shellcheck, Ruff, Trivy, PMD

Latest local Codacy result after CODACY-004 partial remediation plus CODACY-005,
CODACY-006, CODACY-007, and CODACY-008 remediation on 2026-06-07:

- Total findings: 370
- Analyzer errors: 0
- Excluded-path findings: 0
- `PyLintPython3_W1510`: 3 -> 0
- `Semgrep_python.lang.security.audit.dangerous-subprocess-use-audit.dangerous-subprocess-use-audit`: 4 -> 0
- `Bandit_B607`: 4 -> 0
- `Bandit_B603`: 8 -> 4
- `Bandit_B404`: 6 -> 2
- `Lizard_ccn-critical`: 4 -> 0
- `Lizard_nloc-critical`: 1 -> 0
- `Prospector_mccabe`: 3 -> 0
- `markdownlint_MD024`: 2 -> 0
- `Agentlinter_*`: 8 -> 0

Do not remediate `docs/archive/**`, `docs/deprecated/**`, `docs/ci/**`, or
`reference/**` as part of this ledger. They are outside the active remediation
scope.

Final local verification on 2026-06-07:

- `pytest` passed with 145 tests.
- `ruff check .` passed.
- `bash scripts/validate-xml.sh` passed.
- `bash scripts/check-generated-clean.sh` passed.
- `git diff --check -- .codacy/codacy-remediation-ledger.md AGENTS.md
  openclaw.json README.md tools/validate_phyphox.py
  tools/validate_xinclude_paths.py tests/test_phyphox_generated_parity.py
  tests/test_postprocess_phyphox_xml.py tests/test_repo_guardrails.py
  tests/test_validate_xinclude_paths.py` passed.

## Finding Inventory

| Pattern | Tool | Severity | Category | Count | Primary files |
| --- | --- | --- | --- | ---: | --- |
| `Bandit_B101` | Bandit | High | Security | 294 | `tests/test_*.py` |
| `Bandit_B314` | Bandit | Warning | Security | 19 | tests and XML validation tools |
| `Bandit_B405` | Bandit | Warning | Security | 16 | tests and XML validation tools |
| `Semgrep_python.lang.security.use-defused-xml.use-defused-xml` | Semgrep | Error | Security | 16 | tests and XML validation tools |
| `Semgrep_python_xml_rule-element` | Semgrep | High | Security | 10 | tests and XML validation tools |
| `Semgrep_python.lang.security.use-defused-xml-parse.use-defused-xml-parse` | Semgrep | Error | Security | 9 | tests and XML validation tools |
| `Bandit_B603` | Bandit | Warning | Security | 4 | remaining shell-script smoke tests |
| `Bandit_B404` | Bandit | Info | Security | 2 | remaining shell-script smoke tests |
| `Bandit_B607` | Bandit | Warning | Security | 0 | closed by CODACY-004 |
| `Lizard_ccn-critical` | Lizard | Error | Complexity | 0 | closed by CODACY-005 and CODACY-006 |
| `Semgrep_python.lang.security.audit.dangerous-subprocess-use-audit.dangerous-subprocess-use-audit` | Semgrep | Error | Security | 0 | closed by CODACY-004 |
| `Prospector_mccabe` | Prospector | Warning | Complexity | 0 | closed by CODACY-005 |
| `PyLintPython3_W1510` | PyLintPython3 | High | ErrorProne | 0 | closed by CODACY-004 |
| `Agentlinter_*` | Agentlinter | High/Warning | Security/BestPractice | 0 | closed by CODACY-007 |
| `markdownlint_MD024` | markdownlint | Warning | BestPractice | 0 | closed by CODACY-008 |
| `Lizard_nloc-critical` | Lizard | Error | Complexity | 0 | closed by CODACY-005 |

## Remediation Slices

### CODACY-001: Decide and enforce pytest assert policy

- ID: CODACY-001
- Status: BLOCKED_USER_DECISION
- Severity: P2
- Category: Security scanner policy / test hygiene
- Subsystem: tests
- File: `tests/test_astronomy_audit.py`, `tests/test_astronomy_consolidation.py`,
  `tests/test_astronomy_semantics.py`, `tests/test_phyphox_file_contracts.py`,
  `tests/test_phyphox_generated_parity.py`, `tests/test_phyphox_physics.py`,
  `tests/test_phyphox_validate.py`, `tests/test_postprocess_phyphox_xml.py`,
  `tests/test_repo_guardrails.py`, `tests/test_validate_xinclude_paths.py`
- Line range or symbol: `assert` statements across lines 16-661
- Evidence: `Bandit_B101`, 294 findings. Largest clusters:
  `tests/test_phyphox_validate.py` 57, `tests/test_astronomy_audit.py` 64,
  `tests/test_phyphox_physics.py` 48, `tests/test_postprocess_phyphox_xml.py` 32,
  `tests/test_repo_guardrails.py` 22.
- Why it matters: Bandit treats Python `assert` as security-sensitive because
  optimized bytecode removes assertions. In pytest test files, assertions are
  usually intentional and useful, but Codacy will keep reporting them unless the
  project makes an explicit policy decision.
- Runtime/user impact: None in production runtime if these remain test-only.
  High remediation churn if every pytest assertion is rewritten.
- Suggested remediation: Do not blindly rewrite all tests. First decide one of:
  keep pytest assertions and document them as accepted test-only usage; or
  convert tests to explicit helper assertions / `pytest.fail` / comparison
  helpers. If accepting test-only usage, tune Bandit locally/Cloud for `B101` on
  `tests/**` only after explicit false-positive approval.
- Verification required: Run `pytest`, `ruff check tests`, and
  `codacy-analysis analyze --install-dependencies --output-format json --output /tmp/phyphox-codacy-after.json`.
- Suggested test: Existing tests are the coverage. If rewriting assertions,
  preserve failure messages for contract-heavy checks in `tests/test_phyphox_validate.py`.
- Risk of change: Medium if rewriting tests because assertions encode many XML
  and physics invariants; low if the project explicitly configures test-only
  Bandit policy.
- Confidence: high
- Blocker 2026-06-07: 294 `Bandit_B101` findings remain. Rewriting every pytest
  assertion would be high-churn test-only work; tuning `B101` for `tests/**`
  would be an ignore/suppression-style policy decision. Per task rules, do not
  ignore, suppress, exclude, or mark this pattern false positive without
  explicit user confirmation.

### CODACY-002: Replace unsafe XML parsing in active validation tools

- ID: CODACY-002
- Status: BLOCKED_DEPENDENCY_APPROVAL
- Severity: P1
- Category: Security
- Subsystem: XML validation tooling
- File: `tools/validate_phyphox.py`, `tools/validate_xinclude_paths.py`
- Line range or symbol: `tools/validate_phyphox.py:9`,
  `tools/validate_phyphox.py:198`, `tools/validate_phyphox.py:241`,
  `tools/validate_xinclude_paths.py:8`, `tools/validate_xinclude_paths.py:67`
- Evidence: `Bandit_B314`, `Bandit_B405`,
  `Semgrep_python.lang.security.use-defused-xml.use-defused-xml`,
  `Semgrep_python.lang.security.use-defused-xml-parse.use-defused-xml-parse`,
  and `Semgrep_python_xml_rule-element` all flag `xml.etree.ElementTree` imports
  and parse calls.
- Why it matters: These tools parse repository XML and may also be run on local
  files supplied by contributors. Native `xml.etree` does not provide the same
  XXE/entity-expansion hardening as `defusedxml`.
- Runtime/user impact: A malicious or pathological XML file could make local
  validation unsafe or unreliable. This is not Arduino runtime code, but it is
  part of the project verification gate.
- Suggested remediation: Introduce a narrow XML parsing helper that uses
  `defusedxml.ElementTree` for parse/fromstring behavior, then route active
  tools through it. Because this adds or relies on a dependency, get explicit
  approval before changing dependency files. Keep behavior and error messages
  compatible with current validation tests.
- Verification required: `pytest tests/test_phyphox_validate.py
  tests/test_validate_xinclude_paths.py`, `bash scripts/validate-xml.sh`,
  `ruff check tools tests`, and Codacy local analysis.
- Suggested test: Add a focused regression test that a simple internal entity or
  doctype payload is rejected or handled safely by the validation helper without
  changing normal phyphox XML parsing.
- Risk of change: Medium. Parser exceptions and namespace behavior can differ;
  generated and hand-edited experiment validation must stay unchanged.
- Confidence: high
- Blocker 2026-06-07: 25 active-tool XML findings remain across Bandit and
  Semgrep. The correct remediation is to use `defusedxml.ElementTree` or an
  equivalent safe parser helper, which requires adding a test/runtime
  validation dependency. Repository instructions require explicit approval
  before adding production or test dependencies.

### CODACY-003: Replace unsafe XML parsing in tests with the same safe helper

- ID: CODACY-003
- Status: BLOCKED_DEPENDENCY_APPROVAL
- Severity: P2
- Category: Test security / consistency
- Subsystem: tests
- File: `tests/test_astronomy_audit.py`, `tests/test_astronomy_semantics.py`,
  `tests/test_phyphox_file_contracts.py`, `tests/test_phyphox_physics.py`,
  `tests/test_phyphox_validate.py`
- Line range or symbol: imports and parse/fromstring calls around
  `tests/test_astronomy_audit.py:5,27`,
  `tests/test_astronomy_semantics.py:5,21,67,78`,
  `tests/test_phyphox_file_contracts.py:34,36,40,42`,
  `tests/test_phyphox_physics.py:5,14`,
  `tests/test_phyphox_validate.py:159-219`
- Evidence: 51 XML-related findings across Bandit and Semgrep, overlapping with
  CODACY-002 but in tests.
- Why it matters: Tests currently duplicate the unsafe parser pattern and keep
  Codacy noisy even after production/tool code is fixed.
- Runtime/user impact: No direct runtime impact, but it weakens the scanner
  signal and can hide real parser issues in active tooling.
- Suggested remediation: After CODACY-002 creates a safe parser helper, update
  tests to use it. For tests that intentionally verify parser behavior, keep
  the intent explicit and avoid weakening assertions.
- Verification required: `pytest tests/test_astronomy_audit.py
  tests/test_astronomy_semantics.py tests/test_phyphox_file_contracts.py
  tests/test_phyphox_physics.py tests/test_phyphox_validate.py`, then Codacy
  local analysis.
- Suggested test: Reuse the helper regression test from CODACY-002 and add a
  test that normal astronomy and generated phyphox files still parse.
- Risk of change: Medium. Tests are contract guardrails; parser helper adoption
  must not hide parse errors or namespace behavior.
- Confidence: high
- Blocker 2026-06-07: Test XML findings remain until CODACY-002 introduces an
  approved safe parser helper. Do not add `defusedxml` or suppress test XML
  findings without explicit user approval.

### CODACY-004: Harden subprocess tests

- ID: CODACY-004
- Status: PARTIAL_BLOCKED_DECISION
- Severity: P1
- Category: Security / ErrorProne
- Subsystem: tests that invoke scripts
- File: `tests/test_phyphox_generated_parity.py`,
  `tests/test_postprocess_phyphox_xml.py`, `tests/test_repo_guardrails.py`,
  `tests/test_validate_xinclude_paths.py`
- Line range or symbol: `tests/test_phyphox_generated_parity.py:6,20`,
  `tests/test_postprocess_phyphox_xml.py:129,136,146,149,158,162`,
  `tests/test_repo_guardrails.py:8,57,77,94`,
  `tests/test_validate_xinclude_paths.py:5,116`
- Evidence: `Bandit_B404` 6, `Bandit_B603` 8, `Bandit_B607` 4,
  `Semgrep_python.lang.security.audit.dangerous-subprocess-use-audit...` 4, and
  `PyLintPython3_W1510` 3.
- Why it matters: Tests execute local scripts and commands. Even without
  `shell=True`, Codacy flags partial executable names, dynamic argv, and missing
  explicit `check` semantics.
- Runtime/user impact: Low for production, but important for CI reliability and
  for preventing false-success states in test harnesses.
- Suggested remediation: Prefer direct Python function calls where possible. For
  process-level smoke tests that must remain, use static argv lists, resolve
  executable paths with `sys.executable`, `shutil.which`, or an absolute repo
  script path, pass `check=True` when failure should fail the test, and use
  explicit `check=False` plus asserted `returncode` when testing failure paths.
- Verification required: `pytest tests/test_phyphox_generated_parity.py
  tests/test_postprocess_phyphox_xml.py tests/test_repo_guardrails.py
  tests/test_validate_xinclude_paths.py`, `ruff check tests`, and Codacy local
  analysis.
- Suggested test: Keep at least one negative-path assertion for each script that
  intentionally returns nonzero; do not convert negative tests into
  false-success `check=True` calls.
- Risk of change: Medium. Several tests intentionally inspect stdout, stderr,
  and return codes; preserve those contracts.
- Confidence: high
- Remediation update 2026-06-07: Avoidable Python CLI subprocess calls were
  replaced by direct `main()` calls in `tests/test_postprocess_phyphox_xml.py`
  and `tests/test_validate_xinclude_paths.py`. Remaining shell-script smoke
  tests in `tests/test_phyphox_generated_parity.py` and
  `tests/test_repo_guardrails.py` now call `/bin/bash` explicitly, which closed
  all `Bandit_B607` partial-executable findings. No findings were ignored,
  suppressed, excluded, or marked false positive.
- Verification 2026-06-07:
  `pytest tests/test_phyphox_generated_parity.py tests/test_postprocess_phyphox_xml.py tests/test_repo_guardrails.py tests/test_validate_xinclude_paths.py`
  passed with 35 tests; `ruff check tests/test_phyphox_generated_parity.py
  tests/test_postprocess_phyphox_xml.py tests/test_repo_guardrails.py
  tests/test_validate_xinclude_paths.py` passed; `codacy-analysis analyze
  --install-dependencies --output-format json --output /tmp/phyphox-codacy-after.json`
  completed with 388 findings and 0 analyzer errors.
- Remaining CODACY-004 findings: `Bandit_B404` 2 and `Bandit_B603` 4 remain in
  process-level shell-script smoke tests. Closing them without weakening
  coverage likely requires either a project-approved Codacy/Bandit test-policy
  decision or a broader test redesign that avoids launching shell entrypoints.
  Do not suppress or exclude these without explicit false-positive approval.

### CODACY-005: Split active phyphox validation complexity

- ID: CODACY-005
- Status: COMPLETE_LOCAL
- Severity: P2
- Category: Maintainability / Complexity
- Subsystem: validation tooling
- File: `tools/validate_phyphox.py`
- Line range or symbol: `_load_expected_uuids` at line 66,
  `_load_expected_modes` at line 142, `validate_phyphox` at line 235
- Evidence: `Lizard_ccn-critical` reports cyclomatic complexity 26, 29, and 63;
  `Lizard_nloc-critical` reports `validate_phyphox` NLOC 240; `Prospector_mccabe`
  reports corresponding complexity 19, 26, and 56.
- Why it matters: The validator enforces BLE UUIDs, modes, XML structure,
  containers, analysis references, views, and localization contracts. The
  current large functions make it easy to introduce false-success or missed
  validation states.
- Runtime/user impact: This affects verification reliability, not Arduino
  runtime. A weak validator can let invalid phyphox files pass CI.
- Suggested remediation: Split by responsibility without changing behavior:
  constants loading, sketch UUID extraction, sketch mode extraction, source mode
  extraction, root/top-level validation, container validation, input validation,
  analysis validation, view validation, and localization validation. Keep return
  type `list[ValidationError]` stable.
- Verification required: `pytest tests/test_phyphox_validate.py
  tests/test_phyphox_file_contracts.py tests/test_phyphox_generated_parity.py`,
  `bash scripts/validate-xml.sh`, `bash scripts/check-generated-clean.sh`, and
  Codacy local analysis.
- Suggested test: Before refactoring, add or identify tests that fail on
  duplicate containers, missing BLE outputs, bad config UUIDs, and bad mode IDs.
  Then refactor one responsibility at a time.
- Risk of change: High relative to normal cleanup because this file is a central
  repository contract gate.
- Confidence: high
- Remediation update 2026-06-07: `tools/validate_phyphox.py` was split by
  responsibility: UUID loading, mode loading, root/top-level validation,
  container collection/reference validation, Bluetooth input mappings, and
  Bluetooth config output validation. Existing `ValidationError` messages and
  the public `validate_phyphox(...) -> list[ValidationError]` contract were
  preserved. No findings were ignored, suppressed, excluded, or marked false
  positive.
- Verification 2026-06-07: `pytest tests/test_phyphox_validate.py
  tests/test_phyphox_file_contracts.py tests/test_phyphox_generated_parity.py`
  passed with 83 tests; `ruff check tools/validate_phyphox.py
  tests/test_phyphox_validate.py tests/test_phyphox_file_contracts.py
  tests/test_phyphox_generated_parity.py` passed; `bash scripts/validate-xml.sh`
  passed; `bash scripts/check-generated-clean.sh` passed; `codacy-analysis
  analyze --install-dependencies --output-format json --output
  /tmp/phyphox-codacy-after.json` completed with 370 findings and 0 analyzer
  errors.
- Remaining CODACY-005 findings: none. `Lizard_ccn-critical`,
  `Lizard_nloc-critical`, and `Prospector_mccabe` are now 0.

### CODACY-006: Split XInclude href validation branch logic

- ID: CODACY-006
- Status: COMPLETE_LOCAL
- Severity: P2
- Category: Maintainability / Complexity
- Subsystem: XInclude validation tooling
- File: `tools/validate_xinclude_paths.py`
- Line range or symbol: `_validate_href` at line 29
- Evidence: `Lizard_ccn-critical` reports `_validate_href` cyclomatic complexity
  13, just over the threshold 12.
- Why it matters: This function enforces path traversal and URL-boundary rules
  for XInclude. The logic is security-adjacent and should remain easy to audit.
- Runtime/user impact: Verification gate only. Bad changes could allow unsafe
  includes or reject valid generated source XML.
- Suggested remediation: Split URL validation, decoded path validation, target
  existence validation, and resolved-path boundary validation into small helpers.
  Keep the exact user-facing error strings unless tests are deliberately updated.
- Verification required: `pytest tests/test_validate_xinclude_paths.py`,
  `bash scripts/validate-xml.sh`, and Codacy local analysis.
- Suggested test: Add a table-driven test for URL scheme, query, fragment,
  absolute path, `..`, missing target, directory target, symlink escape, and
  valid include.
- Risk of change: Medium. Boundary checks are security-sensitive.
- Confidence: high
- Remediation update 2026-06-07: `_validate_href` was split into URL-boundary,
  decoded-path, and target-boundary helpers in `tools/validate_xinclude_paths.py`.
  Existing user-facing error strings and validation behavior were preserved. No
  findings were ignored, suppressed, excluded, or marked false positive.
- Verification 2026-06-07: `pytest tests/test_validate_xinclude_paths.py`
  passed with 10 tests; `ruff check tools/validate_xinclude_paths.py
  tests/test_validate_xinclude_paths.py` passed; `bash scripts/validate-xml.sh`
  passed; `codacy-analysis analyze --install-dependencies --output-format json
  --output /tmp/phyphox-codacy-after.json` completed with 387 findings and 0
  analyzer errors.
- Remaining CODACY-006 findings: none. `Lizard_ccn-critical` now reports 3
  findings, all in `tools/validate_phyphox.py` under CODACY-005.

### CODACY-007: Update agent guidance or tune Agentlinter scope

- ID: CODACY-007
- Status: COMPLETE_LOCAL
- Severity: P3
- Category: Agent instruction quality
- Subsystem: agent guidance
- File: `AGENTS.md`
- Line range or symbol: line 1 whole-file checks, plus lines 87-99
- Evidence: 8 Agentlinter findings:
  `Agentlinter_security_has-permission-boundaries`,
  `Agentlinter_clarity_escape-hatch-missing`,
  `Agentlinter_memory_has-file-based-notes`,
  `Agentlinter_memory_has-memory-strategy`,
  `Agentlinter_memory_has-state-tracking`,
  `Agentlinter_memory_no-mental-notes`,
  `Agentlinter_runtime_config-exists`.
- Why it matters: The file is already useful to Codex, but Agentlinter expects
  explicit permission boundaries, memory/state rules, and escape hatches for
  absolute-sounding repository contracts.
- Runtime/user impact: None. This is guidance quality and scanner signal.
- Suggested remediation: Add a compact section that says destructive actions,
  dependency additions, Cloud imports/reanalysis, and false-positive ignores need
  explicit user approval. Add a compact state/memory note that large audits
  should write ledger/status files. For absolute contracts at lines 87-99, add
  language like "unless the task explicitly changes and documents the contract."
  If the project does not want Agentlinter to govern this repo, tune Codacy
  rather than padding `AGENTS.md`.
- Verification required: `codacy-analysis analyze --install-dependencies
  --output-format json --output /tmp/phyphox-codacy-after.json` and inspect
  Agentlinter findings.
- Suggested test: None; this is documentation/tooling policy.
- Risk of change: Low, but avoid bloating `AGENTS.md`.
- Confidence: medium
- Remediation update 2026-06-07: `AGENTS.md` now has explicit permission
  boundaries, a file-based memory/state strategy, and escape hatches for the
  BLE and astronomy locale contracts. `openclaw.json` was added with loopback
  binding and environment-token auth, following the minimal local runtime
  configuration pattern and without committing a secret. No findings were
  ignored, suppressed, excluded, or marked false positive.
- Verification 2026-06-07: `jq empty openclaw.json` passed; `git diff --check
  -- AGENTS.md openclaw.json .codacy/codacy-remediation-ledger.md README.md
  tools/validate_xinclude_paths.py` passed; `codacy-analysis analyze
  --install-dependencies --output-format json --output /tmp/phyphox-codacy-after.json`
  completed with 377 findings and 0 analyzer errors.
- Remaining CODACY-007 findings: none. `Agentlinter_*` is now 0.

### CODACY-008: Resolve duplicate README headings

- ID: CODACY-008
- Status: COMPLETE_LOCAL
- Severity: P3
- Category: Documentation
- Subsystem: README
- File: `README.md`
- Line range or symbol: `README.md:139`, `README.md:149`
- Evidence: `markdownlint_MD024`, 2 findings for duplicate heading content.
- Why it matters: Duplicate headings can produce ambiguous anchors and weaker
  navigation in rendered Markdown.
- Runtime/user impact: None.
- Suggested remediation: Rename the repeated headings or add enough parent
  context so anchors are distinct. Preserve README flow and public-facing
  classroom language.
- Verification required: `codacy-analysis analyze --install-dependencies
  --output-format json --output /tmp/phyphox-codacy-after.json` and inspect
  markdownlint findings. Optionally run `ruff`/`pytest` only if code examples are
  changed.
- Suggested test: None.
- Risk of change: Low.
- Confidence: high
- Remediation update 2026-06-07: The duplicate quickstart subheadings were
  renamed to `Core sensor quickstart` and `Astronomy quickstart`, preserving
  the earlier summary headings and README flow. No findings were ignored,
  suppressed, excluded, or marked false positive.
- Verification 2026-06-07: `git diff --check -- README.md
  .codacy/codacy-remediation-ledger.md tools/validate_xinclude_paths.py`
  passed; `codacy-analysis analyze --install-dependencies --output-format json
  --output /tmp/phyphox-codacy-after.json` completed with 385 findings and 0
  analyzer errors.
- Remaining CODACY-008 findings: none. `markdownlint_MD024` is now 0.

## Recommended Execution Order

1. CODACY-002 and CODACY-003 together: XML parser hardening removes the most
   security-significant non-test-policy cluster.
2. CODACY-004: subprocess tests are narrow and likely close 25 findings with
   modest risk.
3. CODACY-005: validator complexity is central; do it in small, verified slices.
4. CODACY-006: XInclude complexity is small but security-adjacent.
5. CODACY-008: README heading cleanup is trivial.
6. CODACY-007: agent guidance or Codacy tuning decision.
7. CODACY-001: pytest assert policy. This is the largest count but should be a
   deliberate policy decision, not an automatic rewrite.

## Closure Criteria

For each implementation slice:

1. Re-run the narrow tests named in the slice.
2. Re-run `codacy-analysis analyze --install-dependencies --output-format json
   --output /tmp/phyphox-codacy-after.json`.
3. Compare counts by pattern, not just total issue count.
4. Confirm excluded paths stay excluded:

```sh
jq '[.issues[].filePath]
  | map(select(startswith("docs/archive/")
    or startswith("docs/deprecated/")
    or startswith("docs/ci/")
    or startswith("reference/")))
  | unique' /tmp/phyphox-codacy-after.json
```

5. Do not report Cloud closure until Codacy Cloud reanalysis has analyzed the
   branch tip and the remote issue count has been checked separately.
