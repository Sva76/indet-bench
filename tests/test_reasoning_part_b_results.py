"""The archived part B results (reasoning models, 16 Nov 2026) are recomputed from their per-row scores."""
import hashlib
import json
import unittest
from pathlib import Path

from indetbench.original_benchmark import _read_scores, load_frozen, report

ROOT = Path(__file__).resolve().parents[1] / "results" / "reasoning_part_B_2026-11-16"


class ReasoningPartBArchive(unittest.TestCase):
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
        self.assertEqual(len(dirs), 3)
        checked = 0
        for d in dirs:
            scores = _read_scores(d / "punteggi.csv")
            esiti = json.loads((d / "esito.json").read_text())["esiti"]
            self.assertEqual(len(scores), 1600 * len(esiti))
            for condition, archived_full in esiti.items():
                with self.subTest(model=d.name, condition=condition):
                    subset = [s for s in scores if s["condizione"] == condition]
                    self.assertEqual(len(subset), 1600)
                    archived = archived_full["report_indetbench"]
                    fresh = report(subset, self.rows)
                    for key in ("value", "ci_lower", "ci_upper", "n_pairs", "n_blocks"):
                        self.assertAlmostEqual(fresh["W_p_unknown"][key], archived["W_p_unknown"][key], places=12)
                    self.assertEqual(fresh["competence_gate"], archived["competence_gate"])
                    self.assertEqual(fresh["verdict"], archived["verdict"])
                    self.assertEqual(fresh["W_by_family_descriptive"], archived["W_by_family_descriptive"])
                    checked += 1
        self.assertEqual(checked, 4)   # Qwen3-8B on and off, Phi-4-reasoning, R1-Distill-Llama-8B


if __name__ == "__main__":
    unittest.main()
