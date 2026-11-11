
# FernExport — Run Guide

## Requirements

- Python 3.10 or later
- Python standard library
- No external dependencies required

## 1. Run the original smoke and acceptance tests

```bash
python3 -B -m unittest discover -s tests -p '*_test.py' -v
```

## 2. Run the primary fixture

```bash
python3 -B app.py --input inputs/primary.json
```

Expected:
- Input rows: 10
- Exported rows: 8
- Foreign rows: 2
- Neutralized cells: 4
- Redacted cells: 0

## 3. Run the secondary fixture

```bash
python3 -B app.py --input inputs/secondary.json
```

Expected:
- Input rows: 10
- Exported rows: 8
- Foreign rows: 2
- Neutralized cells: 6
- Redacted cells: 0

## 4. Verify the CSV

The automated round-trip checker verifies:
- Header and column order.
- Parsed cell contents.
- Record and column counts.
- Formula-neutralization audit.
- Summary information.
- Tenant isolation.
- Empty-input behavior.
- Input immutability and repeatability.

## 5. Verify malformed input

```bash
python3 -B app.py --input inputs/malformed-input.txt
```

Expected:
- Exit code: 2
- Readable error on stderr.
- No output on stdout.

## 6. Test results

Record the actual number of tests executed and their result here.

## 7. Known limitations

The exporter implements the synthetic FernExport policy.
Its formula-neutralization behavior does not guarantee
universal protection across all spreadsheet applications.
