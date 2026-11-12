# FernExport run guide

Requirements: Python 3.10 or later, standard library only. Run every command from the repository root. The results below were recorded on 2026-11-12 with Python 3.14.9.

## 1. Commands

| Purpose | Command | Expected result |
|---|---|---|
| Version | `python3 --version` | 3.10 or later |
| Help | `python3 -B app.py --help` | usage text, exit 0 |
| All tests | `python3 -B -m unittest discover -s tests -p '*_test.py' -v` | `Ran 32 tests`, `OK` |
| Checker tests only | `python3 -B -m unittest discover -s tests -p 'round_trip_checker_test.py' -v` | `Ran 9 tests`, `OK` |
| Primary fixture | `python3 -B app.py --input inputs/primary.json` | exit 0, JSON in §2 |
| Secondary fixture | `python3 -B app.py --input inputs/secondary.json` | exit 0, JSON in §2 |
| Malformed JSON | `python3 -B app.py --input inputs/malformed-input.txt` | exit 2, stderr `error: Expecting ',' delimiter: line 2 column 1 (char 34)`, empty stdout |
| Missing file | `python3 -B app.py --input inputs/does-not-exist.json` | exit 2, stderr `error: [Errno 2] No such file or directory: 'inputs/does-not-exist.json'`, empty stdout |
| Whole fix | `git diff 4e0672d HEAD -- app.py` | `4e0672d` holds the unmodified starter |

## 2. Representative output

Both fixtures have 10 input rows. Rows R01–R08 are exported in input order. X01 (tenant `fern-archive`) and X02 (tenant `other`) are excluded (P2). No cell is redacted (P5).

Primary (`direct`):

```text
"summary": {"exported_rows": 8, "foreign_rows": 2, "input_rows": 10, "neutralized_cells": 4, "redacted_cells": 0}
neutralized_cells (row then column): R02.title, R03.title, R04.title, R05.title
"csv": "row_id,title,note\r\nR01,Plain title,\"comma, note\"\r\nR02,\"'=SUM(1,2)\",\"line one\nline two\"\r\nR03,'+12,\"He said \"\"hello\"\"\"\r\nR04,'-42,\r\nR05,'@lookup,\\N\r\nR06, =not-direct,\t+not-direct\r\nR07,'=already-text,\\\\N\r\nR08,Backslash \\\\ path,normal\r\n"
```

Secondary (`trim-space-tab`):

```text
"summary": {"exported_rows": 8, "foreign_rows": 2, "input_rows": 10, "neutralized_cells": 6, "redacted_cells": 0}
neutralized_cells (row then column): R02.title, R03.title, R04.title, R05.title, R06.title, R06.note
```

The JSON above is escaped. The table below shows the cells as `csv.reader` returns them. `\t` means a tab character. These values are asserted literally in `tests/round_trip_checker_test.py` (`PRIMARY_RECORDS`, `SECONDARY_CHANGES`).

| Cell | Input value | Primary (`direct`) | Secondary (`trim-space-tab`) | Rule |
|---|---|---|---|---|
| R01.note | `comma, note` / `comma, revised note` | `comma, note` | `comma, revised note` | P5 comma kept in one cell; fixture text revised |
| R02.title | `=SUM(1,2)` | `'=SUM(1,2)` | same | P4 |
| R02.note | two lines | one cell `line one` + newline + `line two` | same | P5 |
| R03.title | `+12` | `'+12` | same | P4 |
| R03.note | `He said "hello"` | same text (quotes doubled only inside the CSV) | same | P5 |
| R04.title / note | `-42` / empty | `'-42` / empty | same | P4 / P3 |
| R05.title / note | `@lookup` / null | `'@lookup` / `\N` | same | P4 / P3 |
| R06.title | ` =not-direct` | ` =not-direct` | `' =not-direct` | P4 policy-specific |
| R06.note | `\t+not-direct` | `\t+not-direct` | `'\t+not-direct` | P4 policy-specific |
| R07.title | `'=already-text` | `'=already-text` (not prefixed again) | same | P4 |
| R07.note | literal `\N` | `\\N` | same | P3 |
| R08.title | `Backslash \ path` | `Backslash \\ path` | same | P3 |

