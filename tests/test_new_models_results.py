"""The archived new-model results (14 Nov 2026) are recomputed from their per-row scores."""
import hashlib
import json
import unittest
from pathlib import Path

from indetbench.original_benchmark import _read_scores, load_frozen, report

ROOT = Path(__file__).resolve().parents[1] / "results" / "new_models_2026-11-14"


class NewModelsArchive(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = load_frozen()

    def test_sha256sums(self):
        for line in (ROOT / "SHA256SUMS").read_text().splitlines():
            digest, name = line.split(maxsplit=1)
            data = (ROOT / name.strip()).read_bytes()
            self.assertEqual(hashlib.sha256(data).hexdigest(), digest, name)

    def test_report_recomputed_from_scores(self):
        dirs = sorted(p for p in ROOT.iterdir() if p.is_dir())
        self.assertEqual(len(dirs), 5)
        for d in dirs:
            with self.subTest(model=d.name):
                scores = _read_scores(d / "punteggi.csv")
                self.assertEqual(len(scores), 1600)
                archived = json.loads((d / "esito.json").read_text())["report_indetbench"]
                fresh = report(scores, self.rows)
                for key in ("value", "ci_lower", "ci_upper", "n_pairs", "n_blocks"):
                    self.assertAlmostEqual(fresh["W_p_unknown"][key], archived["W_p_unknown"][key], places=12)
                self.assertEqual(fresh["competence_gate"], archived["competence_gate"])
                self.assertEqual(fresh["verdict"], archived["verdict"])
                self.assertEqual(fresh["W_by_family_descriptive"], archived["W_by_family_descriptive"])


if __name__ == "__main__":
    unittest.main()
