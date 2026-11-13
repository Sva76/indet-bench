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

    def test_report_flags_missing_label_and_low_accuracy(self):
        out = ob.export_rows(self.rows, "PN")
        scores = [{"row_id": o["row_id"], "pair_id": o["pair_id"], "block_id": o["block_id"],
                   "side": o["side"], "score": "0.5", "parsed": "YES",
                   "model_id": "fake", "model_revision": "0" * 40} for o in out]
        rep = ob.report(scores, self.rows, n_bootstrap=0)
        self.assertEqual(rep["W_p_unknown"]["value"], 0.5)
        self.assertIn("label never generated: NO", rep["warnings"])
        self.assertTrue(any("below 0.80" in w for w in rep["warnings"]))

    def test_report_rejects_rows_outside_benchmark(self):
        with self.assertRaisesRegex(ValueError, "not in the frozen benchmark"):
            ob.report([{"row_id": "x", "pair_id": "p", "block_id": "b", "side": "B", "score": "0"}],
                      self.rows, n_bootstrap=0)


if __name__ == "__main__":
    unittest.main()
