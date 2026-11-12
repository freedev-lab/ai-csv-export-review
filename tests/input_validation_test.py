
from __future__ import annotations

import argparse
import json
import pathlib
import subprocess
import sys
import tempfile
import unittest

import app


ROOT = pathlib.Path(__file__).resolve().parents[1]


class InputValidationTests(unittest.TestCase):

    def _valid_payload(self):

        return {
            "tenant": "fern",
            "policy": "direct",
            "rows": [
                {
                    "row_id": "R01",
                    "tenant": "fern",
                    "title": "Product",
                    "note": "Valid note",
                }
            ],
        }

    def _run_cli(self, payload):

        return self._run_cli_with_text(json.dumps(payload))

    def _run_cli_with_text(self, text):

        with tempfile.TemporaryDirectory() as directory:

            input_path = pathlib.Path(directory) / "input.json"

            input_path.write_text(
                text,
                encoding="utf-8"
            )

            return subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "app.py"),
                    "--input",
                    str(input_path),
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )

    def test_envelope_rejects_invalid_values(self):

        cases = [
            ("empty tenant", "tenant", "", "invalid export envelope"),
            ("null tenant", "tenant", None, "invalid export envelope"),
            ("numeric tenant", "tenant", 123, "invalid export envelope"),
            ("invalid rows", "rows", None, "invalid export envelope"),
            ("rows must be a list", "rows", {}, "invalid export envelope"),
            ("invalid policy", "policy", "unknown", "invalid consumer policy"),
        ]

        for name, field, value, message in cases:

            with self.subTest(case=name):

                payload = self._valid_payload()
                payload[field] = value

                with self.assertRaisesRegex(ValueError, message):

                    app.export_rows(
                        payload,
                        argparse.Namespace()
                    )

    def test_rows_reject_invalid_structure_and_fields(self):

        valid_row = {
            "row_id": "R01",
            "tenant": "fern",
            "title": "Product",
            "note": "Valid note",
        }

        invalid_rows = [
            ("row must be an object", "not a dictionary"),
            ("missing row_id", {
                "tenant": "fern",
                "title": "Product",
                "note": "Note",
            }),
            ("empty row_id", {
                **valid_row,
                "row_id": "",
            }),
            ("numeric row_id", {
                **valid_row,
                "row_id": 123,
            }),
            ("missing tenant", {
                "row_id": "R01",
                "title": "Product",
                "note": "Note",
            }),
            ("empty tenant", {
                **valid_row,
                "tenant": "",
            }),
            ("numeric tenant", {
                **valid_row,
                "tenant": 123,
            }),
            ("missing title", {
                "row_id": "R01",
                "tenant": "fern",
                "note": "Note",
            }),
            ("invalid title", {
                **valid_row,
                "title": 123,
            }),
            ("missing note", {
                "row_id": "R01",
                "tenant": "fern",
                "title": "Product",
            }),
            ("invalid note", {
                **valid_row,
                "note": [],
            }),
        ]

        for name, row in invalid_rows:

            with self.subTest(case=name):

                payload = self._valid_payload()
                payload["rows"] = [row]

                with self.assertRaisesRegex(
                    ValueError,
                    "invalid row 1"
                ):

                    app.export_rows(
                        payload,
                        argparse.Namespace()
                    )

    def test_duplicate_row_ids_are_rejected(self):

        payload = self._valid_payload()

        payload["rows"].append({
            "row_id": "R01",
            "tenant": "other",
            "title": "Another product",
            "note": "Another note",
        })

        with self.assertRaisesRegex(
            ValueError,
            "duplicate row 2"
        ):

            app.export_rows(
                payload,
                argparse.Namespace()
            )

    def test_null_and_empty_strings_are_valid(self):

        payload = self._valid_payload()

        payload["rows"] = [
            {
                "row_id": "R01",
                "tenant": "fern",
                "title": None,
                "note": "",
            }
        ]

        result = app.export_rows(
            payload,
            argparse.Namespace()
        )

        self.assertIsInstance(result["csv"], str)

    def test_all_rows_are_validated_before_tenant_selection(self):

        payload = self._valid_payload()

        # This row belongs to another tenant.
        # It is still required to pass validation.
        payload["rows"].append({
            "row_id": "FOREIGN_ROW_SECRET",
            "tenant": "other",
            "title": "FOREIGN_TITLE_SECRET",
            "note": 123,
        })

        with self.assertRaisesRegex(
            ValueError,
            "invalid row 2"
        ):

            app.export_rows(
                payload,
                argparse.Namespace()
            )

    def test_cli_error_has_no_stdout_or_cell_values(self):

        payload = self._valid_payload()

        # A valid row comes first.
        payload["rows"][0]["title"] = "VALID_TITLE_SECRET"

        # This foreign row is invalid.
        payload["rows"].append({
            "row_id": "FOREIGN_ROW_SECRET",
            "tenant": "other",
            "title": "FOREIGN_TITLE_SECRET",
            "note": 123,
        })

        process = self._run_cli(payload)

        self.assertEqual(process.returncode, 2)

        self.assertEqual(process.stdout, "")

        self.assertIn(
            "invalid row 2",
            process.stderr
        )

        self.assertNotIn(
            "VALID_TITLE_SECRET",
            process.stderr
        )

        self.assertNotIn(
            "FOREIGN_TITLE_SECRET",
            process.stderr
        )

        self.assertNotIn(
            "FOREIGN_ROW_SECRET",
            process.stderr
        )

    def test_cli_rejects_non_object_json(self):

        process = self._run_cli([])

        self.assertEqual(process.returncode, 2)

        self.assertEqual(process.stdout, "")

        self.assertIn(
            "input must be a JSON object",
            process.stderr
        )

    def test_cli_rejects_excessively_nested_json(self):

        # Valid JSON nested 100,000 levels deep makes json.loads raise
        # RecursionError. P1: a fatal error exits 2 with a readable
        # message, no traceback and no stdout.
        process = self._run_cli_with_text(
            "[" * 100_000 + "]" * 100_000
        )

        self.assertEqual(process.returncode, 2)

        self.assertEqual(process.stdout, "")

        self.assertIn("error:", process.stderr)

        self.assertNotIn("Traceback", process.stderr)


if __name__ == "__main__":
    unittest.main()
