"""Exercise starter: an AI-drafted implementation with deliberate defects; review, test and repair it."""
from __future__ import annotations

import argparse
import csv
import io
import json
import pathlib
import sys
import typing


COLUMNS = ("row_id", "title", "note")


def encode_cell(value: str | None, policy: str) -> tuple[str, bool]:
    """Encode one cell according to the export policy."""

    # P3: Represent missing values.
    if value is None:
        return r"\N", False

    # P4: Determine which character should be checked.
    if policy == "trim-space-tab":
        checked = value.lstrip(" \t")
    else:
        checked = value

    # Check all four formula triggers.
    neutralized = (
        bool(checked)
        and checked[0] in ("=", "+", "-", "@")
    )

    # P3: Escape every original backslash.
    encoded = value.replace("\\", "\\\\")

    # P4: Prefix exactly one apostrophe when necessary.
    if neutralized:
        encoded = "'" + encoded

    return encoded, neutralized


def export_rows(payload: dict[str, typing.Any], arguments: argparse.Namespace) -> dict[str, typing.Any]:
    """Export fixture rows; policy is supplied by the consumer."""
    tenant = payload.get("tenant")
    rows = payload.get("rows")
    policy = payload.get("policy")
    if not isinstance(tenant, str) or not tenant or not isinstance(rows, list):
        raise ValueError("invalid export envelope")
    if policy not in ("direct", "trim-space-tab"):
        raise ValueError("invalid consumer policy")
    # Validate structure without echoing any cell values.
    seen = set()
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            raise ValueError(f"invalid row {index + 1}")
        if any(not isinstance(row.get(key), str) or not row[key] for key in ("row_id", "tenant")):
            raise ValueError(f"invalid row {index + 1}")
        if row["row_id"] in seen:
            raise ValueError(f"duplicate row {index + 1}")
        seen.add(row["row_id"])
        if any(key not in row or (row[key] is not None and not isinstance(row[key], str)) for key in ("title", "note")):
            raise ValueError(f"invalid row {index + 1}")

    # P5: Create an in-memory CSV output.
    output = io.StringIO(newline="")

    writer = csv.writer(
        output,
        delimiter=",",
        quotechar='"',
        doublequote=True,
        quoting=csv.QUOTE_MINIMAL,
        lineterminator="\r\n",
    )

    # Write the CSV header.
    writer.writerow(COLUMNS)

    audit = []
    exported = 0

    # P2: Select only the exact requested tenant.
    for row in rows:

        if row["tenant"] != tenant:
            continue

        cells = []

        # Process every exported column in the correct order.
        for column in COLUMNS:

            encoded, neutralized = encode_cell(
                row[column],
                policy
            )

            cells.append(encoded)

            # Record every neutralized cell.
            if neutralized:
                audit.append({
                    "row_id": row["row_id"],
                    "column": column
                })

        # Write the complete row.
        writer.writerow(cells)
        exported += 1

    # P5 and P6: Return the generated CSV and metadata.
    return {
        "csv": output.getvalue(),
        "neutralized_cells": audit,
        "summary": {
            "input_rows": len(rows),
            "exported_rows": exported,
            "foreign_rows": len(rows) - exported,
            "neutralized_cells": len(audit),
            "redacted_cells": 0
        }
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Export fictional tenant rows as a CSV string inside JSON.")
    parser.add_argument("--input", default="inputs/primary.json", help="UTF-8 fixture JSON")
    arguments = parser.parse_args()
    try:
        payload = json.loads(pathlib.Path(arguments.input).read_text(encoding="utf-8"))
        if isinstance(payload, dict) is False:
            raise ValueError("input must be a JSON object")
        result = export_rows(payload, arguments)
        print(json.dumps(result, indent=2, sort_keys=True))
    except NotImplementedError as error:
        print(str(error), file=sys.stderr)
        return 3
    # RecursionError: JSON nested too deeply for json.loads is a fatal input error (P1).
    except (OSError, UnicodeError, ValueError, RecursionError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
