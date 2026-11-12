# Decision and work log

**Final status (2026-11-12): all acceptance checks pass.** 32 tests pass, both fixtures match the README self-check, `git diff --check` is clean, and the supplied inputs are unchanged. Details are in Appendix A (Validation 8) and the outputs in Appendix B.

## Priorities
1. **Tenant isolation (P2).** It was the only defect that exposed another tenant's data, so it was reproduced first.
2. **Parseable CSV and cell encoding (P5, P3).** This is what the teammate's parser saw.
3. **Formula neutralization for both consumer policies (P4)**, including `row_id`.
4. **Nonmutation and repeatability (P4, P6).**
5. **A reusable round-trip checker** applied unchanged to both fixtures (P6).
6. **P1 validation controls** and the CLI fatal-error contract.

Order of work, visible in git: review, then one failing test per defect, then the checker, the fix, the P1 controls, the documentation and a final verification pass.

## Deferred
- **Testing in real spreadsheet applications.** Out of scope. C7 stays false and the limits are documented.
- **Splitting commit `4e0672d`.** It imports the unmodified starter together with the first test. History was not rewritten, because that would need a force-push. `4e0672d` is the starter baseline: `git diff 4e0672d HEAD -- app.py` shows the complete fix.
- **Reformatting the fix.** It is correct and readable; reformatting would only add diff noise.
- **A command-line wrapper for the checker.** It is a function any `unittest` test can call (`run-guide.md` §5).

## Obstacle and response
- **Obstacle:** the two consumer policies make the same cell correct in different ways. R06 ` =not-direct` and `\t+not-direct` must stay unchanged under `direct` but get one apostrophe under `trim-space-tab`. A leading newline must never be skipped. One hard-coded expected CSV could not cover both.
- **Response:**
  - One `encode_cell(value, policy)` helper used for every column.
  - Tests for each policy, including newline and apostrophe controls.
  - The checker derives its expectations from `payload["policy"]`.
  - Literal tables pin R06 for both fixtures.

## Validation and refinement
1. **Failing-first.** The 20 tests committed before the fix produced 15 failures on the starter. All pass after the fix (Appendix B.1 and B.2).
2. **Validation caused a code refinement.** During the final review an adversarial check found that 100,000-level nested JSON crashed the CLI with a traceback and exit 1, but P1 requires exit 2. I added a failing test first (`AssertionError: 1 != 2`, Appendix B.3), then added `RecursionError` to the fatal-error handler in `main()`. The test passes and the fixture output is byte-for-byte unchanged.
3. **Checker refinement.** The checker computes expected cells with the same algorithm as `encode_cell`, so a shared misreading of P4 would go unnoticed. I added:
   - literal README self-check values (summary, audit, R01–R08 order, every primary cell);
   - an exact reconciliation of the second fixture;
   - a test proving the checker rejects 5 kinds of tampered result.

   The checker's foreign-content check compared encoded IDs with raw IDs. It now checks the raw and encoded IDs, titles and notes, and runs before the full comparison, so a leak fails with a clear message. On the starter it reports `Foreign row at position 9 entered the audit.`
4. **Review refinement.** C7 changed from "Not verifiable" (first review commit) to "False": the checks test no spreadsheet at all, and P6 rules out a universal guarantee.

## Second fixture (README task 5)
- The checker was applied **unchanged** to `secondary.json` and passes.
- **Reconciliation:** 3 of 24 data cells change; the other 21 are identical. `test_secondary_changes_exactly_three_cells` asserts this.
  - R01.note: `comma, note` → `comma, revised note` (revised fixture text)
  - R06.title: ` =not-direct` → `' =not-direct` (P4 trim-space-tab skips the space)
  - R06.note: `\t+not-direct` → `'\t+not-direct` (P4 trim-space-tab skips the tab)
- **Code refinement needed for the second fixture: none.** The fix already handled both policies. Primary was re-run after every change and passes.
- **Guarantee demonstrated.** Tested on both fixtures, an empty input, a constructed boundary and 400 generated rows:
  - `csv.reader` returns exactly the header and the policy-transformed cells in input order;
  - the audit and summary are exact;
  - no foreign ID or content reaches the CSV or the audit;
  - reversing the encoding with the audit restores every original value;
  - the input is never modified, and repeated calls are identical.
- **Limits of the PR's spreadsheet claim.** No spreadsheet application was opened. P4 leaves a leading newline, carriage return, non-breaking space or full-width `＝` untouched (verified), so nothing here shows safety "in every spreadsheet application".

## Known limits
- The exporter implements the synthetic policy only. No spreadsheet behaviour is claimed.
- The tests must run from the repository root, as in the README commands, because they import `app` from the current directory.

