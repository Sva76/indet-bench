"""CPU-only synthetic tests; no original Test M or C data redistributed."""
import hashlib
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from zipfile import ZipFile

from indetbench.replay import W, delta_W, make_pairs, sha256, verify, c_archive
from indetbench.archive_safety import check_zip_archive


class ReplayTests(unittest.TestCase):
    def test_pair_w_and_paired_delta(self):
        pairs = {
            "a": {"block": "x", "family": "AND", "B": "aB", "C": "aC"},
            "b": {"block": "x", "family": "AND", "B": "bB", "C": "bC"},
            "c": {"block": "y", "family": "AND", "B": "cB", "C": "cC"},
        }
        method = {"aB": 0, "aC": 1, "bB": 1, "bC": 1, "cB": 2, "cC": 1}
        baseline = {"aB": 0, "aC": 1, "bB": 0, "bC": 1, "cB": 0, "cC": 1}
        w = W(method, pairs, ("AND",), 20261108, 0)
        self.assertAlmostEqual(w["stima"], 0.375)
        self.assertEqual(w["valide"], 3)
        dw = delta_W(method, baseline, pairs, ("AND",), 20261108, 0)
        self.assertAlmostEqual(dw["stima"], -0.625)
        self.assertAlmostEqual(dw["W_riferimento_stesse_coppie"], 1)
        self.assertEqual(dw["coppie"], 3)

    def test_bad_or_incomplete_pairs_rejected(self):
        rows = [
            dict(pair_key="p", kind="B", passaggio_id="x", famiglia="AND", row_id="one"),
            dict(pair_key="p", kind="B", passaggio_id="x", famiglia="AND", row_id="two"),
        ]
        with self.assertRaisesRegex(ValueError, "duplicate"):
            make_pairs(rows)
        with self.assertRaisesRegex(ValueError, "Incomplete"):
            make_pairs(rows[:1])

    def test_mismatch_is_detected_not_overwritten(self):
        errors = []
        verify("sample", {"stima": 0.9, "ci95": [0.8, 1.0]},
               {"stima": 0.4, "ci95": [0.1, 0.9]}, errors)
        self.assertEqual(len(errors), 2)

    def test_sha_changes_with_bytes(self):
        with TemporaryDirectory() as folder:
            path = Path(folder) / "x.txt"
            path.write_text("abc", encoding="utf-8")
            self.assertEqual(sha256(path), hashlib.sha256(b"abc").hexdigest())
            path.write_text("abcd", encoding="utf-8")
            self.assertNotEqual(sha256(path), hashlib.sha256(b"abc").hexdigest())

    def test_zip_archive_size_limits_and_member_paths(self):
        with TemporaryDirectory() as folder:
            path = Path(folder) / "sample.zip"
            with ZipFile(path, "w") as archive:
                archive.writestr("data/observations.json", "test input")
            with ZipFile(path) as archive:
                check_zip_archive(archive)
                with self.assertRaisesRegex(ValueError, "member uncompressed size"):
                    check_zip_archive(archive, max_member_bytes=4)
                with self.assertRaisesRegex(ValueError, "total uncompressed size"):
                    check_zip_archive(archive, max_archive_bytes=4)

            unsafe = Path(folder) / "unsafe.zip"
            with ZipFile(unsafe, "w") as archive:
                archive.writestr("../outside.txt", "bad")
            with ZipFile(unsafe) as archive:
                with self.assertRaisesRegex(ValueError, "unsafe member path"):
                    check_zip_archive(archive)

    def test_incorrect_archive_type_is_rejected(self):
        with TemporaryDirectory() as folder:
            path = Path(folder) / "not_c.zip"
            with ZipFile(path, "w") as archive:
                archive.writestr("README", "not test C")
            with self.assertRaisesRegex(ValueError, "Not the original"):
                with c_archive(path):
                    pass


if __name__ == "__main__":
    unittest.main()
