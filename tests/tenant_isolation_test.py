
from __future__ import annotations

import argparse
import csv
import io
import unittest

import app


class TenantIsolationTests(unittest.TestCase):

    def test_export_includes_only_exact_tenant(self) -> None:

        payload = {
            "tenant": "fern",
            "policy": "direct",
            "rows": [
                {
                    "row_id": "R01",
                    "tenant": "fern",
                    "title": "Belongs to fern",
                    "note": "Keep this row",
                },
                {
                    "row_id": "X01",
                    "tenant": "fern-archive",
                    "title": "FOREIGN-SENTINEL",
                    "note": "Must not be exported",
                },
                {
                    "row_id": "X02",
                    "tenant": "other",
                    "title": "OTHER-SENTINEL",
                    "note": "Must not be exported either",
                },
            ],
        }

        result = app.export_rows(
            payload,
            argparse.Namespace()
        )

        records = list(
            csv.reader(
                io.StringIO(result["csv"], newline="")
            )
        )

        exported_row_ids = [
            record[0] for record in records[1:]
        ]

        self.assertEqual(exported_row_ids, ["R01"])

        self.assertNotIn(
            "FOREIGN-SENTINEL",
            result["csv"]
        )

        self.assertNotIn(
            "OTHER-SENTINEL",
            result["csv"]
        )


if __name__ == "__main__":
    unittest.main()
