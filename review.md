
# Code Review — AI CSV Exporter

## 1. Review Summary

The current implementation contains several defects
that prevent it from satisfying the export policy P1-P6.

## 2. Bugs

### Bug 1 — Tenant Isolation
- Location: app.py, line 39
- Severity: Critical
- Requirement: P2
- Problem: The application uses substring matching (tenant not in row["tenant]) instead of exact string comparison when selecting rows.
- Consequence: when exporting data for tenant fern, the application can also include data belonging to fern-archive,this creates a tenant data isolation proplem and can expose another tenant's information
- Solution: Replace substring matching with exact equality (row["tenant"] != tenant). This ensures that only rows belonging to the requested tenant are exported.

### Bug 2 — CSV Serialization
- Location: app.py, lines 35 and 47-49
- Severity: High
- Requirement: P5
- Problem: The application manually generates CSV content by joining values with commas instead of using Python's standard csv library.
- Consequence: Values containing commas, quotation marks or newlines can break the CSV structure. This can cause spreadsheet applications or CSV parsers to interpret the data incorrectly. The implementation also uses LF (\n) instead of the required CRLF (\r\n) record endings.
- Solution: Use Python's standard csv.writer with the required configuration: comma delimiter, double quote character, doublequote=True, QUOTE_MINIMAL and CRLF line endings.

### Bug 3 — Cell Encoding
- Location: app.py, line 42
- Severity: High
- Requirement: P3
- Problem:The application converts None into an empty string and doubles apostrophes instead of escaping backslashes. This does not follow the required cell encoding policy.
- Consequence: The original distinction between null values, empty strings and literal \N strings is lost. Original backslashes are also not preserved correctly, while apostrophes are unnecessarily modified.
- Solution:Encode None as \N, double every backslash in string values, and preserve other characters, including apostrophes and newlines. Do not modify the original values.

### Bug 4 — Formula Neutralization
- Location: app.py, lines 43-45
- Severity: High
- Requirement: P4
- Problem: The application only checks whether a value starts with =. It ignores the other required formula triggers (+, - and @) and does not implement the two consumer policies (direct and trim-space-tab).
- Consequence:Some potentially dangerous values can be exported without neutralization. Values with leading spaces or tabs are also handled incorrectly under the trim-space-tab policy.
- Solution: Check the original string according to the selected policy. For direct, inspect the first character. For trim-space-tab, skip only leading ASCII spaces and tabs. If the checked character is =, +, - or @, prefix exactly one apostrophe to the encoded value and record the cell in the audit.

### Bug 5 — Input Mutation
- Location: app.py, line 46
- Severity: High
- Requirement: P4 and P6
- Problem: The application assigns transformed cell values directly back to the original row using row[column] = value.
- Consequence: Exporting data modifies the original input objects. Calling the export function multiple times with the same input can produce different results because the original data has already been changed.
- Solution: Never modify the original rows. Create a separate list of encoded cell values for each exported row and pass that list to the CSV writer. This ensures that the input remains unchanged and repeated exports produce identical results.

### Bug 6 — Missing Protection for row_id
- Location: app.py, lines 41-45
- Severity: High
- Requirement: P4
- Problem: The formula neutralization loop only processes title and note, excluding row_id.
- Consequence: A row_id beginning with a formula trigger such as =, +, - or @ is exported without the required neutralization. This means the implementation does not apply the P4 policy to every exported string.
- Solution: Apply the cell encoding and formula neutralization process to all exported columns, including row_id, title and note. Preserve the required column order.


## 3. AI Claims Review

| Claim | Verdict | Explanation |
|-------|---------|-------------|
| C1 | False | Manual string joining does not safely serialize commas, quotes and multiline values. |
| C2 | False | Only the equals sign is checked; the other three formula triggers are ignored. |
| C3 | False | Null values and empty strings become identical, and backslashes are not escaped. |
| C4 | False | Substring matching can include related tenant names such as fern-archive. |
| C5 | False | The exporter modifies original row objects and changes repeated results. |
| C6 | Confirmed | The four supplied CLI smoke checks pass. |
| C7 | False | The tests do not establish universal spreadsheet safety. No spreadsheet application was tested. |

## 4. Merge Verdict

**Original AI implementation: Request changes.**

The original implementation does not satisfy P1-P6.

The corrected implementation addresses the identified defects through exact tenant matching, policy-compliant cell encoding, standard CSV serialization, nonmutating processing and automated acceptance tests.

The corrected implementation should be considered ready for approval only after the complete test suite and both supplied fixtures pass.
