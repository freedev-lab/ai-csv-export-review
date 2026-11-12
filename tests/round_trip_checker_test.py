
from __future__ import annotations

import argparse
import copy
import csv
import io
import json
import pathlib
import unittest

import app

from csv_checker import COLUMNS, assert_export_matches_policy


ROOT = pathlib.Path(__file__).resolve().parents[1]


# Literal expectations from the README self-check and export-policy.md.
# They are written out by hand so they do not depend on the checker's own
# expected-cell calculation, which mirrors app.encode_cell.
EXPORTED_IDS = ["R01", "R02", "R03", "R04", "R05", "R06", "R07", "R08"]

# csv.reader output for inputs/primary.json (policy "direct").
PRIMARY_RECORDS = [
    ["row_id", "title", "note"],
    ["R01", "Plain title", "comma, note"],        # P5: comma stays in one cell
    ["R02", "'=SUM(1,2)", "line one\nline two"],  # P4 "="; P5 multiline cell
    ["R03", "'+12", 'He said "hello"'],           # P4 "+"; P5 quotes
    ["R04", "'-42", ""],                          # P4 "-"; P3 empty string
    ["R05", "'@lookup", r"\N"],                   # P4 "@"; P3 null
    ["R06", " =not-direct", "\t+not-direct"],     # P4 direct: no skipping
    ["R07", "'=already-text", r"\\N"],            # P4 no re-prefix; P3 literal \N
    ["R08", r"Backslash \\ path", "normal"],      # P3 backslash doubled
]

# The only parsed cells that differ for inputs/secondary.json
# (policy "trim-space-tab"). The other 21 data cells are identical.
SECONDARY_CHANGES = {
    ("R01", "note"): ("comma, note", "comma, revised note"),  # revised text
    ("R06", "title"): (" =not-direct", "' =not-direct"),      # P4 skips space
    ("R06", "note"): ("\t+not-direct", "'\t+not-direct"),     # P4 skips tab
}

SELF_CHECK = {
    "primary.json": {
        "summary": {
            "input_rows": 10,
            "exported_rows": 8,
            "foreign_rows": 2,
            "neutralized_cells": 4,
            "redacted_cells": 0,
        },
        "audit": [
            ("R02", "title"),
            ("R03", "title"),
            ("R04", "title"),
            ("R05", "title"),
        ],
    },
    "secondary.json": {
        "summary": {
            "input_rows": 10,
            "exported_rows": 8,
            "foreign_rows": 2,
            "neutralized_cells": 6,
            "redacted_cells": 0,
        },
        "audit": [
            ("R02", "title"),
            ("R03", "title"),
            ("R04", "title"),
            ("R05", "title"),
            ("R06", "title"),
            ("R06", "note"),
        ],
    },
}


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

    def _parse(self, result):

        return list(
            csv.reader(
                io.StringIO(result["csv"], newline="")
            )
        )

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

    def test_fixtures_match_readme_self_check(self):

        for filename, expected in SELF_CHECK.items():

            with self.subTest(fixture=filename):

                result = self._export_and_check(
                    self._load_fixture(filename)
                )

                records = self._parse(result)

                self.assertEqual(result["summary"], expected["summary"])

                self.assertEqual(
                    [
                        (item["row_id"], item["column"])
                        for item in result["neutralized_cells"]
                    ],
                    expected["audit"]
                )

                # One header plus 8 data records, including the
                # two-line note of R02.
                self.assertEqual(len(records), 9)

                self.assertEqual(
                    [record[0] for record in records[1:]],
                    EXPORTED_IDS
                )

                self.assertEqual(records[2][2], "line one\nline two")

                audit_text = json.dumps(result["neutralized_cells"])

                for marker in (
                    "X01",
                    "X02",
                    "FOREIGN-SENTINEL-ONE",
                    "FOREIGN-SENTINEL-TWO",
                ):
                    self.assertNotIn(marker, result["csv"])
                    self.assertNotIn(marker, audit_text)

    def test_primary_matches_literal_records(self):

        result = self._export_and_check(
            self._load_fixture("primary.json")
        )

        self.assertEqual(
            self._parse(result),
            PRIMARY_RECORDS
        )

    def test_secondary_changes_exactly_three_cells(self):

        primary_records = self._parse(
            self._export_and_check(self._load_fixture("primary.json"))
        )

        secondary_records = self._parse(
            self._export_and_check(self._load_fixture("secondary.json"))
        )

        self.assertEqual(len(primary_records), len(secondary_records))

        changed_cells = {}
        unchanged_count = 0

        for first, second in zip(
            primary_records[1:],
            secondary_records[1:]
        ):

            # Same row identity and order in both fixtures.
            self.assertEqual(first[0], second[0])

            for column_index, column in enumerate(COLUMNS):

                if first[column_index] == second[column_index]:
                    unchanged_count += 1
                else:
                    changed_cells[(first[0], column)] = (
                        first[column_index],
                        second[column_index],
                    )

        self.assertEqual(changed_cells, SECONDARY_CHANGES)

        self.assertEqual(unchanged_count, 21)

    def test_checker_rejects_tampered_results(self):

        payload = self._load_fixture("primary.json")

        good = app.export_rows(
            copy.deepcopy(payload),
            argparse.Namespace()
        )

        tampered_results = {
            "foreign row appended": {
                **good,
                "csv": good["csv"] + "X01,FOREIGN-SENTINEL-ONE,'=foreign\r\n",
            },
            "LF record endings": {
                **good,
                "csv": good["csv"].replace("\r\n", "\n"),
            },
            "apostrophe removed": {
                **good,
                "csv": good["csv"].replace("'+12", "+12"),
            },
            "audit entry missing": {
                **good,
                "neutralized_cells": good["neutralized_cells"][1:],
            },
            "wrong summary count": {
                **good,
                "summary": {**good["summary"], "foreign_rows": 1},
            },
        }

        for name, tampered in tampered_results.items():

            with self.subTest(tampering=name):

                with self.assertRaises(AssertionError):

                    assert_export_matches_policy(
                        self,
                        payload,
                        tampered
                    )


if __name__ == "__main__":
    unittest.main()
