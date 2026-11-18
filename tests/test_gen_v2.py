# Copyright (c) 2026 Simona Vargiu. IndetBench.
# Licensed under the PolyForm Noncommercial License 1.0.0. See LICENSE and NOTICE.
"""Tests for the v2 generator (draft). The gold labels are re-derived here from the
prompt text alone, by a parser and a brute-force solver written independently of
indetbench.gen_v2, so a rendering error or a solver error makes the test fail."""
import itertools
import json
from collections import Counter
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


def parse_text(prompt):
    """Rules [(head, function, [(clause, positive)])], known facts, uncertain facts,
    and the positive and negative outcome clauses, from the prompt text only."""
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
    return rules, known, unknown, positive, negative


def solve_from_text(prompt):
    """Gold label of a v2 prompt computed from its text only."""
    rules, known, unknown, positive, negative = parse_text(prompt)
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
        report = gen_v2.audit(self.pairs, baselines=False)
        self.assertEqual(report["minimal_pair_violations"], 0)
        # Draft thresholds (spec section 5); the binding values are an owner decision.
        self.assertTrue(0.45 <= report["B_share_YES_overall"] <= 0.55, report["B_share_YES_overall"])
        self.assertTrue(0.45 <= report["W_true_count_overall"] <= 0.55, report["W_true_count_overall"])
        for level, share in report["C_share_flipped_satisfied_by_level"].items():
            self.assertTrue(0.45 <= share <= 0.55, (level, share))
        for cell in report["subcells_fine"].values():
            self.assertGreater(cell["n_pairs"], 0)

    def test_metadata_matches_text(self):
        """Flipped-fact sign, location, satisfaction and shallow counts, re-derived from text."""
        by_pair = {}
        for row in self.pairs:
            by_pair.setdefault(row["pair_id"], {})[row["side"]] = row
        for pair in by_pair.values():
            b, c = pair["B"], pair["C"]
            rules, b_known, _, _, _ = parse_text(b["prompt"])
            _, c_known, _, _, _ = parse_text(c["prompt"])
            changed = [k for k in b_known if b_known[k] != c_known.get(k)]
            self.assertEqual(len(changed), 1, b["row_id"])  # found from the text, not the metadata
            fact = changed[0]
            hits = [(i, sign, rules[i][1]) for i, (_, _, lits) in enumerate(rules)
                    for clause, sign in lits if clause == fact]
            self.assertEqual(len(hits), 1, b["row_id"])
            index, sign, _ = hits[0]
            ops = {"AND", "OR", "EXACTLY_ONE", "NOT_ALL", "BOTH_OR_NEITHER"}
            for row in (b, c):
                self.assertEqual(row["flipped_fact"], fact)
                self.assertEqual(row["c_flipped_word"], "true" if c_known[fact] else "false")
                self.assertEqual(row["flipped_rule"], index)
                self.assertIn(row["flipped_rule_op"], ops)
                self.assertEqual(row["flipped_rule_op"], row["ops"][index])
                self.assertEqual(row["flipped_sign"], "positive" if sign else "negative")
                self.assertEqual(row["flipped_location"],
                                 "root" if index == len(rules) - 1 else "intermediate")
                self.assertEqual(row["c_flipped_satisfied"], c_known[fact] == sign)
            for row in (b, c):
                rules, known, unknown, _, _ = parse_text(row["prompt"])
                counts = Counter()
                for i, (_, _, lits) in enumerate(rules):
                    for clause, sgn in lits:
                        kind = ("unc" if clause in unknown else "sat" if known.get(clause) == sgn
                                else "unsat" if clause in known else "ref")
                        if kind == "ref":
                            continue
                        counts[f"all_{kind}"] += 1
                        if i == len(rules) - 1:
                            counts[f"root_{kind}"] += 1
                for key in ("root_sat", "root_unsat", "root_unc", "all_sat", "all_unsat", "all_unc"):
                    self.assertEqual(row["shallow"][key], counts[key], (row["row_id"], key))
                heads = {head for head, _, _ in rules}
                for i, (_, _, lits) in enumerate(rules):
                    per = row["shallow"]["rules"][i]
                    self.assertEqual(per["op"], row["ops"][i])
                    expected = Counter()
                    for clause, sgn in lits:
                        if clause in heads:
                            expected["refs"] += 1
                        elif clause in unknown:
                            expected["unc"] += 1
                        elif known[clause] == sgn:
                            expected["sat"] += 1
                        else:
                            expected["unsat"] += 1
                    for key in ("sat", "unsat", "unc", "refs"):
                        self.assertEqual(per[key], expected[key], (row["row_id"], i, key))

    def test_integrity_errors(self):
        good = [dict(r) for r in self.pairs[:4]]
        cases = {
            "duplicate row": good + [dict(good[0])],
            "incomplete pair": good[:3],
            "side D in pair file": good + [{**good[0], "row_id": "x|D", "pair_id": "x", "side": "D"}],
            "pair across stories": good[:1] + [{**good[1], "block_id": "other"}] + good[2:],
            "missing field": good[:3] + [{k: v for k, v in good[3].items() if k != "pair_id"}],
            "blank id": good[:3] + [{**good[3], "block_id": " "}],
            "non-object record": good + [None],
            "B and C disagree": [good[0], {**good[1], "flipped_rule_op": "OR" if good[0]["flipped_rule_op"] != "OR" else "AND"}] + good[2:],
        }
        for name, rows in cases.items():
            with self.assertRaises(ValueError, msg=name):
                gen_v2.audit(rows, baselines=False)

    def test_minimal_pair_check_rejects_other_changes(self):
        b = next(r for r in self.pairs if r["side"] == "B")
        c = next(r for r in self.pairs if r["pair_id"] == b["pair_id"] and r["side"] == "C")
        self.assertTrue(gen_v2.minimal_pair_ok(b["prompt"], c["prompt"]))
        # One word changed in a rule instead of a fact value: same word count, one diff.
        rule_line = next(l for l in b["prompt"].splitlines() if l.startswith("Rule 1:"))
        word = rule_line.split()[-1]
        broken = b["prompt"].replace(rule_line, rule_line[: -len(word)] + "x" + word, 1)
        self.assertFalse(gen_v2.minimal_pair_ok(b["prompt"], broken))
        rows = [b, {**c, "prompt": broken}]
        self.assertGreater(gen_v2.audit(rows, baselines=False)["minimal_pair_violations"], 0)

    def test_ids_bind_to_dataset(self):
        other, _ = gen_v2.generate(seed=20261117, stories_per_cell=40)
        self.assertFalse({r["row_id"] for r in other} & {r["row_id"] for r in self.pairs})
        reordered, _ = gen_v2.generate(seed=20261118, stories_per_cell=40,
                                       domains=tuple(reversed(gen_v2.DOMAINS)))
        self.assertFalse({r["row_id"] for r in reordered} & {r["row_id"] for r in self.pairs})
        scores = [{"row_id": r["row_id"], "pair_id": r["pair_id"], "block_id": r["block_id"],
                   "side": r["side"], "parsed": "YES"} for r in other]
        with self.assertRaises(ValueError):
            gen_v2.report(self.pairs, scores, n_bootstrap=10)

    def test_flip_location_constraint(self):
        pairs, _ = gen_v2.generate(seed=5, stories_per_cell=8, flip_location="intermediate")
        for row in pairs:
            if row["depth"] >= 2:
                self.assertEqual(row["flipped_location"], "intermediate", row["row_id"])
                self.assertEqual(row["flip_location_constraint"], "intermediate")
            else:
                self.assertEqual(row["flip_location_constraint"], "any")
            self.assertEqual(solve_from_text(row["prompt"]), row["gold"])
        with self.assertRaises(ValueError):
            gen_v2.make_story("x", level=1, domain="approval", marker=0, target="YES",
                              rng=gen_v2.random.Random(0), flip_location="intermediate")

    def test_folds_never_share_units(self):
        table = gen_v2.pairs_by_id(self.pairs)
        for key in (lambda p: p["B"]["block_id"],
                    lambda p: (p["B"]["level"], tuple(p["B"]["ops"]), p["B"]["outcome_polarity"])):
            folds = gen_v2._folds(table, key, 5, 1)
            unit_folds = {}
            for pid, pair in table.items():
                unit_folds.setdefault(key(pair), set()).add(folds[pid])
            self.assertTrue(all(len(f) == 1 for f in unit_folds.values()))

    def test_heldout_baselines_shape(self):
        small, _ = gen_v2.generate(seed=11, stories_per_cell=8)
        result = gen_v2.heldout_baselines(small, n_bootstrap=50)
        for name in ("bow_nb|story_folds", "bow_nb|domain_held_out",
                     "shallow_with_operator|story_folds", "shallow_without_operator|story_folds",
                     "shallow_without_operator|structure_folds"):
            self.assertEqual(set(result[name]), {f"L{l}" for l in gen_v2.LEVELS})
            for value in result[name].values():
                self.assertTrue(0.0 <= value["W"] <= 1.0)


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

    def test_confirmation_files_checksum(self):
        """The four confirmation files of results/v2_draft_audit_2026-11-18 are rebuilt bit for bit."""
        import hashlib
        expected = {
            ("any", "pairs"): "9c1358c8a978ab0750f8fb877b6cd26c7b8cd54d59d64b0c7f05bc4728a0e6ba",
            ("any", "controls"): "ceeb73f42adf844951bc2c88dea6973252e85e08c2898b756c627f01684550f7",
            ("intermediate", "pairs"): "f8da8b118bcd944551910bf2dacd949d50357caf8ed91cc102e8876a53d989e1",
            ("intermediate", "controls"): "2e8c19f21e112807a71d21a285c4b65fd52167697fe3f99c2294d5cc717f6294",
        }
        for loc in ("any", "intermediate"):
            pairs, controls = gen_v2.generate(seed=20261119, stories_per_cell=40,
                                              flip_location=None if loc == "any" else loc)
            for kind, rows in (("pairs", pairs), ("controls", controls)):
                with tempfile.TemporaryDirectory() as tmp:
                    path = Path(tmp) / "f.jsonl"
                    gen_v2._write_jsonl(path, rows)
                    digest = hashlib.sha256(path.read_bytes()).hexdigest()
                self.assertEqual(digest, expected[(loc, kind)], (loc, kind))

    def test_cli_generate_and_audit(self):
        with tempfile.TemporaryDirectory() as tmp:
            out, ctl = Path(tmp) / "p.jsonl", Path(tmp) / "c.jsonl"
            gen_v2.main(["generate", "--seed", "3", "--stories-per-cell", "2",
                         "--output", str(out), "--controls", str(ctl)])
            rows = [json.loads(line) for line in out.read_text(encoding="utf-8").splitlines()]
            self.assertTrue(rows and all(r["side"] in ("B", "C") for r in rows))
            self.assertEqual(len(ctl.read_text(encoding="utf-8").splitlines()), 2 * 5 * 5)


