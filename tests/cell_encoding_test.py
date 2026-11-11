
from __future__ import annotations

import argparse
import csv
import io
import unittest

import app


class CellEncodingTests(unittest.TestCase):

    def _export(self, rows: list[dict]) -> list[list[str]]:

        payload = {
            "tenant": "fern",
            "policy": "direct",
            "rows": rows,
        }

        result = app.export_rows(
            payload,
            argparse.Namespace()
        )

        return list(
            csv.reader(
                io.StringIO(result["csv"], newline="")
            )
        )

    def test_null_empty_and_literal_backslash_n_remain_distinct(self):

        records = self._export([
            {
                "row_id": "R01",
                "tenant": "fern",
                "title": None,
                "note": "",
            },
            {
                "row_id": "R02",
                "tenant": "fern",
                "title": r"\N",
                "note": "Normal text",
            },
        ])

        self.assertEqual(
            records[1],
            ["R01", r"\N", ""]
        )

        self.assertEqual(
            records[2],
            ["R02", r"\\N", "Normal text"]
        )

    def test_backslashes_are_doubled_and_apostrophes_preserved(self):

        records = self._export([
            {
                "row_id": "R03",
                "tenant": "fern",
                "title": r"C:\Users\O'Brien",
                "note": "It's a good application",
            }
        ])

        self.assertEqual(
            records[1],
            [
                "R03",
                r"C:\\Users\\O'Brien",
                "It's a good application",
            ]
        )


if __name__ == "__main__":
    unittest.main()
