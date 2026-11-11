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