## Next step
An independent review of this branch, then integration tests in the consumer's real environment, including the spreadsheet applications they actually use.

---

# Appendix A: chronological validation record

Written while the work progressed. Placeholders were filled and evidence added on 2026-11-12.

## Validation 1 — Tenant Isolation

- Test: `test_export_includes_only_exact_tenant`
- Expected: only R01 should be exported.
- Actual: R01 and X01 were exported (`Lists differ: ['R01', 'X01'] != ['R01']`).
- Result: FAILED as expected.
- Cause: substring matching instead of exact tenant comparison.
- Fixture evidence: for `primary.json` the starter exported X01 (`FOREIGN-SENTINEL-ONE`), listed X01 in `neutralized_cells` and reported 9 exported and 1 foreign row.
- Next action: fix tenant filtering.

## Validation 2 — CSV Serialization

### Test 1: Special Characters
- Expected: the CSV reader recovers the original columns and values.
- Actual: commas and embedded newlines produce incorrect records. With `primary.json`, the starter's CSV parses as 11 records instead of 9.
- Result: FAILED as expected.
- Cause: manual CSV string concatenation.

### Test 2: CRLF Record Endings
- Expected: CSV records use `\r\n`.
- Actual: the CSV uses `\n`.
- Result: FAILED as expected.
- Cause: incorrect record separator.

## Validation 3 — Cell Encoding

### Test 1: Null, Empty and Literal Backslash-N
- Expected: None, empty strings and a literal `\N` remain distinguishable.
- Actual: null becomes an empty string (`['R01', '', ''] != ['R01', '\\N', '']`), and a literal backslash-N is not escaped.
- Result: FAILED as expected.
- Cause: incorrect null handling and missing backslash escaping.

### Test 2: Backslashes and Apostrophes
- Expected: backslashes are doubled and apostrophes preserved.
- Actual: backslashes remain unchanged and apostrophes are doubled (`O''Brien`).
- Result: FAILED as expected.
- Cause: incorrect cell encoding implementation.

## Validation 4 — Formula Neutralization

### Test 1: Direct Policy
- Expected: all four formula triggers are neutralized only when they appear at character zero, in every exported column.
- Actual: the implementation only checks the equals sign and ignores `row_id`.
- Result: FAILED as expected.
- Cause: incomplete formula detection.

### Test 2: Trim-Space-Tab Policy
- Expected: leading ASCII spaces and tabs are skipped when checking formula triggers.
- Actual: leading spaces and tabs are not handled.
- Result: FAILED as expected.
- Cause: the selected consumer policy is not implemented.

### Test 3: Newlines and Existing Apostrophes
- Expected: newlines are not skipped, and apostrophe-prefixed values are not neutralized again.
- Actual: no cells were reported as neutralized.
- Result: PASSED, on the starter as well. This is a legitimate control.

## Validation 5 — Input Immutability and Repeatability

### Test 1: Original Input Immutability
- Expected: the original payload is unchanged after exporting.
- Actual: the exporter modifies title and note values in the original rows.
- Result: FAILED as expected.
- Cause: direct assignment to the original row with `row[column] = value`.

### Test 2: Repeatability
- Expected: two calls with the same payload produce identical results.
- Actual: the second export differs (`'=SUM(1,2)` became `''=SUM(1,2)`) because the first export modified the input.
- Result: FAILED as expected.
- Cause: the exporter does not preserve the original input.

## Validation 6 — Reusable CSV Round-Trip Checker

### Implementation
- A reusable checker that accepts the original payload and the export result.
- Independent expected-cell encoding.
- CSV parsing and exact record validation.
- Header, column count, row count and order checks.
- Audit and summary verification.
- Reverse decoding using the audit information.

### Test Cases
- Primary fixture.
- Secondary fixture.
- Empty input.
- Constructed boundary case.
- Repeated exports using the same object.
- Comparison of changed and unchanged cells between the fixtures.

### Result before the fix
All 6 checker tests failed on the unchanged starter. The suite at this commit gave `Ran 20 tests`, `FAILED (failures=15)` (Appendix B.1). `app.py` was not changed at this point.

### Next Action
Repair the exporter and run the complete acceptance suite.

## Repair 1 — Policy-Compliant CSV Export

### Changes
- Kept the existing P1 input validation.
- Replaced substring tenant matching with exact equality.
- Added a reusable `encode_cell()` function.
- Implemented null and backslash encoding.
- Implemented both formula-neutralization policies.
- Applied the encoding to all exported columns.
- Replaced manual CSV concatenation with `csv.writer`.
- Configured CRLF record endings and `QUOTE_MINIMAL`.
- Removed modifications to the original input objects.

