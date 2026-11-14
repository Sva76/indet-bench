"""Chat-template option resolution for the hidden-state extractor; no model download."""
import unittest

from indetbench.hf_runner import chat_prompt
from indetbench.hidden_uncertainty import resolve_model_key


class FakeTokenizer:
    def apply_chat_template(self, messages, tokenize=False, add_generation_prompt=True, **options):
        return "thinking=" + str(options.get("enable_thinking"))


class ResolveModelKeyTests(unittest.TestCase):
    def test_auto_matches_score_pairs_rule(self):
        self.assertEqual(resolve_model_key("auto", "Qwen/Qwen3-8B"), "qwen")
        self.assertEqual(resolve_model_key("auto", "mistralai/Mistral-Nemo-Instruct-2407"), "mistral")
        self.assertEqual(resolve_model_key("auto", "allenai/OLMo-2-1124-7B-Instruct"), "other")

    def test_explicit_key_is_kept(self):
        self.assertEqual(resolve_model_key("other", "Qwen/Qwen2.5-0.5B-Instruct"), "other")

    def test_auto_qwen_disables_thinking(self):
        key = resolve_model_key("auto", "Qwen/Qwen3-8B")
        self.assertEqual(chat_prompt(FakeTokenizer(), "x", model_key=key), "thinking=False")


if __name__ == "__main__":
    unittest.main()
