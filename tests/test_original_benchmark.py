import gzip
import tempfile
import unittest
from pathlib import Path

from indetbench import original_benchmark as ob


class OriginalBenchmarkTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = ob.load_frozen()

    def test_frozen_file_hash_and_design(self):
        self.assertEqual(len(self.rows), 4800)
        self.assertEqual({r["set"] for r in self.rows}, {"PN", "SN"})
        self.assertEqual(len({r["story_id"] for r in self.rows}), 200)

    def test_packaged_copy_is_identical_to_archived_original(self):
        if not ob.ARCHIVED_FROZEN.exists():
            self.skipTest("research_originals/ not available (installed package only)")
        self.assertEqual(ob.DEFAULT_FROZEN.read_bytes(), ob.ARCHIVED_FROZEN.read_bytes())

    def test_tampered_file_is_rejected(self):
        raw = gzip.decompress(ob.DEFAULT_FROZEN.read_bytes()).replace(b"approval", b"approvaI", 1)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "x.json.gz"
            path.write_bytes(gzip.compress(raw))
            with self.assertRaisesRegex(ValueError, "SHA-256 mismatch"):
                ob.load_frozen(path)

    def test_export_is_800_complete_pairs_with_unchanged_prompts(self):
        out = ob.export_rows(self.rows, "PN")
        self.assertEqual(len(out), 1600)
        by_id = {r["row_id"]: r for r in self.rows}
        self.assertTrue(all(o["prompt"] == by_id[o["row_id"]]["prompt"] for o in out))
        self.assertEqual({o["gold"] for o in out if o["side"] == "C"}, {"UNKNOWN"})
        self.assertNotIn("UNKNOWN", {o["gold"] for o in out if o["side"] == "B"})
        self.assertEqual(len({o["block_id"] for o in out}), 200)

    def test_report_on_synthetic_scores(self):
        out = ob.export_rows(self.rows, "PN")
        scores = []
        for o in out:
            c = o["side"] == "C"
            scores.append({"row_id": o["row_id"], "pair_id": o["pair_id"], "block_id": o["block_id"],
                           "side": o["side"], "score": "0.9" if c else "0.1",
                           "parsed": "UNKNOWN" if c else o["gold"],
                           "model_id": "fake", "model_revision": "0" * 40})
        rep = ob.report(scores, self.rows, n_bootstrap=0)
        self.assertEqual(rep["W_p_unknown"]["value"], 1.0)
        self.assertEqual(set(rep["W_by_family_descriptive"].values()), {1.0})
        self.assertEqual(rep["behaviour"]["B/AND"]["accuracy"], 1.0)
        self.assertEqual(rep["warnings"], [])
        self.assertTrue(rep["competence_gate"]["passed"])
        self.assertTrue(rep["verdict"].startswith("NO INTERVAL"))

    def test_report_flags_missing_label_and_low_accuracy(self):
        out = ob.export_rows(self.rows, "PN")
        scores = [{"row_id": o["row_id"], "pair_id": o["pair_id"], "block_id": o["block_id"],
                   "side": o["side"], "score": "0.5", "parsed": "UNKNOWN",
                   "model_id": "fake", "model_revision": "0" * 40} for o in out]
        rep = ob.report(scores, self.rows, n_bootstrap=0)
        self.assertEqual(rep["W_p_unknown"]["value"], 0.5)
        self.assertIn("label never generated: NO", rep["warnings"])
        self.assertFalse(rep["competence_gate"]["passed"])
        self.assertTrue(rep["verdict"].startswith("NOT EVALUABLE"))

    def test_constant_yes_answer_passes_overall_part_but_fails_gate(self):
        # 532 of the 800 B cases have gold YES, so always answering YES gives 0.665.
        out = ob.export_rows(self.rows, "PN")
        scores = [{"row_id": o["row_id"], "pair_id": o["pair_id"], "block_id": o["block_id"],
                   "side": o["side"], "score": "0.5", "parsed": "YES",
                   "model_id": "fake", "model_revision": "0" * 40} for o in out]
        rep = ob.report(scores, self.rows, n_bootstrap=0)
        self.assertAlmostEqual(rep["competence_gate"]["accuracy_B"], 532 / 800)
        self.assertEqual(rep["competence_gate"]["accuracy_B_by_gold"], {"NO": 0.0, "YES": 1.0})
        self.assertIn("label never generated: NO", rep["warnings"])
        # The overall part passes, but the per-gold-label part excludes the constant answer.
        self.assertTrue(rep["competence_gate"]["passed_overall"])
        self.assertEqual(rep["competence_gate"]["failed_parts"], ["NO"])
        self.assertFalse(rep["competence_gate"]["passed"])
        self.assertTrue(rep["verdict"].startswith("NOT EVALUABLE"))

    def test_gate_threshold_is_inclusive_and_verdict_rule(self):
        # Exactly 0.50 overall and on each gold label: 134/268 NO and 266/532 YES.
        rep = ob.report(self._scores_with_b_correct({"NO": 134, "YES": 266}), self.rows, n_bootstrap=200)
        self.assertEqual(rep["competence_gate"]["accuracy_B"], 0.5)
        self.assertEqual(rep["competence_gate"]["accuracy_B_by_gold"], {"NO": 0.5, "YES": 0.5})
        self.assertTrue(rep["competence_gate"]["passed"])
        self.assertEqual(rep["verdict"], "CONFIRMED")
        w = {"value": 0.55, "ci_lower": 0.49, "ci_upper": 0.61}
        self.assertEqual(ob.verdict(w, True, "PN"), "NOT CONCLUSIVE")
        self.assertEqual(ob.verdict({"value": 0.4, "ci_lower": 0.3, "ci_upper": 0.5}, True, "PN"),
                         "NOT CONFIRMED")
        self.assertTrue(ob.verdict(w, True, "SN").startswith("DESCRIPTIVE"))

    def _scores_with_b_correct(self, n_correct: dict) -> list[dict]:
        """Synthetic PN scores: the first n_correct[label] B cases of each gold label right,
        the other B cases wrong (ALTRO); C always UNKNOWN with a higher score."""
        out = ob.export_rows(self.rows, "PN")
        seen = {"NO": 0, "YES": 0}
        scores = []
        for o in out:
            if o["side"] == "B":
                seen[o["gold"]] += 1
                parsed = o["gold"] if seen[o["gold"]] <= n_correct[o["gold"]] else "ALTRO"
            else:
                parsed = "UNKNOWN"
            scores.append({"row_id": o["row_id"], "pair_id": o["pair_id"], "block_id": o["block_id"],
                           "side": o["side"], "score": "0.9" if o["side"] == "C" else "0.1",
                           "parsed": parsed, "model_id": "fake", "model_revision": "0" * 40})
        return scores

    def test_b_cases_are_unbalanced_by_gold_label(self):
        out = ob.export_rows(self.rows, "PN")
        counts = {label: sum(o["side"] == "B" and o["gold"] == label for o in out) for label in ("NO", "YES")}
        self.assertEqual(counts, {"NO": 268, "YES": 532})
        self.assertEqual({o["family"] for o in out if o["side"] == "B" and o["gold"] == "NO"}, {"AND"})

    def test_constant_no_answer_fails_overall_and_yes(self):
        rep = ob.report(self._scores_with_b_correct({"NO": 268, "YES": 0}), self.rows, n_bootstrap=0)
        gate = rep["competence_gate"]
        self.assertAlmostEqual(gate["accuracy_B"], 268 / 800)
        self.assertEqual(gate["failed_parts"], ["overall", "YES"])
        self.assertTrue(rep["verdict"].startswith("NOT EVALUABLE"))

    def test_per_label_threshold_is_inclusive_and_binding_when_overall_passes(self):
        # 266/532 = 0.500 on gold YES: passes (inclusive).
        rep = ob.report(self._scores_with_b_correct({"NO": 268, "YES": 266}), self.rows, n_bootstrap=200)
        self.assertEqual(rep["competence_gate"]["accuracy_B_by_gold"]["YES"], 0.5)
        self.assertTrue(rep["competence_gate"]["passed"])
        self.assertEqual(rep["verdict"], "CONFIRMED")
        # 265/532 < 0.50 on gold YES: overall 533/800 = 0.666 passes, the gate does not.
        rep = ob.report(self._scores_with_b_correct({"NO": 268, "YES": 265}), self.rows, n_bootstrap=0)
        gate = rep["competence_gate"]
        self.assertTrue(gate["passed_overall"])
        self.assertEqual(gate["passed_by_gold"], {"NO": True, "YES": False})
        self.assertEqual(gate["failed_parts"], ["YES"])
        self.assertTrue(rep["verdict"].startswith("NOT EVALUABLE"))
        # Same on gold NO: 133/268 < 0.50 fails, 134/268 = 0.50 passes.
        self.assertFalse(ob.report(self._scores_with_b_correct({"NO": 133, "YES": 532}),
                                   self.rows, n_bootstrap=0)["competence_gate"]["passed"])
        self.assertTrue(ob.report(self._scores_with_b_correct({"NO": 134, "YES": 532}),
                                  self.rows, n_bootstrap=0)["competence_gate"]["passed"])

    def test_original_four_models_pass_both_parts_of_the_gate(self):
        for model, counts in ob.REFERENCE_B_ACCURACY_BY_GOLD_PS.items():
            with self.subTest(model=model):
                self.assertEqual({k: v[1] for k, v in counts.items()}, {"NO": 268, "YES": 532})
                overall = (counts["NO"][0] + counts["YES"][0]) / 800
                self.assertAlmostEqual(overall, ob.REFERENCE_B_ACCURACY_PS[model]["all"], places=3)
                rep = ob.report(self._scores_with_b_correct({k: v[0] for k, v in counts.items()}),
                                self.rows, n_bootstrap=0)
                self.assertTrue(rep["competence_gate"]["passed"], model)
                self.assertEqual(rep["competence_gate"]["failed_parts"], [])

    def test_missing_gold_label_fails_gate(self):
        scores = self._scores_with_b_correct({"NO": 268, "YES": 532})
        gold = {r["row_id"]: r for r in self.rows}
        b_yes_only = [s for s in scores if s["side"] == "B" and gold[s["row_id"]]["condition"] == "YES"]
        gate = ob.competence_gate(b_yes_only, gold)
        self.assertIsNone(gate["accuracy_B_by_gold"]["NO"])
        self.assertEqual(gate["n_B_by_gold"]["NO"], 0)
        self.assertFalse(gate["passed"])
        self.assertEqual(gate["failed_parts"], ["NO"])

    def test_report_rejects_rows_outside_benchmark(self):
        with self.assertRaisesRegex(ValueError, "not in the frozen benchmark"):
            ob.report([{"row_id": "x", "pair_id": "p", "block_id": "b", "side": "B", "score": "0"}],
                      self.rows, n_bootstrap=0)


    def _full_scores(self):
        out = ob.export_rows(self.rows, "PN")
        return [{"row_id": o["row_id"], "pair_id": o["pair_id"], "block_id": o["block_id"],
                 "side": o["side"], "score": "0.9" if o["side"] == "C" else "0.1",
                 "parsed": "UNKNOWN" if o["side"] == "C" else o["gold"],
                 "model_id": "fake", "model_revision": "0" * 40} for o in out]

    def test_report_rejects_swapped_sides(self):
        # Before 15 Nov 2026 a swapped side column inverted W (0.975 -> 0.025) without error.
        scores = [dict(s, side={"B": "C", "C": "B"}[s["side"]]) for s in self._full_scores()]
        with self.assertRaisesRegex(ValueError, "identifier mismatches.*side="):
            ob.report(scores, self.rows, n_bootstrap=0)

    def test_report_rejects_wrong_pair_or_block(self):
        scores = self._full_scores()
        scores[0] = dict(scores[0], block_id="V9999")
        with self.assertRaisesRegex(ValueError, "identifier mismatches.*block_id="):
            ob.report(scores, self.rows, n_bootstrap=0)
        scores = self._full_scores()
        scores[0] = dict(scores[0], pair_id=scores[-1]["pair_id"])
        with self.assertRaisesRegex(ValueError, "identifier mismatches.*pair_id="):
            ob.report(scores, self.rows, n_bootstrap=0)

    def test_report_rejects_duplicate_rows(self):
        scores = self._full_scores()
        with self.assertRaisesRegex(ValueError, "more than once"):
            ob.report(scores + scores[:1], self.rows, n_bootstrap=0)

    def test_report_rejects_mixed_models(self):
        scores = self._full_scores()
        mixed = scores[:800] + [dict(s, model_id="other") for s in scores[800:]]
        with self.assertRaisesRegex(ValueError, "mix 2 models"):
            ob.report(mixed, self.rows, n_bootstrap=0)
        mixed = scores[:800] + [dict(s, model_revision="1" * 40) for s in scores[800:]]
        with self.assertRaisesRegex(ValueError, "mix 2 models"):
            ob.report(mixed, self.rows, n_bootstrap=0)

    def test_report_rejects_a_rows(self):
        a_row = next(r for r in self.rows if r["set"] == "PN" and r["kind"] == "A")
        scores = self._full_scores() + [{"row_id": a_row["row_id"], "pair_id": "x", "block_id": "y",
                                         "side": "B", "score": "0"}]
        with self.assertRaisesRegex(ValueError, "not B or C rows"):
            ob.report(scores, self.rows, n_bootstrap=0)

    def test_coverage_rule(self):
        scores = self._full_scores()
        rep = ob.report(scores, self.rows, n_bootstrap=0)
        self.assertEqual(rep["coverage"]["complete_pairs"], 800)
        self.assertTrue(rep["coverage"]["passed"])
        # 760 complete pairs pass (inclusive), 759 give a DESCRIPTIVE outcome.
        pair_ids = sorted({s["pair_id"] for s in scores})
        for keep, passed in ((760, True), (759, False)):
            kept = set(pair_ids[:keep])
            sub = [s for s in scores if s["pair_id"] in kept]
            rep = ob.report(sub, self.rows, n_bootstrap=200)
            with self.subTest(keep=keep):
                self.assertEqual(rep["coverage"]["complete_pairs"], keep)
                self.assertEqual(rep["coverage"]["passed"], passed)
                if passed:
                    self.assertEqual(rep["verdict"], "CONFIRMED")
                else:
                    self.assertTrue(rep["verdict"].startswith("DESCRIPTIVE (coverage"))


if __name__ == "__main__":
    unittest.main()