### Validation
- Ran the complete automated test suite.
- Verified the primary and secondary fixtures.
- Checked the audit and summary counts.
- Checked input immutability and repeatability.

### Result
All 20 tests at the fix commit `bcd472e` pass; full output in Appendix B.2. The 15 tests that failed on the starter now pass, and the 5 controls still pass.

### Known Limitations
- Formula neutralization implements the synthetic assessment policy.
- It does not establish universal spreadsheet safety.

## Validation 7 — Input Validation and Error Handling

### Tests
- Invalid tenant values.
- Invalid policy values.
- Non-list rows.
- Invalid row structures.
- Missing and empty required fields.
- Duplicate row IDs, including duplicates across tenants.
- Valid null and empty cell values.
- Validation of foreign rows before tenant selection.
- CLI exit code and error output.
- No partial stdout on fatal errors.
- No cell-value leakage in error messages.

### Expected Results
- Invalid inputs raise `ValueError`.
- Row errors identify only the one-based row position.
- Invalid input exits with code 2.
- Fatal errors produce no stdout.
- Error messages do not reveal cell values.
- Valid null and empty values are accepted.

### Result
All 7 tests pass. They also pass on the unmodified starter (re-run on 2026-11-12), so they are **controls**. The AI patch's P1 validation was already correct, and these tests protect it from regressions. The CLI test confirms that `error: invalid row 2` is the whole stderr: the sentinels `VALID_TITLE_SECRET`, `FOREIGN_TITLE_SECRET` and `FOREIGN_ROW_SECRET` do not appear.

### Conclusion
P1 validation behavior is tested.

## Validation 8 — Final Acceptance Review (filled 2026-11-12)

### Policy Review
- P1: input validation verified (controls, plus the deeply nested JSON fix in Validation 9).
- P2: exact tenant isolation verified.
- P3: cell encoding verified.
- P4: both formula policies verified.
- P5: CSV serialization verified.
- P6: repeatability and round-trip behavior verified.

### AI Claims
- C1–C5: false.
- C6: confirmed (smoke checks only; not evidence of correctness).
- C7: false.

### Fixture Verification
- Primary fixture: exit 0. Summary `{"exported_rows": 8, "foreign_rows": 2, "input_rows": 10, "neutralized_cells": 4, "redacted_cells": 0}`. R01–R08 exported in order. R02–R05 titles neutralized. The checker passes.
- Secondary fixture: exit 0. Summary `{"exported_rows": 8, "foreign_rows": 2, "input_rows": 10, "neutralized_cells": 6, "redacted_cells": 0}`. R02–R05 titles plus R06 title and note neutralized. The checker passes unchanged.
- Both fixtures use the same reusable checker.
- Changed and unchanged cells were compared: exactly 3 changed (R01.note, R06.title, R06.note) and 21 unchanged.

### Quality Checks
- Automated test suite: `Ran 32 tests in 2.131s`, `OK`.
- `git diff --check`: clean. It first reported trailing whitespace at `app.py:68` and a blank line at the end of this file; both were fixed.
- Original input fixtures preserved: `inputs/*`, `README.md`, `.gitignore` and `tests/app_test.py` are byte-identical to the exercise zip.

### Known Limitations
The implementation follows the synthetic export policy. Universal spreadsheet safety is not guaranteed.

### Final Status
All acceptance checks passed.

## Validation 9 — Final review pass (2026-11-12)

A final review of the whole submission against the README (with Claude Code; see `ai-use-note.md`):

- **Deeply nested JSON (P1).** Added `test_cli_rejects_excessively_nested_json`. It failed first (Appendix B.3). Repair 2 added `RecursionError` to the fatal-error handler in `main()`; it now exits 2 with `error: Stack overflow (...) while decoding a JSON array from a unicode string`.
- **Checker.** The foreign-content check now covers raw and encoded IDs, titles and notes, and runs before the full comparison.
- **New tests in `round_trip_checker_test.py`:**
  - `test_fixtures_match_readme_self_check`
  - `test_primary_matches_literal_records`
  - `test_secondary_changes_exactly_three_cells` (replaces the weaker `test_secondary_changes_some_cells_and_preserves_others`)
  - `test_checker_rejects_tampered_results`
- **Optional stretch.** `tests/generated_cells_test.py` runs 200 generated rows (fixed seed) per policy through the checker.
- **New tests on the starter.** On the unmodified starter, every round-trip checker test except the tamper test fails (9 failures, counting subtests), and the generated test fails for both policies. So the new tests detect the original defects (Appendix B.4).
- **Cleanup.** Removed trailing whitespace, sorted the imports, used two blank lines between functions, and filled every documentation placeholder with executed results.

