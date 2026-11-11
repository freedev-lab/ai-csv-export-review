
from __future__ import annotations

import argparse
import copy
import unittest

import app


class RepeatabilityTests(unittest.TestCase):

    def _create_payload(self) -> dict:

        return {
            "tenant": "fern",
            "policy": "direct",
            "rows": [
                {
                    "row_id": "R01",
                    "tenant": "fern",
                    "title": "=SUM(1,2)",
                    "note": "It's a test",
                },
                {
                    "row_id": "X01",
                    "tenant": "other",
                    "title": "Foreign row",
                    "note": "Must remain unchanged",
                },
            ],
        }

    def test_export_does_not_modify_original_payload(self):

        # Arrange
        payload = self._create_payload()

        original_payload = copy.deepcopy(payload)

        # Act
        app.export_rows(
            payload,
            argparse.Namespace()
        )

        # Assert
        self.assertEqual(
            payload,
            original_payload,
            "Exporting must not modify the original input."
        )

    def test_repeated_exports_produce_identical_results(self):

        # Arrange
        payload = self._create_payload()

        arguments = argparse.Namespace()

        # Act
        first_result = app.export_rows(payload, arguments)

        second_result = app.export_rows(payload, arguments)

        # Assert
        self.assertEqual(
            first_result,
            second_result,
            "Repeated exports of the same input must be identical."
        )


if __name__ == "__main__":
    unittest.main()
