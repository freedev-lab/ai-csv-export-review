"""Reusable round-trip checker for FernExport export results (P2-P6).

Use it from any unittest.TestCase with an unmodified copy of the payload:

    original = copy.deepcopy(payload)
    result = app.export_rows(payload, argparse.Namespace())
    assert_export_matches_policy(self, original, result)

Expected cells are derived from payload["policy"], so the same checker works
for either consumer policy without changes. It asserts: the result keys; no
BOM; the exact header, cell values, row order and column/row counts after
csv.reader parsing; the exact csv.writer text (CRLF, QUOTE_MINIMAL); that no
foreign row ID or content reaches the CSV or the audit; the exact audit and
summary; and that reversing the encoding with the audit restores every
original cell. It proves nothing about spreadsheet applications.
"""

from __future__ import annotations

import csv
import io

COLUMNS = ("row_id", "title", "note")
FORMULA_TRIGGERS = ("=", "+", "-", "@")


def _expected_cell(value, policy):
    """Calculate the expected encoded cell without modifying the input."""

    if value is None:
        return r"\N", False

    if policy == "trim-space-tab":
        checked = value.lstrip(" \t")
    else:
        checked = value

    neutralized = (
        bool(checked)
        and checked[0] in FORMULA_TRIGGERS
    )

    encoded = value.replace("\\", "\\\\")

    if neutralized:
        encoded = "'" + encoded

    return encoded, neutralized


def _decode_cell(encoded, neutralized):
    """Reverse the policy encoding using the audit information."""

    if neutralized:
        if not encoded.startswith("'"):
            raise AssertionError(
                "Neutralized cell is missing its audit apostrophe."
            )

        encoded = encoded[1:]

    if encoded == r"\N":
        return None

    decoded = []
    index = 0

    while index < len(encoded):

        if encoded[index] == "\\":

            if (
                index + 1 >= len(encoded)
                or encoded[index + 1] != "\\"
            ):
                raise AssertionError(
                    "Unescaped backslash found in exported cell."
                )

            decoded.append("\\")
            index += 2

        else:
            decoded.append(encoded[index])
            index += 1

    return "".join(decoded)


def assert_export_matches_policy(test_case, payload, result):
    """
    Verify the CSV result against the authoritative export policy.

    test_case: unittest.TestCase instance
    payload: original (unmodified) input dictionary
    result: output returned by app.export_rows()
    """

    # 1. Verify the result structure.
    test_case.assertEqual(
        set(result),
        {"csv", "neutralized_cells", "summary"}
    )

    csv_text = result["csv"]

    test_case.assertIsInstance(csv_text, str)

    # A UTF-8 BOM is not allowed.
    test_case.assertFalse(csv_text.startswith("﻿"))

    # 2. Select only the exact requested tenant.
    selected_rows = [
        row for row in payload["rows"]
        if row["tenant"] == payload["tenant"]
    ]

    foreign_rows = [
        row for row in payload["rows"]
        if row["tenant"] != payload["tenant"]
    ]

    # 3. Calculate the expected exported cells.
    expected_records = [list(COLUMNS)]
    expected_audit = []

    for row in selected_rows:

        cells = []

        for column in COLUMNS:

            encoded, neutralized = _expected_cell(
                row[column],
                payload["policy"]
            )

            cells.append(encoded)

            if neutralized:
                expected_audit.append({
                    "row_id": row["row_id"],
                    "column": column
                })

        expected_records.append(cells)

    # 4. Parse the actual CSV.
    parsed_records = list(
        csv.reader(
            io.StringIO(csv_text, newline="")
        )
    )

    # 5. No foreign row ID or content may reach the CSV or the audit (P2).
    # Checked before the full comparison so a leak fails with a clear
    # message. Both the raw and the encoded form of each foreign cell are
    # checked; values that a selected row legitimately exports are skipped.
    expected_cells = {
        cell for record in expected_records[1:] for cell in record
    }

    parsed_cells = {
        cell for record in parsed_records[1:] for cell in record
    }

    audit_row_ids = {
        item.get("row_id")
        for item in result["neutralized_cells"]
        if isinstance(item, dict)
    }

    for position, row in enumerate(payload["rows"], start=1):

        if row["tenant"] == payload["tenant"]:
            continue

        test_case.assertNotIn(
            row["row_id"],
            audit_row_ids,
            f"Foreign row at position {position} entered the audit."
        )

        for column in COLUMNS:

            value = row[column]

            # Null and empty cells also occur legitimately.
            if not value:
                continue

            encoded, _ = _expected_cell(value, payload["policy"])

            for form in {value, encoded}:

                if form in expected_cells:
                    continue

                test_case.assertNotIn(
                    form,
                    parsed_cells,
                    f"Foreign {column} from row position {position} "
                    f"entered the CSV."
                )

    # 6. Verify header, cell values and row order.
    test_case.assertEqual(
        parsed_records,
        expected_records
    )

    # 7. Verify row and column counts.
    test_case.assertEqual(
        parsed_records[0],
        list(COLUMNS)
    )

    test_case.assertEqual(
        len(parsed_records),
        len(selected_rows) + 1
    )

    for record in parsed_records:
        test_case.assertEqual(len(record), len(COLUMNS))

    # 8. Independently serialize expected cells.
    # This checks quoting and exact CRLF record endings.
    expected_stream = io.StringIO(newline="")

    writer = csv.writer(
        expected_stream,
        delimiter=",",
        quotechar='"',
        doublequote=True,
        quoting=csv.QUOTE_MINIMAL,
        lineterminator="\r\n"
    )

    writer.writerows(expected_records)

    test_case.assertEqual(
        csv_text,
        expected_stream.getvalue()
    )

    # 9. Verify the neutralization audit.
    test_case.assertEqual(
        result["neutralized_cells"],
        expected_audit
    )

    # 10. Verify summary information.
    expected_summary = {
        "input_rows": len(payload["rows"]),
        "exported_rows": len(selected_rows),
        "foreign_rows": len(foreign_rows),
        "neutralized_cells": len(expected_audit),
        "redacted_cells": 0
    }

    test_case.assertEqual(
        result["summary"],
        expected_summary
    )

    # 11. Reverse the encoding using the audit (P6).
    audit_keys = {
        (item["row_id"], item["column"])
        for item in result["neutralized_cells"]
    }

    for index, original_row in enumerate(selected_rows, start=1):

        exported_record = parsed_records[index]

        for column_index, column in enumerate(COLUMNS):

            encoded = exported_record[column_index]

            was_neutralized = (
                original_row["row_id"],
                column
            ) in audit_keys

            decoded = _decode_cell(
                encoded,
                was_neutralized
            )

            test_case.assertEqual(
                decoded,
                original_row[column],
                f"Round-trip mismatch in {original_row['row_id']}.{column}"
            )
