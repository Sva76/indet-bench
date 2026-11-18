# Copyright (c) 2026 Simona Vargiu. IndetBench.
# Licensed under the PolyForm Noncommercial License 1.0.0. See LICENSE and NOTICE.
"""Tests for the v2 generator (draft). The gold labels are re-derived here from the
prompt text alone, by a parser and a brute-force solver written independently of
indetbench.gen_v2, so a rendering error or a solver error makes the test fail."""
import itertools
import json
import re
import tempfile
import unittest
from pathlib import Path

from indetbench import gen_v2
from indetbench.hf_runner import load_pairs

ITEM_LIST = {
    "all of these hold: ": all,
    "at least one of these holds: ": any,
    "exactly one of these holds: ": lambda v: sum(v) == 1,
    "not all of these hold: ": lambda v: not all(v),
    "either both or neither of these hold: ": lambda v: len(set(v)) == 1,
}
UNCERTAIN = (r"It may be true or false that (.+)\.", r"It is not known whether (.+)\.",
             r"The records do not say whether (.+)\.", r"Nobody has checked whether (.+)\.")


def _literal(text):
    match = re.fullmatch(r"the (\w+) is (not )?(.+)", text)
    return f"the {match.group(1)} is {match.group(3)}", match.group(2) is None


def solve_from_text(prompt):
    """Gold label of a v2 prompt computed from its text only."""
    rules_block = prompt.split("Rules:\n", 1)[1].split("\nFacts:\n", 1)[0]
    facts_block = prompt.split("\nFacts:\n", 1)[1].split("\n\nQuestion: ", 1)[0]
    question = prompt.rsplit("Question: ", 1)[1]
    positive, negative, _, asked = next(d for d in gen_v2.DOMAINS.values() if d[3] == question)
    rules = []
    for line in rules_block.splitlines():
        match = re.fullmatch(r"Rule \d+: (.+?) if and only if (.+)\.", line)
        if not match:
            continue
        head, body = match.group(1), match.group(2)
        if body.startswith("both "):
            func, parts = all, body[len("both "):].split(" and ")
        else:
            prefix = next(p for p in ITEM_LIST if body.startswith(p))
            func, parts = ITEM_LIST[prefix], body[len(prefix):].split("; ")
        rules.append((head[0].lower() + head[1:], func, [_literal(p) for p in parts]))
    known, unknown = {}, []
    for line in facts_block.splitlines():
        match = re.fullmatch(r"It is (true|false) that (.+)\.", line)
        if match:
            known[match.group(2)] = match.group(1) == "true"
            continue
        unknown.append(next(re.fullmatch(p, line).group(1) for p in UNCERTAIN
                            if re.fullmatch(p, line)))
    answers = set()
    for values in itertools.product((False, True), repeat=len(unknown)):
        world = dict(known)
        world.update(zip(unknown, values))
        for head, func, literals in rules:
            world[head] = func([world[clause] == sign for clause, sign in literals])
        root = rules[-1][0]
        assert root in (positive, negative), root
        answers.add(world[root] if root == positive else not world[root])
    return "YES" if answers == {True} else "NO" if answers == {False} else "UNKNOWN"


class GeneratorV2Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pairs, cls.controls = gen_v2.generate(seed=20261118, stories_per_cell=40)

    def test_gold_matches_independent_solver_on_text(self):
        for row in self.pairs + self.controls:
            self.assertEqual(solve_from_text(row["prompt"]), row["gold"], row["row_id"])

    def test_minimal_pairs(self):
        by_pair = {}
        for row in self.pairs:
            by_pair.setdefault(row["pair_id"], {})[row["side"]] = row
        for pair_id, pair in by_pair.items():
            b, c = pair["B"]["prompt"].split(), pair["C"]["prompt"].split()
            self.assertEqual(len(b), len(c), pair_id)
            diffs = [(x, y) for x, y in zip(b, c) if x != y]
            self.assertEqual(len(diffs), 1, pair_id)
            self.assertIn(diffs[0], (("true", "false"), ("false", "true")), pair_id)
            self.assertIn(pair["B"]["gold"], ("YES", "NO"))
            self.assertEqual(pair["C"]["gold"], "UNKNOWN")

    def test_controls_are_determined_and_keep_uncertainty(self):
        for row in self.controls:
            self.assertIn(row["gold"], ("YES", "NO"))
            uncertain = sum(bool(re.fullmatch(p, line)) for line in row["prompt"].splitlines()
                            for p in UNCERTAIN)
            self.assertEqual(uncertain, row["n_uncertain"], row["row_id"])

    def test_draft_shortcut_audit(self):
        report = gen_v2.audit(self.pairs)
        self.assertEqual(report["minimal_pair_violations"], 0)
        # Draft thresholds (spec section 5); the binding values are an owner decision.
        self.assertTrue(0.45 <= report["B_share_YES_overall"] <= 0.55, report["B_share_YES_overall"])
        self.assertTrue(0.45 <= report["W_true_count_overall"] <= 0.55, report["W_true_count_overall"])
        for domain, value in report["W_bow_heldout_domain"].items():
            self.assertTrue(0.40 <= value <= 0.60, (domain, value))

    def test_solver_against_brute_force_definitions(self):
        rng = gen_v2.random.Random(7)
        for _ in range(300):
            level = rng.choice(list(gen_v2.LEVELS))
            knobs = gen_v2.LEVELS[level]
            conditions = gen_v2.random_conditions(knobs["n_vars"], knobs["depth"], rng)
            for values in itertools.product((False, True), repeat=knobs["n_vars"]):
                world = dict(enumerate(values))
                computed = []
                for condition in conditions:
                    items = [world[i[1]] == i[2] if i[0] == "lit" else computed[i[1]]
                             for i in condition.items]
                    expected = {"AND": all(items), "OR": any(items),
                                "EXACTLY_ONE": sum(items) == 1, "NOT_ALL": not all(items),
                                "BOTH_OR_NEITHER": len(set(items)) == 1}[condition.op]
                    computed.append(expected)
                self.assertEqual(gen_v2.evaluate(conditions, world), computed[-1])

    def test_deterministic_and_readable_by_hf_runner(self):
        again, _ = gen_v2.generate(seed=20261118, stories_per_cell=40)
        self.assertEqual(self.pairs, again)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "pairs.jsonl"
            gen_v2._write_jsonl(path, self.pairs)
            self.assertEqual(len(load_pairs(path)), len(self.pairs))

    def test_cli_generate_and_audit(self):
        with tempfile.TemporaryDirectory() as tmp:
            out, ctl = Path(tmp) / "p.jsonl", Path(tmp) / "c.jsonl"
            gen_v2.main(["generate", "--seed", "3", "--stories-per-cell", "2",
                         "--output", str(out), "--controls", str(ctl)])
            rows = [json.loads(line) for line in out.read_text(encoding="utf-8").splitlines()]
            self.assertTrue(rows and all(r["side"] in ("B", "C") for r in rows))
            self.assertEqual(len(ctl.read_text(encoding="utf-8").splitlines()), 2 * 5 * 5)


if __name__ == "__main__":
    unittest.main()
