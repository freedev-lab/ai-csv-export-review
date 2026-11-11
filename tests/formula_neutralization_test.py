
from __future__ import annotations

import argparse
import csv
import io
import unittest

import app


class FormulaNeutralizationTests(unittest.TestCase):

    def _export(self, policy: str, rows: list[dict]) -> dict:

        payload = {
            "tenant": "fern",
            "policy": policy,
            "rows": rows,
        }

        return app.export_rows(
            payload,
            argparse.Namespace()
        )

    def _parse_csv(self, result: dict) -> list[list[str]]:

        return list(
            csv.reader(
                io.StringIO(result["csv"], newline="")
            )
        )

    def test_direct_policy_checks_all_four_triggers(self):

        rows = [
            {
                "row_id": "=R01",
                "tenant": "fern",
                "title": "+formula",
                "note": "-formula",
            },
            {
                "row_id": "R02",
                "tenant": "fern",
                "title": "@formula",
                "note": "normal text",
            },
            {
                "row_id": "R03",
                "tenant": "fern",
                "title": " =formula",
                "note": "\t+formula",
            },
            {
                "row_id": "R04",
                "tenant": "fern",
                "title": "'@already-prefixed",
                "note": "normal text",
            },
        ]

        result = self._export("direct", rows)

        records = self._parse_csv(result)

        self.assertEqual(
            records,
            [
                ["row_id", "title", "note"],
                ["'=R01", "'+formula", "'-formula"],
                ["R02", "'@formula", "normal text"],
                ["R03", " =formula", "\t+formula"],
                ["R04", "'@already-prefixed", "normal text"],
            ],
        )

        self.assertEqual(
            result["neutralized_cells"],
            [
                {"row_id": "=R01", "column": "row_id"},
                {"row_id": "=R01", "column": "title"},
                {"row_id": "=R01", "column": "note"},
                {"row_id": "R02", "column": "title"},
            ],
        )

    def test_trim_space_tab_policy_skips_only_spaces_and_tabs(self):

        rows = [
            {
                "row_id": "@R01",
                "tenant": "fern",
                "title": " =formula",
                "note": "\t+formula",
            },
            {
                "row_id": "R02",
                "tenant": "fern",
                "title": " \t-formula",
                "note": " @formula",
            },
        ]

        result = self._export("trim-space-tab", rows)

        records = self._parse_csv(result)

        self.assertEqual(
            records,
            [
                ["row_id", "title", "note"],
                ["'@R01", "' =formula", "'\t+formula"],
                ["R02", "' \t-formula", "' @formula"],
            ],
        )

        self.assertEqual(
            result["neutralized_cells"],
            [
                {"row_id": "@R01", "column": "row_id"},
                {"row_id": "@R01", "column": "title"},
                {"row_id": "@R01", "column": "note"},
                {"row_id": "R02", "column": "title"},
                {"row_id": "R02", "column": "note"},
            ],
        )

    def test_trim_policy_does_not_skip_newlines_or_existing_apostrophes(self):

        rows = [
            {
                "row_id": "R03",
                "tenant": "fern",
                "title": "\n=not-trigger",
                "note": " \n@not-trigger",
            },
            {
                "row_id": "R04",
                "tenant": "fern",
                "title": "'=already-prefixed",
                "note": "'@already-prefixed",
            },
        ]

        result = self._export("trim-space-tab", rows)

        self.assertEqual(
            result["neutralized_cells"],
            [],
        )


if __name__ == "__main__":
    unittest.main()
