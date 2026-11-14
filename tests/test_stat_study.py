"""Synthetic end-to-end checks of preregistered statistical analysis.

These generated fake scores do NOT represent SmolLM2 inference results.
"""
from __future__ import annotations

import csv
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from indetbench.hf_runner import load_pairs
from indetbench.stat_study import (
    EXPECTED_MODEL, EXPECTED_REVISION, analyze, _holm, _sign_test_two_sided
)


DATA = Path(__file__).resolve().parents[1] / "data" / "smol_stat_v01_frozen.jsonl"


class StatStudyTests(unittest.TestCase):
    def test_frozen_balance_and_fake_score_pipeline(self):
        rows=load_pairs(DATA)
        self.assertEqual(len(rows),480)
        self.assertEqual(len({x["pair_id"] for x in rows}),240)
        with TemporaryDirectory() as tmp:
            scores=Path(tmp)/"fake.csv"
            with scores.open("w",newline="",encoding="utf-8") as f:
                wr=csv.DictWriter(f,fieldnames=["row_id","pair_id","block_id",
                    "side","score","p_yes","p_no","p_unknown","mass_total",
                    "prompt_tokens","model_id","model_revision","parsed"])
                wr.writeheader()
                for row in rows:
                    side=row["side"]
                    y=0.45 if row["gold_response"]=="YES" else 0.05
                    n=0.45 if row["gold_response"]=="NO" else 0.05
                    u=0.8 if side=="C" else 0.05
                    wr.writerow({
                      "row_id":row["row_id"],"pair_id":row["pair_id"],
                      "block_id":row["block_id"],"side":side,
                      "score":u,"p_yes":y,"p_no":n,"p_unknown":u,
                      "mass_total":y+n+u,
                      "prompt_tokens":max(1,len(row["prompt"])//6),
                      "model_id":EXPECTED_MODEL,"model_revision":EXPECTED_REVISION,
                      "parsed":row["gold_response"]})
            report=analyze(DATA,scores,boots=0)
            self.assertEqual(report["sample_pairs"],240)
            self.assertEqual(report["metrics"]["raw_unknown"]["W"]["value"],1.0)
            self.assertEqual(report["behavior"]["B_correct"],240)
            self.assertEqual(report["behavior"]["C_correct_abstention"],240)
            self.assertEqual(report["behavior"]["B_invalid_format"],0)

    def test_exact_sign_test_and_holm(self):
        self.assertAlmostEqual(_sign_test_two_sided([1.0,1.0,0.0]),1.0)
        self.assertEqual(_sign_test_two_sided([0.5,0.5]),1.0)
        adj=_holm({"A":.001,"B":.02,"C":.5})
        self.assertAlmostEqual(adj["A"],.003)
        self.assertAlmostEqual(adj["B"],.04)
        self.assertAlmostEqual(adj["C"],.5)


if __name__=="__main__":
    unittest.main()
