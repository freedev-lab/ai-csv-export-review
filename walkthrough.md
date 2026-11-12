# FernExport walkthrough (text version, about 4 minutes)

## 1. What I did
Before changing anything, I reviewed the AI-drafted PR #315 against the export policy P1–P6. Then I:
- reproduced each reported symptom with a failing test;
- repaired `export_rows` with the standard `csv` module;
- built a reusable round-trip checker that passes, unchanged, on both fixtures.

The order is visible in git: review, failing tests, checker, fix, controls, documentation.

## 2. The most serious defect: another tenant's row leaks (P2)
The patch selected rows with `if tenant not in row["tenant"]`, which is a substring test. For the requested tenant `fern`, row X01 of tenant `fern-archive` also matched, because `fern` is a substring of `fern-archive`.

What the unmodified code produced for `primary.json`:
- The CSV contained `X01,FOREIGN-SENTINEL-ONE,'=foreign`.
- The audit (`neutralized_cells`) contained `{"row_id": "X01", "column": "note"}`, so the foreign ID also leaked into the diagnostics.
- The summary said 9 exported rows and 1 foreign row instead of 8 and 2.

This is the teammate's "unfamiliar tenant row". I rank it Critical because it gives one tenant another tenant's data. The other defects corrupt the output but expose no foreign data.

The fix is one line, an exact case-sensitive comparison: `if row["tenant"] != tenant: continue`. The test `test_export_includes_only_exact_tenant` failed before the fix (`['R01', 'X01'] != ['R01']`) and passes now. If the leak ever comes back, the checker fails with `Foreign row at position 9 entered the audit.`

## 3. One edge case: the same cell under two consumer policies (P4)
Row R06 has the title ` =not-direct` (leading space) and the note `\t+not-direct` (leading tab).
- **Under `direct`**, only character zero is checked. It is a space or a tab, so both cells are exported unchanged.
- **Under `trim-space-tab`**, leading ASCII spaces and tabs are skipped, so the check sees `=` and `+`. Exactly one apostrophe is added in front of the whole encoded value, and the whitespace is kept: `' =not-direct` and `'\t+not-direct`.

That is why the primary fixture neutralizes 4 cells and the secondary fixture 6. Related boundaries are tested too:
- a leading newline is never skipped (`"\n=x"` is not neutralized);
- an apostrophe-prefixed value such as R07 `'=already-text` is not prefixed again;
- `row_id` is checked like every other exported string.

## 4. Evidence of execution (2026-11-12, Python 3.14.9)
- `python3 -B -m unittest discover -s tests -p '*_test.py' -v` gives `Ran 32 tests in 2.131s` and `OK`, with 32 passing and 0 failing.
- Before the fix, the 20 tests committed at that point failed 15 times on the starter (`FAILED (failures=15)`). The re-run command is in `run-guide.md` §4.
- `python3 -B app.py --input inputs/primary.json` exits 0. The summary is `input_rows 10, exported_rows 8, foreign_rows 2, neutralized_cells 4, redacted_cells 0`, and the neutralized cells are the titles of R02–R05.
- `python3 -B app.py --input inputs/secondary.json` exits 0 with the same counts except `neutralized_cells 6`; R06's title and note are added.
- Both CSVs parse as one header plus 8 records, R01–R08 in input order, including R02's two-line note.
- The second fixture changes exactly 3 parsed cells (R01.note, R06.title, R06.note); the other 21 are identical.
- `python3 -B app.py --input inputs/malformed-input.txt` exits 2 with `error: Expecting ',' delimiter: line 2 column 1 (char 34)` and empty stdout.

## 5. Limits
The checks prove the synthetic policy:
- exact transport of the policy-transformed cells through `csv.writer` and `csv.reader`;
- reversal of the encoding using the audit;
- tenant isolation;
- nonmutation and repeatability.

They do not prove spreadsheet safety. No spreadsheet application was opened, and the policy deliberately leaves a leading newline, carriage return, non-breaking space or full-width `＝` untouched. So the PR's claim C7, "safe in every spreadsheet application", is false.
