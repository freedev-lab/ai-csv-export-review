
from __future__ import annotations

import argparse
import copy
import csv
import io
import json
import pathlib
import unittest

import app

from csv_checker import assert_export_matches_policy


ROOT = pathlib.Path(__file__).resolve().parents[1]


class RoundTripCheckerTests(unittest.TestCase):

    def _load_fixture(self, filename):

        path = ROOT / "inputs" / filename

        return json.loads(
            path.read_text(encoding="utf-8")
        )

    def _export_and_check(self, payload):

        original = copy.deepcopy(payload)

        result = app.export_rows(
            payload,
            argparse.Namespace()
        )

        assert_export_matches_policy(
            self,
            original,
            result
        )

        return result

    def test_primary_fixture(self):

        payload = self._load_fixture("primary.json")

        self._export_and_check(payload)

    def test_secondary_fixture(self):

        payload = self._load_fixture("secondary.json")

        self._export_and_check(payload)

    def test_empty_input(self):

        payload = {
            "tenant": "fern",
            "policy": "direct",
            "rows": []
        }

        self._export_and_check(payload)

    def test_constructed_boundary_case(self):

        payload = {
            "tenant": "fern",
            "policy": "trim-space-tab",
            "rows": [
                {
                    "row_id": "R01",
                    "tenant": "fern",
                    "title": ' \t+SUM(1,2), "boundary"',
                    "note": "first line\nsecond line; path\\end",
                },
                {
                    "row_id": "@R02",
                    "tenant": "fern",
                    "title": None,
                    "note": r"\N",
                },
                {
                    "row_id": "X01",
                    "tenant": "fern-archive",
                    "title": "FOREIGN-ONLY-MARKER",
                    "note": "=foreign",
                }
            ]
        }

        self._export_and_check(payload)

    def test_two_exports_of_same_object_are_identical(self):

        payload = self._load_fixture("primary.json")

        original = copy.deepcopy(payload)

        arguments = argparse.Namespace()

        first_result = app.export_rows(
            payload,
            arguments
        )

        second_result = app.export_rows(
            payload,
            arguments
        )

        self.assertEqual(payload, original)

        self.assertEqual(
            first_result,
            second_result
        )

        assert_export_matches_policy(
            self,
            original,
            first_result
        )

        assert_export_matches_policy(
            self,
            original,
            second_result
        )

    def test_secondary_changes_some_cells_and_preserves_others(self):

        primary = self._load_fixture("primary.json")
        secondary = self._load_fixture("secondary.json")

        primary_result = self._export_and_check(primary)
        secondary_result = self._export_and_check(secondary)

        primary_records = list(
            csv.reader(
                io.StringIO(primary_result["csv"], newline="")
            )
        )

        secondary_records = list(
            csv.reader(
                io.StringIO(secondary_result["csv"], newline="")
            )
        )

        changed_cells = []
        unchanged_cells = []

        for first, second in zip(
            primary_records[1:],
            secondary_records[1:]
        ):

            for column in range(len(first)):

                if first[column] == second[column]:
                    unchanged_cells.append(first[column])
                else:
                    changed_cells.append(
                        (first[0], column)
                    )

        self.assertTrue(
            changed_cells,
            "The secondary fixture should change at least one cell."
        )

        self.assertTrue(
            unchanged_cells,
            "The secondary fixture should preserve some cells."
        )


if __name__ == "__main__":
    unittest.main()
