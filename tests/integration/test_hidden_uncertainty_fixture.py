"""CPU-only integrity checks; not a model experiment."""
import unittest
from hidden_uncertainty_fixture import build, validate


class FixtureIntegrity(unittest.TestCase):
    def test_reproducible(self):
        self.assertEqual(build(42, 32), build(42, 32))

    def test_pair_completeness(self):
        rows = build(42, 32)
        validate(rows, 32)
        self.assertEqual(len(rows), 64)
        self.assertEqual(sum(x["underdetermined"] for x in rows), 32)

    def test_label_balance(self):
        rows = build(42, 32)
        b = [x for x in rows if x["side"] == "B"]
        self.assertEqual(sum(x["gold"] == "YES" for x in b), 16)
        self.assertEqual(sum(x["gold"] == "NO" for x in b), 16)

    def test_reject_missing_pair(self):
        rows = build(42, 32)
        with self.assertRaises(ValueError):
            validate(rows[:-1], 32)

    def test_reject_duplicate(self):
        rows = build(42, 32)
        with self.assertRaises(ValueError):
            validate(rows + [rows[0]], 32)


if __name__ == "__main__":
    unittest.main()
