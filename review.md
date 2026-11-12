# Code review: AI-drafted PR #315 (tenant CSV export)

**Scope.** `app.py` exactly as supplied (byte-identical to the exercise zip and committed unchanged in `4e0672d`), reviewed against `inputs/export-policy.md` (P1–P6). The review includes code outside the diff (`main()`). Starter line numbers match the post-patch line numbers of `inputs/change.diff` (hunk `@@ -15 +15,37 @@`). "Now" references point to the repaired `app.py`.

**Evidence.** Starter output for `inputs/primary.json` and `inputs/secondary.json`, parsed with `csv.reader`, plus the failing-first tests. The tests committed before the fix give 20 tests and 15 failures on the starter; the re-run command is in `run-guide.md` §4.

**Severity scale.** Critical: another tenant's data is exposed. High: valid input gives wrong or unparseable output, or calls are not repeatable. Low: fails only on pathological input.

## Teammate symptoms and their causes

| Reported symptom | Cause |
|---|---|
| A parser sees unexpected records | Bug 2: CSV built with `",".join`, no quoting |
| A tenant reports an unfamiliar row | Bug 1: substring tenant match exports `fern-archive` rows |
| Repeat calls differ | Bug 5: the export rewrites the caller's rows |

## Findings

### Bug 1: related-name tenant rows are exported (Critical, P2)
- **Location:** `app.py:39`, `if tenant not in row["tenant"]:`
- **Evidence:** for `primary.json`, the starter's CSV contains `X01,FOREIGN-SENTINEL-ONE,'=foreign` (tenant `fern-archive`). `neutralized_cells` contains `{"row_id": "X01", "column": "note"}`. The summary reports `exported_rows: 9, foreign_rows: 1` instead of 8 and 2. Failing test: `test_export_includes_only_exact_tenant`.
- **Consequence:** tenant `fern` receives another tenant's row, and the foreign ID also leaks into the audit. This is a cross-tenant data exposure.
- **Fix:** case-sensitive exact equality, `if row["tenant"] != tenant: continue` (now `app.py:88`).

### Bug 2: CSV is built by joining strings (High, P5)
- **Location:** `app.py:35`, `app.py:47`, `app.py:49`
- **Evidence:** `csv.reader` parses the starter's primary CSV as 11 records instead of 9:
  - R01 becomes 4 fields (`comma`, ` note`).
  - R02 becomes `'=SUM(1`, `2)`, `line one`, plus a separate one-field record `line two`.
  - Records end in LF, not CRLF.

  R03's `He said "hello"` happens to survive Python's reader because the field does not start with a quote, but it is still not P5 quoting. Failing tests: `test_writer_preserves_commas_quotes_and_embedded_newlines`, `test_writer_uses_crlf_record_endings`.
- **Consequence:** consumers see extra or shifted records and columns.
- **Fix:** stdlib `csv.writer` with comma delimiter, `"` quotechar, `doublequote=True`, `QUOTE_MINIMAL`, `lineterminator="\r\n"` and no BOM (now `app.py:67-80`; rows written at `app.py:111`).

### Bug 3: wrong cell encoding (High, P3)
- **Location:** `app.py:42`, `value = (row[column] or "").replace("'", "''")`
- **Evidence:**
  - R05.note (`null`) and R04.note (`""`) both export as an empty field.
  - R07.note, the literal text `\N`, is exported unescaped as `\N`, so a reader decodes it as null.
  - R08's backslash is not doubled.
  - R07.title `'=already-text` becomes `''=already-text`.

  Failing tests: `test_null_empty_and_literal_backslash_n_remain_distinct`, `test_backslashes_are_doubled_and_apostrophes_preserved`.
- **Consequence:** null, empty and literal `\N` cannot be told apart, backslashes cannot be decoded, and user text with apostrophes is altered.
- **Fix:** `encode_cell` (now `app.py:16-42`): `None` becomes `\N`, every backslash is doubled, and apostrophes and newlines are left alone.

### Bug 4: only `=` is checked and the consumer policy is ignored (High, P4)
- **Location:** `app.py:43-45`
- **Evidence:**
  - In `primary.json`, R03 `+12`, R04 `-42` and R05 `@lookup` are exported without an apostrophe. The audit lists only R02.title and the foreign X01.note.
  - For `secondary.json` (`trim-space-tab`), R06 ` =not-direct` and `\t+not-direct` are not neutralized.

  Failing tests: `test_direct_policy_checks_all_four_triggers`, `test_trim_space_tab_policy_skips_only_spaces_and_tabs`.
- **Consequence:** three of the four trigger characters, and the stricter consumer mode, are unprotected.
- **Fix:** check character zero (`direct`) or the first character after leading ASCII spaces and tabs (`trim-space-tab`) against `= + - @`. Prefix exactly one apostrophe to the encoded full string. Record `row_id`/`column` in row-then-column order (now `app.py:23-40`, audit at `app.py:103-108`).

