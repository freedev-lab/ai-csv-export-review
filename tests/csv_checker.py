
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
    payload: original input dictionary
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
    test_case.assertFalse(csv_text.startswith("\ufeff"))

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

    # Verify header, cell values and row order.
    test_case.assertEqual(
        parsed_records,
        expected_records
    )

    # 5. Verify row and column counts.
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

    # 6. Independently serialize expected cells.
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

    # 7. Verify the neutralization audit.
    test_case.assertEqual(
        result["neutralized_cells"],
        expected_audit
    )

    # 8. Verify summary information.
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

    # 9. Explicitly verify foreign records are absent.
    exported_ids = {
        record[0] for record in parsed_records[1:]
    }

    for foreign_row in foreign_rows:

        test_case.assertNotIn(
            foreign_row["row_id"],
            exported_ids
        )

        test_case.assertNotIn(
            foreign_row["row_id"],
            [
                item["row_id"]
                for item in result["neutralized_cells"]
            ]
        )

    # 10. Reverse the encoding using the audit.
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