def _scores(rows, *, score, parsed, mass=1.0, model="m", drop=()):
    return [{"row_id": r["row_id"], "pair_id": r["pair_id"], "block_id": r["block_id"],
             "side": r["side"], "score": str(score(r)), "parsed": parsed(r),
             "mass_total": str(mass), "prompt_tokens": "100", "model_id": model,
             "model_revision": "0" * 40}
            for r in rows if r["row_id"] not in drop]


class ReportV2Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pairs, cls.controls = gen_v2.generate(seed=21, stories_per_cell=12)

    def run_report(self, scores, **kw):
        return gen_v2.report(self.pairs, scores, n_bootstrap=200, **kw)

    def test_oracle_model(self):
        scores = _scores(self.pairs, score=lambda r: float(r["gold"] == "UNKNOWN"),
                         parsed=lambda r: r["gold"])
        answers = [{"row_id": r["row_id"], "parsed": r["gold"]} for r in self.controls]
        result = self.run_report(scores, control_rows=self.controls, control_answers=answers)
        for level, entry in result["levels"].items():
            self.assertEqual(entry["status"], "CONFIRMED", level)
            self.assertEqual(entry["W_p_unknown"]["W"], 1.0)
            self.assertEqual(entry["W_generated_answer"]["W"], 1.0)
            self.assertEqual(entry["accuracy_B"]["share"], 1.0)
            self.assertEqual(entry["abstention_C"]["share"], 1.0)
            self.assertEqual(entry["false_abstention_B"]["share"], 0.0)
            self.assertEqual(entry["false_abstention_D"]["share"], 0.0)
            self.assertEqual(entry["accuracy_D"]["share"], 1.0)

    def test_statuses_are_distinct_from_negative_results(self):
        right = lambda r: r["gold"]
        flat = _scores(self.pairs, score=lambda r: 0.3, parsed=right)
        self.assertTrue(all(e["status"] == "NOT CONFIRMED" for e in self.run_report(flat)["levels"].values()))
        low_mass = _scores(self.pairs, score=lambda r: 0.3, parsed=right, mass=0.2)
        self.assertTrue(all(e["status"] == "NOT MEASURABLE" for e in self.run_report(low_mass)["levels"].values()))
        always_yes = _scores(self.pairs, score=lambda r: float(r["gold"] == "UNKNOWN"),
                             parsed=lambda r: "YES")
        self.assertTrue(all(e["status"] == "NOT EVALUABLE" for e in self.run_report(always_yes)["levels"].values()))
        drop = {r["row_id"] for r in self.pairs if r["side"] == "C"}
        drop = set(sorted(drop)[: len(drop) // 5])
        partial = _scores(self.pairs, score=lambda r: float(r["gold"] == "UNKNOWN"), parsed=right, drop=drop)
        statuses = {e["status"] for e in self.run_report(partial)["levels"].values()}
        self.assertIn("DESCRIPTIVE", statuses)

    def test_answers_only_file(self):
        rows = [{"row_id": r["row_id"], "pair_id": r["pair_id"], "block_id": r["block_id"],
                 "side": r["side"], "parsed": r["gold"]} for r in self.pairs]
        result = self.run_report(rows)
        self.assertFalse(result["has_probability_scores"])
        for entry in result["levels"].values():
            self.assertEqual(entry["status"], "ANSWERS ONLY")
            self.assertNotIn("W_p_unknown", entry)
            self.assertEqual(entry["W_generated_answer"]["W"], 1.0)

    def test_answer_measures_use_all_scored_rows(self):
        """A B answer counts even when its C partner is missing."""
        level1 = [r for r in self.pairs if r["level"] == 1]
        no_b = [r for r in level1 if r["side"] == "B" and r["gold"] == "NO"]
        wrong = {r["row_id"] for r in no_b[: len(no_b) // 2 + 1]}
        drop = {r["pair_id"] for r in no_b if r["row_id"] in wrong}
        scores = _scores(self.pairs, score=lambda r: 0.5,
                         parsed=lambda r: "YES" if r["row_id"] in wrong else r["gold"],
                         drop={r["row_id"] for r in self.pairs if r["side"] == "C" and r["pair_id"] in drop})
        entry = self.run_report(scores)["levels"]["L1"]
        self.assertEqual(entry["accuracy_B_gold_NO"]["n"], len(no_b))
        self.assertLess(entry["accuracy_B_gold_NO"]["share"], 0.5)
        self.assertEqual(entry["status"], "NOT EVALUABLE")

    def test_median_and_nonfinite_mass(self):
        masses = iter([0.1, 0.1, 0.8, 0.8] * 10000)
        rows = _scores(self.pairs, score=lambda r: float(r["gold"] == "UNKNOWN"), parsed=lambda r: r["gold"])
        for row in rows:
            row["mass_total"] = str(next(masses))
        for entry in self.run_report(rows)["levels"].values():
            self.assertEqual(entry["status"], "NOT MEASURABLE")  # median 0.45
        rows[0]["mass_total"] = "nan"
        with self.assertRaises(ValueError):
            self.run_report(rows)

    def test_primary_population_sets_coverage_and_splits(self):
        rows = _scores(self.pairs, score=lambda r: float(r["gold"] == "UNKNOWN"), parsed=lambda r: r["gold"])
        b_ids = sorted(r["row_id"] for r in self.pairs if r["side"] == "B")
        mismatched = set(b_ids[: len(b_ids) // 4])
        for row in rows:
            if row["row_id"] in mismatched:
                row["prompt_tokens"] = "101"
        result = self.run_report(rows)
        self.assertIn("DESCRIPTIVE", {e["status"] for e in result["levels"].values()})
        for entry in result["levels"].values():
            self.assertLessEqual(entry["n_pairs_primary"], entry["n_pairs_complete"])
            for split in entry["by_flipped_location"].values():
                self.assertIn("W_p_unknown_sensitivity_all_lengths", split)
                self.assertIn("W_generated_answer", split)
                self.assertIn("false_abstention_B", split)

    def test_length_check_rules(self):
        rows = _scores(self.pairs, score=lambda r: float(r["gold"] == "UNKNOWN"), parsed=lambda r: r["gold"])
        for row in rows:
            if row["side"] == "C":
                row["prompt_tokens"] = "0100"  # same count as "100"
        for entry in self.run_report(rows)["levels"].values():
            self.assertEqual(entry["n_pairs_primary"], entry["n_pairs_complete"])
            self.assertEqual(entry["status"], "CONFIRMED")
        no_len = [{k: v for k, v in r.items() if k != "prompt_tokens"} for r in rows]
        for entry in self.run_report(no_len)["levels"].values():
            self.assertEqual(entry["status"], "DESCRIPTIVE")
            self.assertIn("prompt_tokens", entry["status_reason"])
        bad = [dict(r) for r in rows]
        bad[0]["prompt_tokens"] = "-3"
        with self.assertRaises(ValueError):
            self.run_report(bad)

    def test_coverage_gate_on_counts(self):
        level = [r for r in self.pairs if r["level"] == 2]
        pair_ids = sorted({r["pair_id"] for r in level})
        n = len(pair_ids)
        keep = int(0.95 * n) - 1 if int(0.95 * n) == 0.95 * n else int(0.95 * n)  # strictly below 95%
        drop = {r["row_id"] for r in level if r["side"] == "C" and r["pair_id"] in set(pair_ids[keep:])}
        rows = _scores(self.pairs, score=lambda r: float(r["gold"] == "UNKNOWN"), parsed=lambda r: r["gold"],
                       drop=drop)
        entry = self.run_report(rows)["levels"]["L2"]
        self.assertLess(entry["n_pairs_primary"], 0.95 * n)
        self.assertEqual(entry["status"], "DESCRIPTIVE")

    def test_coverage_that_rounds_to_95_percent(self):
        """1,019 pairs, 968 complete: 0.94995 displays as 0.95 but is below the gate."""
        many, _ = gen_v2.generate(seed=31, stories_per_cell=110, levels=(2,))
        keep = sorted({r["pair_id"] for r in many})[:1019]
        pairs = [r for r in many if r["pair_id"] in set(keep)]
        drop = {r["row_id"] for r in pairs if r["side"] == "C" and r["pair_id"] in set(keep[968:])}
        rows = _scores(pairs, score=lambda r: float(r["gold"] == "UNKNOWN"), parsed=lambda r: r["gold"], drop=drop)
        entry = gen_v2.report(pairs, rows, n_bootstrap=50)["levels"]["L2"]
        self.assertEqual(entry["coverage_primary"], 0.95)
        self.assertEqual(entry["status"], "DESCRIPTIVE")

    def test_one_shot_iterables(self):
        pairs, controls = gen_v2.generate(seed=5, stories_per_cell=2, levels=iter([1]),
                                          domains=iter(["approval"]))
        same, _ = gen_v2.generate(seed=5, stories_per_cell=2, levels=(1,), domains=("approval",))
        self.assertTrue(pairs and controls)
        self.assertEqual(pairs, same)

    def test_control_story_checks(self):
        rows = _scores(self.pairs, score=lambda r: 0.5, parsed=lambda r: r["gold"])
        copy = dict(self.controls[0], row_id="copy|D", pair_id="copy|D")
        wrong_level = [dict(self.controls[0], level=self.controls[0]["level"] + 1)] + self.controls[1:]
        for controls in (self.controls + [copy], wrong_level):
            answers = [{"row_id": r["row_id"], "parsed": r["gold"]} for r in controls]
            with self.assertRaises(ValueError):
                self.run_report(rows, control_rows=controls, control_answers=answers)

    def test_missing_metadata_is_rejected(self):
        broken = [{k: v for k, v in r.items() if k != "c_flipped_satisfied"} for r in self.pairs]
        with self.assertRaises(ValueError):
            gen_v2.audit(broken, baselines=False)
        mixed = [dict(r) for r in self.pairs]
        mixed[0]["sat_both_available"] = not mixed[0]["sat_both_available"]
        with self.assertRaises(ValueError):
            gen_v2.audit(mixed, baselines=False)

    def test_controls_from_another_dataset(self):
        rows = _scores(self.pairs, score=lambda r: 0.5, parsed=lambda r: r["gold"])
        _, other_controls = gen_v2.generate(seed=22, stories_per_cell=12)
        answers = [{"row_id": r["row_id"], "parsed": r["gold"]} for r in other_controls]
        with self.assertRaises(ValueError):
            self.run_report(rows, control_rows=other_controls, control_answers=answers)

    def test_control_file_checks(self):
        rows = _scores(self.pairs, score=lambda r: 0.5, parsed=lambda r: r["gold"])
        answers = [{"row_id": r["row_id"], "parsed": r["gold"], "model_id": "other",
                    "model_revision": "1" * 40} for r in self.controls]
        with self.assertRaises(ValueError):
            self.run_report(rows, control_rows=self.controls, control_answers=answers)
        dup = self.controls + [dict(self.controls[0], gold="NO" if self.controls[0]["gold"] == "YES" else "YES")]
        two_col = [{"row_id": r["row_id"], "parsed": r["gold"]} for r in self.controls]
        with self.assertRaises(ValueError):
            self.run_report(rows, control_rows=dup, control_answers=two_col)
        self.run_report(rows, control_rows=self.controls, control_answers=two_col)

    def test_input_errors(self):
        good = _scores(self.pairs, score=lambda r: 0.5, parsed=lambda r: r["gold"])
        bad_cases = {
            "unknown row": good + [{**good[0], "row_id": "nope"}],
            "duplicate": good + [dict(good[0])],
            "side mismatch": [{**good[0], "side": "C" if good[0]["side"] == "B" else "B"}] + good[1:],
            "two models": [{**good[0], "model_id": "other"}] + good[1:],
            "bad label": [{**good[0], "parsed": "maybe"}] + good[1:],
            "missing side": [{k: v for k, v in good[0].items() if k != "side"}] + good[1:],
            "missing parsed": [{k: v for k, v in good[0].items() if k != "parsed"}] + good[1:],
            "non-finite score": [{**good[0], "score": "inf"}] + good[1:],
        }
        for name, rows in bad_cases.items():
            with self.assertRaises(ValueError, msg=name):
                self.run_report(rows)


if __name__ == "__main__":
    unittest.main()
