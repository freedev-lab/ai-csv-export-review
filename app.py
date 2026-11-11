"""Exercise starter: an AI-drafted implementation with deliberate defects; review, test and repair it."""
from __future__ import annotations

import argparse
import json
import pathlib
import sys
import typing


COLUMNS = ("row_id", "title", "note")


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
    lines = [",".join(COLUMNS)]
    audit = []
    exported = 0
    for row in rows:
        if tenant not in row["tenant"]:
            continue
        for column in ("title", "note"):
            value = (row[column] or "").replace("'", "''")
            if value.startswith("="):
                value = "'" + value
                audit.append({"row_id": row["row_id"], "column": column})
            row[column] = value
        lines.append(",".join(row[column] for column in COLUMNS))
        exported += 1
    return {"csv": "\n".join(lines) + "\n", "neutralized_cells": audit,
            "summary": {"input_rows": len(rows), "exported_rows": exported,
                        "foreign_rows": len(rows) - exported, "neutralized_cells": len(audit), "redacted_cells": 0}}


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
    except (OSError, UnicodeError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
