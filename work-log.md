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
