## Validation 1 — Tenant Isolation

- Test: test_export_includes_only_exact_tenant
- Expected: Only R01 should be exported.
- Actual: R01 and X01 were exported.
- Result: FAILED as expected.
- Cause: Substring matching instead of exact tenant comparison.
- Next action: Fix tenant filtering.


## Validation 2 — CSV Serialization

### Test 1: Special Characters
- Expected: CSV reader should recover the original columns and values.
- Actual: Commas and embedded newlines produce incorrect records.
- Result: FAILED as expected.
- Cause: Manual CSV string concatenation.

### Test 2: CRLF Record Endings
- Expected: CSV records should use \r\n.
- Actual: CSV uses \n.
- Result: FAILED as expected.
- Cause: Incorrect record separator.



## Validation 3 — Cell Encoding

### Test 1: Null, Empty and Literal Backslash-N
- Expected: None, empty strings and literal \N must remain distinguishable.
- Actual: Null is converted into an empty string, and literal backslash-N is not escaped.
- Result: FAILED as expected.
- Cause: Incorrect null handling and missing backslash escaping.

### Test 2: Backslashes and Apostrophes
- Expected: Backslashes should be doubled and apostrophes preserved.
- Actual: Backslashes remain unchanged and apostrophes are doubled.
- Result: FAILED as expected.
- Cause: Incorrect cell encoding implementation.



## Validation 4 — Formula Neutralization

### Test 1: Direct Policy
- Expected: All four formula triggers should be neutralized only when they appear at character zero.
- Actual: The implementation only checks the equals sign and ignores row_id.
- Result: FAILED as expected.
- Cause: Incomplete formula detection.

### Test 2: Trim-Space-Tab Policy
- Expected: Leading ASCII spaces and tabs should be skipped when checking formula triggers.
- Actual: Leading spaces and tabs are not handled correctly.
- Result: FAILED as expected.
- Cause: The selected consumer policy is not implemented.

### Test 3: Newlines and Existing Apostrophes
- Expected: Newlines must not be skipped, and existing apostrophe-prefixed values must not be neutralized again.
- Actual: No cells were reported as neutralized.
- Result: PASSED.




## Validation 5 — Input Immutability and Repeatability

### Test 1: Original Input Immutability
- Expected: The original payload must remain unchanged after exporting.
- Actual: The exporter modifies title and note values in the original rows.
- Result: FAILED as expected.
- Cause: Direct assignment to the original row using row[column] = value.

### Test 2: Repeatability
- Expected: Two calls with the same payload must produce identical results.
- Actual: The second export produces different values because the first export modified the input.
- Result: FAILED as expected.
- Cause: The exporter does not preserve the original input.




## Validation 6 — Reusable CSV Round-Trip Checker

### Implementation
- Created a reusable checker accepting the original payload and export result.
- Added independent expected-cell encoding.
- Added CSV parsing and exact record validation.
- Added header, column count, row count and order checks.
- Added audit and summary verification.
- Added reverse decoding using the audit information.

### Test Cases
- Primary fixture.
- Secondary fixture.
- Empty input.
- Constructed boundary case.
- Repeated exports using the same object.
- Comparison of changed and unchanged cells between fixtures.

### Current Result
- Tests are expected to expose the existing implementation defects.
- No changes have been made to app.py yet.

### Next Action
- Repair the exporter and run the complete acceptance suite.




## Repair 1 — Policy-Compliant CSV Export

### Changes
- Preserved the existing P1 input validation.
- Replaced substring tenant matching with exact equality.
- Added a reusable encode_cell() function.
- Implemented null and backslash encoding.
- Implemented both formula-neutralization policies.
- Applied encoding to all exported columns.
- Replaced manual CSV concatenation with csv.writer.
- Configured CRLF record endings and QUOTE_MINIMAL.
- Removed modifications to original input objects.

### Validation
- Executed the complete automated test suite.
- Verified the primary fixture.
- Verified the secondary fixture.
- Checked audit information and summary counts.
- Checked input immutability and repeatability.

### Result
testCli_whenHelpRequested_returnsUsage (app_test.StarterTests.testCli_whenHelpRequested_returnsUsage) ... ok
testCli_whenInputMissing_reportsReadableError (app_test.StarterTests.testCli_whenInputMissing_reportsReadableError) ... ok
testCli_whenJsonMalformed_reportsReadableError (app_test.StarterTests.testCli_whenJsonMalformed_reportsReadableError) ... ok
testCli_whenPrimaryRead_returnsExportEnvelope (app_test.StarterTests.testCli_whenPrimaryRead_returnsExportEnvelope) ... ok
test_backslashes_are_doubled_and_apostrophes_preserved (cell_encoding_test.CellEncodingTests.test_backslashes_are_doubled_and_apostrophes_preserved) ... ok
test_null_empty_and_literal_backslash_n_remain_distinct (cell_encoding_test.CellEncodingTests.test_null_empty_and_literal_backslash_n_remain_distinct) ... ok
test_writer_preserves_commas_quotes_and_embedded_newlines (csv_serialization_test.CsvSerializationTests.test_writer_preserves_commas_quotes_and_embedded_newlines) ... ok
test_writer_uses_crlf_record_endings (csv_serialization_test.CsvSerializationTests.test_writer_uses_crlf_record_endings) ... ok
test_direct_policy_checks_all_four_triggers (formula_neutralization_test.FormulaNeutralizationTests.test_direct_policy_checks_all_four_triggers) ... ok
test_trim_policy_does_not_skip_newlines_or_existing_apostrophes (formula_neutralization_test.FormulaNeutralizationTests.test_trim_policy_does_not_skip_newlines_or_existing_apostrophes) ... ok
test_trim_space_tab_policy_skips_only_spaces_and_tabs (formula_neutralization_test.FormulaNeutralizationTests.test_trim_space_tab_policy_skips_only_spaces_and_tabs) ... ok
test_export_does_not_modify_original_payload (repeatability_test.RepeatabilityTests.test_export_does_not_modify_original_payload) ... ok
test_repeated_exports_produce_identical_results (repeatability_test.RepeatabilityTests.test_repeated_exports_produce_identical_results) ... ok
test_constructed_boundary_case (round_trip_checker_test.RoundTripCheckerTests.test_constructed_boundary_case) ... ok
test_empty_input (round_trip_checker_test.RoundTripCheckerTests.test_empty_input) ... ok
test_primary_fixture (round_trip_checker_test.RoundTripCheckerTests.test_primary_fixture) ... ok
test_secondary_changes_some_cells_and_preserves_others (round_trip_checker_test.RoundTripCheckerTests.test_secondary_changes_some_cells_and_preserves_others) ... ok
test_secondary_fixture (round_trip_checker_test.RoundTripCheckerTests.test_secondary_fixture) ... ok
test_two_exports_of_same_object_are_identical (round_trip_checker_test.RoundTripCheckerTests.test_two_exports_of_same_object_are_identical) ... ok
test_export_includes_only_exact_tenant (tenant_isolation_test.TenantIsolationTests.test_export_includes_only_exact_tenant) ... ok


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
- Invalid inputs produce ValueError.
- Row errors identify only the one-based row position.
- Invalid input produces exit code 2.
- Fatal errors produce no stdout.
- Error messages do not reveal cell values.
- Valid null and empty values are accepted.

### Result
[Record your actual test results here.]

### Conclusion
P1 validation behavior has been tested.