---

# Appendix B: test output

## B.1 Failing-first: tests from commit `a7c1ff6` (before the fix) on the starter

Re-run on 2026-11-12 with the command in `run-guide.md` §4. The code at that commit is unchanged, so the result is the same as before the fix.

```text
FAIL: test_backslashes_are_doubled_and_apostrophes_preserved
FAIL: test_null_empty_and_literal_backslash_n_remain_distinct
FAIL: test_writer_preserves_commas_quotes_and_embedded_newlines
FAIL: test_writer_uses_crlf_record_endings
FAIL: test_direct_policy_checks_all_four_triggers
FAIL: test_trim_space_tab_policy_skips_only_spaces_and_tabs
FAIL: test_export_does_not_modify_original_payload
FAIL: test_repeated_exports_produce_identical_results
FAIL: test_constructed_boundary_case
FAIL: test_empty_input
FAIL: test_primary_fixture
FAIL: test_secondary_changes_some_cells_and_preserves_others
FAIL: test_secondary_fixture
FAIL: test_two_exports_of_same_object_are_identical
FAIL: test_export_includes_only_exact_tenant
Ran 20 tests in 2.204s
FAILED (failures=15)
```

First assertion message of selected failures:

```text
test_export_includes_only_exact_tenant -> AssertionError: Lists differ: ['R01', 'X01'] != ['R01']
test_null_empty_and_literal_backslash_n_remain_distinct -> AssertionError: Lists differ: ['R01', '', ''] != ['R01', '\\N', '']
test_writer_preserves_commas_quotes_and_embedded_newlines -> AssertionError: Lists differ: [... ['R01', 'Product', ' "Deluxe"', 'First line'], ['Second line']] != [... ['R01', 'Product, "Deluxe"', 'First line\nSecond line']]
test_empty_input -> AssertionError: 'row_id,title,note\n' != 'row_id,title,note\r\n'
test_export_does_not_modify_original_payload -> AssertionError: {... 'title': "'=SUM(1,2)", 'note': "It''s a test"} ...} != {... 'title': '=SUM(1,2)', 'note': "It's a test"} ...}
```

## B.2 After the fix: tests at commit `bcd472e`

Re-run on 2026-11-12 from a clean export of `bcd472e`.

```text
testCli_whenHelpRequested_returnsUsage ... ok
testCli_whenInputMissing_reportsReadableError ... ok
testCli_whenJsonMalformed_reportsReadableError ... ok
testCli_whenPrimaryRead_returnsExportEnvelope ... ok
test_backslashes_are_doubled_and_apostrophes_preserved ... ok
test_null_empty_and_literal_backslash_n_remain_distinct ... ok
test_writer_preserves_commas_quotes_and_embedded_newlines ... ok
test_writer_uses_crlf_record_endings ... ok
test_direct_policy_checks_all_four_triggers ... ok
test_trim_policy_does_not_skip_newlines_or_existing_apostrophes ... ok
test_trim_space_tab_policy_skips_only_spaces_and_tabs ... ok
test_export_does_not_modify_original_payload ... ok
test_repeated_exports_produce_identical_results ... ok
test_constructed_boundary_case ... ok
test_empty_input ... ok
test_primary_fixture ... ok
test_secondary_changes_some_cells_and_preserves_others ... ok
test_secondary_fixture ... ok
test_two_exports_of_same_object_are_identical ... ok
test_export_includes_only_exact_tenant ... ok

Ran 20 tests in 1.902s

OK
```

## B.3 Failing-first: deeply nested JSON, before Repair 2 (2026-11-12)

```text
test_cli_rejects_excessively_nested_json ... FAIL
FAIL: test_cli_rejects_excessively_nested_json (input_validation_test.InputValidationTests.test_cli_rejects_excessively_nested_json)
    self.assertEqual(process.returncode, 2)
AssertionError: 1 != 2
Ran 8 tests in 0.819s
FAILED (failures=1)
```

## B.4 New tests run against the unmodified starter (2026-11-12)

```text
round_trip_checker_test.py: Ran 9 tests, FAILED (failures=9)
  (test_checker_rejects_tampered_results passes, as it should: tampered copies of a wrong result are rejected too)
generated_cells_test.py: FAILED for policy='direct' and policy='trim-space-tab'
test_primary_fixture -> AssertionError: 'X01' unexpectedly found in {'R02', 'X01'} : Foreign row at position 9 entered the audit.
```

## B.5 Final run after all changes (2026-11-12, Python 3.14.9)

```text
$ python3 -B -m unittest discover -s tests -p '*_test.py'
Ran 32 tests in 2.131s

OK
```
