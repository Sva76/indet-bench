"""Model-runner input and tokenizer tests; no model download or GPU."""
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from indetbench.hf_runner import chat_prompt, load_pairs, parse_label, token_label_ids, validate_revision


class FakeTokenizer:
    def encode(self, value, add_special_tokens=False):
        idx = {"YES": 1, "NO": 2, "UNKNOWN": 3}[value.strip().upper()]
        return [idx + (10 if value.startswith(" ") else 0)]

    def apply_chat_template(self, messages, tokenize=False, add_generation_prompt=True, **options):
        return messages[0]["content"] + " thinking=" + str(options.get("enable_thinking"))


class HFRunnerTests(unittest.TestCase):
    def test_label_ids_are_disjoint_and_include_space_variants(self):
        ids = token_label_ids(FakeTokenizer())
        self.assertEqual(ids["UNKNOWN"], [3, 13])
        self.assertEqual(ids["YES"], [1, 11])

    def test_qwen_disables_thinking(self):
        self.assertIn("thinking=False", chat_prompt(FakeTokenizer(), "test", model_key="qwen"))
        self.assertIn("thinking=None", chat_prompt(FakeTokenizer(), "test", model_key="other"))

    def test_parse_label(self):
        self.assertEqual(parse_label("  'UNKNOWN'"), "UNKNOWN")
        self.assertEqual(parse_label("Maybe UNKNOWN"), "ALTRO")

    def test_revision_must_be_immutable_commit(self):
        self.assertEqual(validate_revision("A" * 40), "a" * 40)
        for invalid in (None, "", "main", "v1.0.0", "a" * 39, "z" * 40):
            with self.assertRaisesRegex(ValueError, "commit SHA"):
                validate_revision(invalid)

    def test_input_requires_complete_matched_pairs(self):
        rows = [
            {"row_id": "b", "pair_id": "p", "block_id": "story1", "side": "B", "prompt": "x"},
            {"row_id": "c", "pair_id": "p", "block_id": "story1", "side": "C", "prompt": "y"},
        ]
        with TemporaryDirectory() as directory:
            path = Path(directory) / "pairs.jsonl"
            path.write_text("\n".join(json.dumps(x) for x in rows), encoding="utf-8")
            self.assertEqual(len(load_pairs(path)), 2)
            path.write_text(json.dumps(rows[0]), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "complete"):
                load_pairs(path)
            wrong = [rows[0], dict(rows[1], block_id="story2")]
            path.write_text("\n".join(json.dumps(x) for x in wrong), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "inconsistent"):
                load_pairs(path)


if __name__ == "__main__":
    unittest.main()
