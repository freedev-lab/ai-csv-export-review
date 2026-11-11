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
