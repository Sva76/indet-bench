"""The original Step 2 output archives committed in research_originals/step2/outputs/ (published 15 Nov 2026)."""
import csv
import gzip
import hashlib
import io
import json
import unittest
import zipfile
from pathlib import Path

from indetbench.original_benchmark import REFERENCE_W_PS, export_rows, load_frozen, report

ROOT = Path(__file__).resolve().parents[1] / "research_originals" / "step2"
OUT = ROOT / "outputs"
EXPECTED = {
    "testU2_risultati.zip": "dbcd61faa7ba0b6bdade866fc8d130eb21d4a6d7c471e9e2c9a7b8537d999433",
    "testM_A_risultati_completo_senza_triviaqa.zip": "fa9577bea44135e06f4583dc80fb9400929dde240063c7a9e5918eb66016e033",
    "testM_B_risultati_completo.zip": "a78cf5a02566d22de80acf8fff6caff0fa0049c697abbbf27667b807648cea3a",
    "completo_Drive_20261113.zip": "da84d9bfb81df8ef15c39524b9e507ffa13eb1e563ce18715b432a1638b5bbed",
}
MODEL_KEYS = {"qwen": "Qwen/Qwen3-8B", "mistral": "mistralai/Mistral-Nemo", "olmo": "allenai/OLMo-2", "llama": "meta-llama/Llama-3.1"}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


class OriginalArchives(unittest.TestCase):
    def test_archive_hashes(self):
        for name, digest in EXPECTED.items():
            self.assertEqual(sha(OUT / name), digest, name)

    def test_righe_c_selection(self):
        data = gzip.decompress((ROOT / "test_c_selection" / "righe_C.json.gz").read_bytes())
        self.assertEqual(hashlib.sha256(data).hexdigest(),
                         "4586e18f4e589505b63699ac91117a927d8bdfc965506a4e3d73920e2e6b0b42")

    def test_triviaqa_rows_removed_only(self):
        with zipfile.ZipFile(OUT / "testM_A_risultati_completo_senza_triviaqa.zip") as z:
            names = set(z.namelist())
        self.assertNotIn("dati/triviaqa.json", names)
        self.assertEqual(len(names), 51)

    def test_u2_published_w_recomputed(self):
        frozen = export_rows(load_frozen(), "PN")
        by_id = {r["row_id"]: r for r in frozen}
        with zipfile.ZipFile(OUT / "testU2_risultati.zip") as z:
            rows = list(csv.DictReader(io.TextIOWrapper(z.open("punteggi.csv"), encoding="utf-8")))
            archived = json.loads(z.read("esiti.json"))["modelli"]
        for key, prefix in MODEL_KEYS.items():
            with self.subTest(model=key):
                scores = []
                for r in rows:
                    if r["modello"] == key and r["row_id"] in by_id:
                        g = by_id[r["row_id"]]
                        scores.append({"row_id": r["row_id"], "pair_id": g["pair_id"], "block_id": g["block_id"],
                                       "side": g["side"], "score": r["p_UNKNOWN"], "parsed": r["parsed"]})
                self.assertEqual(len(scores), 1600)
                w = report(scores, load_frozen())["W_p_unknown"]
                # exact archived U2 estimate (HI1, set PN) and the rounded published reference
                self.assertAlmostEqual(w["value"], archived[key]["HI1"]["stima"], places=12)
                (ref,) = [v for k, v in REFERENCE_W_PS.items() if k.startswith(prefix)]
                self.assertLessEqual(abs(w["value"] - ref[0]), 0.0005 + 1e-12)



try:
    import numpy  # noqa: F401
    from indetbench.replay import replay_c, replay_m_b
    from indetbench.replay_m_a import replay_m_a
except ImportError:  # replay extra not installed
    replay_c = None


@unittest.skipIf(replay_c is None, "needs the [replay] extra (NumPy)")
class ReplayCommittedArchives(unittest.TestCase):
    def test_replay_c(self):
        r = replay_c(OUT / "completo_Drive_20261113.zip")
        self.assertTrue(r["passed"]); self.assertEqual(r["statistics_checked"], 508)

    def test_replay_m_a(self):
        r = replay_m_a(OUT / "testM_A_risultati_completo_senza_triviaqa.zip")
        self.assertTrue(r["passed"]); self.assertEqual(r["numeric_values_checked"], 498)

    def test_replay_m_b(self):
        r = replay_m_b(OUT / "testM_B_risultati_completo.zip")
        self.assertTrue(r["passed"]); self.assertEqual(r["statistics_checked"], 176)


if __name__ == "__main__":
    unittest.main()