Reconciliation of the second fixture: 3 of 24 data cells change (R01.note because the fixture text changed; R06.title and R06.note because of the stricter policy). The other 21 cells are identical. Both CSVs parse as 1 header plus 8 records, including R02's two-line note.

## 3. What the tests assert

| Test file | Asserts |
|---|---|
| `app_test.py` | The 4 supplied smoke checks, unchanged |
| `tenant_isolation_test.py` | Only exact tenant `fern`; `fern-archive` and `other` sentinels absent (P2) |
| `csv_serialization_test.py` | Commas, quotes and newlines survive `csv.reader`; CRLF only (P5) |
| `cell_encoding_test.py` | null `\N`, empty, literal `\N` becomes `\\N`; backslashes doubled; apostrophes kept (P3) |
| `formula_neutralization_test.py` | All four triggers, `row_id` included; both policies; newline is not skipped; apostrophe input not re-prefixed (P4) |
| `repeatability_test.py` | Input unchanged; two calls identical (P4, P6) |
| `input_validation_test.py` | Envelope and row validation, duplicates, validation before selection, exit 2 with no stdout and no cell values, deeply nested JSON (P1) |
| `round_trip_checker_test.py` | Reusable checker on both fixtures, empty input, constructed boundary and two calls on one object; literal README self-check; exact 3-cell reconciliation; checker rejects 5 tampered results (P2–P6) |
| `generated_cells_test.py` | Optional stretch: 200 generated rows (fixed seed) per policy through the same checker |

## 4. Re-run the failing-first evidence

This runs the 20 tests committed before the fix (commit `a7c1ff6`) against the unmodified starter, in a temporary folder:

```sh
tmp=$(mktemp -d)
git archive a7c1ff6 | tar -x -C "$tmp"
(cd "$tmp" && python3 -B -m unittest discover -s tests -p '*_test.py')
```

Expected: `Ran 20 tests`, `FAILED (failures=15)`. The 5 tests that pass are the 4 smoke checks and the newline/apostrophe control. The output is in `work-log.md`, Appendix B.

## 5. Reuse the checker on another payload or policy

```python
import argparse, copy, unittest
import app
from csv_checker import assert_export_matches_policy  # tests/ must be on sys.path

class MyCheck(unittest.TestCase):
    def test_new_payload(self):
        payload = {"tenant": "fern", "policy": "trim-space-tab", "rows": [
            {"row_id": "N01", "tenant": "fern", "title": " =total", "note": None},
            {"row_id": "N02", "tenant": "fern-archive", "title": "x", "note": "y"},
        ]}
        original = copy.deepcopy(payload)
        result = app.export_rows(payload, argparse.Namespace())
        assert_export_matches_policy(self, original, result)
```

The checker derives the expected cells from `payload["policy"]`, so it needs no change for a different consumer policy.

## 6. Test results (2026-11-12, Python 3.14.9)

```text
$ python3 -B -m unittest discover -s tests -p '*_test.py'
Ran 32 tests in 2.131s

OK
```

Also verified:
- `git diff --check 4e0672d` reports no whitespace errors.
- `inputs/*`, `README.md` and `tests/app_test.py` are byte-identical to the exercise zip.

## 7. Known limitations
- The exporter implements the synthetic FernExport policy only. No spreadsheet application was opened, so no spreadsheet safety is claimed (see C7 in `review.md`).
- Leading characters other than ASCII space and tab (newline, carriage return, non-breaking space) and look-alikes such as full-width `＝` are not neutralized. This is what P4 specifies, but some spreadsheet applications may treat them differently.
