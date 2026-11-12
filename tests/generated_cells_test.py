"""Optional stretch: deterministic generated cells through the reusable checker."""

from __future__ import annotations

import argparse
import copy
import random
import unittest

import app

from csv_checker import assert_export_matches_policy


# Characters that stress P3-P5: separators, quotes, CR/LF, backslashes,
# apostrophes, the four triggers, spaces/tabs and non-ASCII text.
ALPHABET = " \t\r\n,\"'\\=+-@Nxé中"

SEED = 315


def _generated_payload(policy: str) -> dict:

    rng = random.Random(SEED)

    def cell():
        if rng.random() < 0.1:
            return None
        return "".join(
            rng.choice(ALPHABET) for _ in range(rng.randint(0, 6))
        )

    rows = []

    for index in range(200):
        rows.append({
            # Unique IDs; some start with a trigger, a space or a backslash.
            "row_id": rng.choice(["", "=", "-", " ", "\\", "'"]) + f"G{index:03d}",
            # Related-name and different-case tenants must be excluded.
            "tenant": rng.choice(["fern", "fern", "fern-archive", "Fern"]),
            "title": cell(),
            "note": cell(),
        })

    return {"tenant": "fern", "policy": policy, "rows": rows}


class GeneratedCellTests(unittest.TestCase):

    def test_generated_cells_round_trip_under_both_policies(self):

        for policy in ("direct", "trim-space-tab"):

            with self.subTest(policy=policy):

                payload = _generated_payload(policy)
                original = copy.deepcopy(payload)

                first = app.export_rows(payload, argparse.Namespace())
                second = app.export_rows(payload, argparse.Namespace())

                self.assertEqual(payload, original)
                self.assertEqual(first, second)

                assert_export_matches_policy(self, original, first)


if __name__ == "__main__":
    unittest.main()
