"""Small synthetic tests of Test M-A score discovery and comparison.

The real archived Test M A ZIP is not copied into this repository.
"""
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from zipfile import ZipFile

from indetbench.replay_m_a import _check, _member, _method_scores, _reference


class TestMAReplayTests(unittest.TestCase):
    def test_source_scores_are_taken_from_rows_not_summary(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "mini.zip"
            with ZipFile(path, "w") as z:
                z.writestr("uscite/M1_qwen-abcdef/M1_qwen.json", json.dumps({
                    "riferimento": [
                        {"row_id": "pB", "p_UNKNOWN": 0.1},
                        {"row_id": "pC", "p_UNKNOWN": 0.9}
                    ],
                    "polygraph": [
                        {"row_id": "pB", "u_MSP": 1.0},
                        {"row_id": "pC", "u_MSP": 2.0}
                    ],
                }))
            with ZipFile(path) as z:
                ref = _reference(z, "env_m1", "qwen")
                scores, source = _method_scores(z, "M1-MSP", "qwen")
                self.assertEqual(ref, {"pB": .1, "pC": .9})
                self.assertEqual(scores, {"pB": 1.0, "pC": 2.0})
                self.assertEqual(source, ("env_m1", "qwen"))
                with self.assertRaisesRegex(ValueError, "Expected exactly one"):
                    _member(z, "M1_llama-", "M1_llama.json")

    def test_comparison_counts_ci_and_detects_discrepancies(self):
        original = {"stima": 0.8, "ci95": [0.6, 1.0], "coppie": 800}
        same = {"stima": 0.8, "ci95": [0.6, 1.0], "coppie": 800}
        errors = []
        self.assertEqual(_check("example", original, same, errors), 4)
        self.assertFalse(errors)
        changed = {"stima": 0.7, "ci95": [0.5, 0.9], "coppie": 799}
        _check("example", original, changed, errors)
        self.assertTrue(errors)


if __name__ == "__main__":
    unittest.main()
