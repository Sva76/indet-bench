"""Competence condition on the 240-pair corpus; synthetic reports only."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "integration"))
from competence_gate_240 import binomial_upper_tail, gate  # noqa: E402


def report(overall, yes, no):
    return {"model": "m", "pairs": 240,
            "behavior": {"B_accuracy": overall},
            "subgroups": {"B_gold": {"YES": {"B_accuracy": yes, "pairs": 120},
                                      "NO": {"B_accuracy": no, "pairs": 120}}},
            "primary": {"W": 0.6, "ci95": [0.5, 0.7]}, "auroc": {"value": 0.6}}


class GateTests(unittest.TestCase):
    def test_official_is_inclusive_and_per_label(self):
        self.assertEqual(gate(report(0.5, 0.5, 0.5))["official_verdict"], "EVALUABLE (EXPLORATORY)")
        g = gate(report(0.625, 0.3833333333333333, 0.8666666666666667))
        self.assertEqual(g["official_verdict"], "NOT EVALUABLE")
        self.assertEqual(g["official_failed_parts"], ["gold_YES"])
        self.assertTrue(g["theoretical_only_would_be_evaluable"])

    def test_constant_answer_fails_both(self):
        g = gate(report(0.5, 1.0, 0.0))
        self.assertEqual(g["official_failed_parts"], ["gold_NO"])
        self.assertFalse(g["theoretical_only_would_be_evaluable"])

    def test_chance_is_strict(self):
        third = 40 / 120
        self.assertFalse(gate(report(third, third, third))["theoretical_only_would_be_evaluable"])

    def test_binomial_tail(self):
        self.assertAlmostEqual(binomial_upper_tail(0, 10, 1 / 3), 1.0)
        self.assertAlmostEqual(binomial_upper_tail(46, 120, 1 / 3), 0.1436768, places=5)


if __name__ == "__main__":
    unittest.main()