### Bug 5: the export mutates the caller's rows (High, P4 and P6)
- **Location:** `app.py:46`, `row[column] = value`
- **Evidence:**
  - One call rewrites the payload: R02.title becomes `'=SUM(1,2)` and R05.note `None` becomes `""`.
  - A second call on the same object returns a different CSV: R02.title `''=SUM(1,2)`, R07.title `''''=already-text`.
  - Even the foreign row X01 is modified.

  Failing tests: `test_export_does_not_modify_original_payload`, `test_repeated_exports_produce_identical_results`, `test_two_exports_of_same_object_are_identical`.
- **Consequence:** results depend on how many times the export ran, and caller data is corrupted.
- **Fix:** encoded values go into a new `cells` list per row; input rows are never assigned (now `app.py:91-111`).

### Bug 6: `row_id` is never encoded or checked (High, P3 and P4)
- **Location:** `app.py:41`, `for column in ("title", "note"):`
- **Evidence:** P4 applies to "each original non-null exported string", and `row_id` is exported. A row ID `=R01` is exported as `=R01` with no audit entry, and a backslash in a row ID would not be doubled. Failing test: `test_direct_policy_checks_all_four_triggers` (row `=R01`).
- **Consequence:** a formula can enter the CSV through the ID column.
- **Fix:** `encode_cell` runs for every column in `COLUMNS`, including `row_id` (now `app.py:94`).

### Bug 7, outside the diff: deeply nested JSON crashes the CLI (Low, P1)
- **Location:** `app.py:67` in the starter's `main()`, `except (OSError, UnicodeError, ValueError)`
- **Evidence:** a valid JSON array nested 100,000 levels deep makes `json.loads` raise `RecursionError`, so the CLI printed a traceback and exited 1. Failing test: `test_cli_rejects_excessively_nested_json` (`AssertionError: 1 != 2`).
- **Consequence:** breaks the P1 contract that fatal errors exit 2 with readable stderr.
- **Fix:** `RecursionError` was added to the fatal-error handler (now `app.py:141-142`). The CLI now prints `error: Stack overflow (...) while decoding a JSON array from a unicode string` on Python 3.14, exits 2 and writes nothing to stdout.

## Confirmed correct and kept unchanged
- **P1 validation in the AI patch** (`app.py:50-65`): envelope, policy, row types, unique non-empty `row_id`, present `title`/`note`, every row validated before selection, and position-only error messages. The 7 control tests in `tests/input_validation_test.py` pass on both the starter and the fix.
- `main()` prints only after `export_rows` returns, so a fatal error never leaves partial stdout.
- The four smoke checks in `tests/app_test.py` are unchanged.

## Claim check (C1–C7)

| Claim | Disposition | Reason and evidence |
|---|---|---|
| C1: commas, quotes and multiline notes preserved | **False** | Bug 2: 11 parsed records instead of 9 for primary; R01 and R02 are split. |
| C2: all four triggers, either policy | **False** | Bug 4: only `=` is checked. R03 `+`, R04 `-`, R05 `@` and R06 under trim-space-tab are not neutralized, and `row_id` is never checked (Bug 6). |
| C3: null, empty and literal `\N` distinguishable | **False** | Bug 3: R05 null and R04 empty both export as an empty field; literal `\N` is not escaped. |
| C4: related-name tenants excluded, including diagnostics | **False** | Bug 1: X01 (`fern-archive`) is in the CSV **and** in `neutralized_cells`, and the summary counts it as exported. |
| C5: nonmutating, repeatable, apostrophe-prefixed text preserved | **False** | Bug 5: the input is rewritten and a second call differs. Bug 3: R07 `'=already-text` becomes `''=already-text`. |
| C6: four CLI smoke checks pass | **Confirmed** | They pass on the starter and on the fix. They are infrastructure checks: check 4 only checks types, so it passed while the starter leaked X01. They are not evidence of correctness. |
| C7: safe in every spreadsheet application | **False** | The checks open no spreadsheet (the PR says none was tested), and P6 says the policy proves no universal guarantee. P4 leaves some leading characters untouched (for example newline, carriage return, non-breaking space and full-width `＝`), so "every application" cannot follow. Safety in any specific application is not verifiable with the supplied material. |

## Merge verdict
- **PR #315 as drafted: request changes; do not merge.** Bug 1 exposes another tenant's row and ID, Bugs 2–6 make the CSV wrong or unparseable, and C1–C5 and C7 are false.
- **Repaired branch: approve.** `export_rows` meets P1–P6. All 32 tests pass. Both fixtures match the README self-check: 10 input rows, 8 exported in R01–R08 order, 2 foreign, 4 (primary) and 6 (secondary) neutralized, 0 redacted. The supplied fixtures, patch and claim description are byte-identical to the exercise zip. The approval covers the synthetic policy only (see C7).
