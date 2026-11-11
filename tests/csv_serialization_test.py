
from __future__ import annotations

import argparse
import csv
import io
import unittest

import app


class CsvSerializationTests(unittest.TestCase):

    def _export(self, title: str, note: str) -> str:
        payload = {
            "tenant": "fern",
            "policy": "direct",
            "rows": [
                {
                    "row_id": "R01",
                    "tenant": "fern",
                    "title": title,
                    "note": note,
                }
            ],
        }

        result = app.export_rows(
            payload,
            argparse.Namespace()
        )

        return result["csv"]

    def test_writer_preserves_commas_quotes_and_embedded_newlines(self):

        csv_text = self._export(
            'Product, "Deluxe"',
            "First line\nSecond line",
        )

        records = list(
            csv.reader(
                io.StringIO(csv_text, newline="")
            )
        )

        self.assertEqual(
            records,
            [
                ["row_id", "title", "note"],
                ["R01", 'Product, "Deluxe"', "First line\nSecond line"],
            ],
        )

    def test_writer_uses_crlf_record_endings(self):

        csv_text = self._export(
            "Product",
            "Simple note"
        )

        self.assertTrue(
            csv_text.endswith("\r\n")
        )

        without_crlf = csv_text.replace("\r\n", "")

        self.assertNotIn("\n", without_crlf)
        self.assertNotIn("\r", without_crlf)


if __name__ == "__main__":
    unittest.main()
