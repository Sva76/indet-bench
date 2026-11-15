import csv
import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "results/baseline_intervals_2026-11-15/compute.py"


class BaselineIntervals(unittest.TestCase):
    def test_published_table_is_recomputed(self):
        spec = importlib.util.spec_from_file_location("baseline_intervals", SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        fresh = [{k: str(v) for k, v in row.items()} for row in module.compute()]
        with (SCRIPT.parent / "baseline_intervals.csv").open(newline="", encoding="utf-8") as handle:
            published = list(csv.DictReader(handle))
        self.assertEqual(fresh, published)

    def test_point_estimates_match_the_reports(self):
        with (SCRIPT.parent / "baseline_intervals.csv").open(newline="", encoding="utf-8") as handle:
            rows = {(r["run"], r["model"], r["baseline"]): r for r in csv.DictReader(handle)}
        for run in ("new_models_2026-11-14", "larger_models_2026-11-15"):
            with (ROOT / "results" / run / "riepilogo.csv").open(newline="", encoding="utf-8") as handle:
                for r in csv.DictReader(handle):
                    for col, name in (("W_entropia", "entropy"), ("W_meno_p_max", "neg_p_max"),
                                      ("W_risposta_UNKNOWN", "unknown01")):
                        with self.subTest(run=run, model=r["modello"], baseline=name):
                            self.assertAlmostEqual(float(rows[(run, r["modello"], name)]["W_baseline"]),
                                                   float(r[col]), places=5)


if __name__ == "__main__":
    unittest.main()
