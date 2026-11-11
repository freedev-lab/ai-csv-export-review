## Validation 1 — Tenant Isolation

- Test: test_export_includes_only_exact_tenant
- Expected: Only R01 should be exported.
- Actual: R01 and X01 were exported.
- Result: FAILED as expected.
- Cause: Substring matching instead of exact tenant comparison.
- Next action: Fix tenant filtering.