"""Regression for NumPy integer overflow in exact paired sign test."""
from __future__ import annotations

import importlib.util
from math import comb
from pathlib import Path
import unittest

import numpy as np


class SignOverflowRegression(unittest.TestCase):
    def test_numpy_240_pair_sign_p_correct(self):
        path = Path(__file__).resolve().parents[0] / "integration" / "analyze_smol_stat.py"
        spec = importlib.util.spec_from_file_location("smol_stat_standalone", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        a = np.asarray([1.0] * 115 + [0.0] * 125)
        expected = min(1.0, 2.0 * sum(comb(240, i) for i in range(116)) / (2 ** 240))
        self.assertAlmostEqual(module.sign_p(a), expected, places=12)
        self.assertAlmostEqual(expected, 0.5613667386935357, places=12)
        self.assertAlmostEqual(module.sign_p([1.0] * 120 + [0.0] * 120), 1.0)


if __name__ == "__main__":
    unittest.main()
