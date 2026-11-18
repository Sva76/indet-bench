# Copyright (c) 2026 Simona Vargiu. IndetBench.
# Licensed under the PolyForm Noncommercial License 1.0.0. See LICENSE and NOTICE.
"""IndetBench v2 pair generator. DRAFT: not frozen, not preregistered.

Design and rules: docs/V2_GENERATOR_SPEC.md. Summary:

* Every pair is a B/C minimal pair: the two prompts differ in exactly one word,
  the truth value ("true"/"false") of one stated fact. B's answer is determined
  (gold YES or NO); C's is not (gold UNKNOWN).
* Gold labels come from enumerating every value of the uncertain facts, never
  from a person or a model.
* Difficulty is set by knobs: rule variables, chain depth, uncertain facts and
  distractor facts (LEVELS). Variety comes from operators, literal polarity,
  domains and paraphrases of the uncertainty marker.
* Literal polarity is randomised inside rules, so the surface word "true" is
  not tied to the logical value a rule needs (the v1 per-cell shortcut).
* An optional D control per story states every rule fact and makes only
  distractors uncertain: its answer is determined, so an UNKNOWN there is a
  false abstention.

Standard library only. Output is JSON Lines that `indetbench.hf_runner` reads
(sides B and C); D controls go to a separate file.
"""
from __future__ import annotations

import argparse
import itertools
import json
import math
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
import random
import re

GENERATOR_VERSION = "0.1.0-draft"

INSTRUCTION = ("Read the short rules and the facts below. Answer with a single word "
               "on the first line: YES, NO or UNKNOWN.")

# Invented, generic vocabulary written for this project. Entities and
# intermediate-condition subjects are disjoint, so a condition is never stated as a fact.
ENTITIES = (
    "anvil", "archive", "balcony", "barrel", "battery", "beacon", "bicycle", "boiler",
    "cabinet", "canoe", "caravan", "carousel", "cellar", "chimney", "compass", "conveyor",
    "corridor", "courtyard", "crane", "depot", "drum", "easel", "elevator", "ferry",
    "fountain", "furnace", "gazebo", "generator", "glider", "greenhouse", "hammock", "harbor",
    "kayak", "kettle", "kiln", "lantern", "ledger", "lobby", "loom", "mill", "monitor",
    "orchard", "pantry", "pavilion", "pier", "printer", "pump", "quarry", "raft", "router",
    "saddle", "satchel", "scaffold", "scanner", "scooter", "sled", "statue", "sundial",
    "telescope", "terrace", "toaster", "tractor", "trailer", "tripod", "trolley", "turbine",
    "vault", "wagon", "workshop", "windmill",
)
PREDICATES = (
    "approved", "calibrated", "certified", "cleaned", "inspected", "insured", "labeled",
    "locked", "measured", "painted", "photographed", "refueled", "registered", "repaired",
    "reserved", "serviced", "signed off", "stamped", "tagged", "tested", "unlocked",
    "upgraded", "weighed",
)
CONDITIONS = (
    ("permit", "valid"), ("audit", "complete"), ("clearance", "granted"),
    ("checklist", "satisfied"), ("quota", "available"), ("license", "active"),
    ("review", "passed"), ("budget", "confirmed"), ("schedule", "open"),
    ("contract", "binding"), ("dossier", "accepted"), ("waiver", "on file"),
)
# Domain: (positive outcome, negative outcome, closing sentence, question). A rule
# defines either outcome (outcome polarity); the question always asks the positive one,
# so the same operator can give a YES or a NO answer.
DOMAINS = {
    "approval": ("approval is given", "approval is withheld",
                 "Approval is either given or withheld.", "Is approval given?"),
    "access": ("the gate opens", "the gate stays closed",
               "The gate either opens or stays closed.", "Does the gate open?"),
    "shipping": ("the order ships today", "the order is held back today",
                 "The order either ships today or is held back today.",
                 "Does the order ship today?"),
    "payment": ("the payment is released", "the payment is withheld",
                "The payment is either released or withheld.", "Is the payment released?"),
    "operation": ("the line may start", "the line must stay idle",
                  "The line either may start or must stay idle.", "May the line start?"),
}
# Paraphrases of the uncertainty statement. Marker 0 is the v1 wording.
MARKERS = (
    "It may be true or false that {p}.",
    "It is not known whether {p}.",
    "The records do not say whether {p}.",
    "Nobody has checked whether {p}.",
)
KNOWN = "It is {v} that {p}."

OPS_ANY = ("AND", "OR", "EXACTLY_ONE", "NOT_ALL")
OPS_BINARY_ONLY = ("BOTH_OR_NEITHER",)

LEVELS = {
    1: {"n_vars": 2, "depth": 1, "n_uncertain": 1, "n_distractors": 1},
    2: {"n_vars": 3, "depth": 1, "n_uncertain": 1, "n_distractors": 2},
    3: {"n_vars": 3, "depth": 2, "n_uncertain": 1, "n_distractors": 3},
    4: {"n_vars": 4, "depth": 2, "n_uncertain": 2, "n_distractors": 4},
    5: {"n_vars": 5, "depth": 3, "n_uncertain": 2, "n_distractors": 6},
}


@dataclass(frozen=True)
class Var:
    entity: str
    predicate: str

    def clause(self, positive: bool = True) -> str:
        return f"the {self.entity} is {'' if positive else 'not '}{self.predicate}"


@dataclass(frozen=True)
class Condition:
    """op over items; an item is ("lit", var_index, positive) or ("ref", condition_index)."""
    op: str
    items: tuple


def apply_op(op: str, values: list[bool]) -> bool:
    if op == "AND":
        return all(values)
    if op == "OR":
        return any(values)
    if op == "EXACTLY_ONE":
        return sum(values) == 1
    if op == "NOT_ALL":
        return not all(values)
    if op == "BOTH_OR_NEITHER":
        if len(values) != 2:
            raise ValueError("BOTH_OR_NEITHER is binary")
        return values[0] == values[1]
    raise ValueError(f"Unknown operator {op}")


def evaluate(conditions: tuple[Condition, ...], assignment: dict[int, bool]) -> bool:
    """Value of the last (root) condition under a full assignment of rule variables."""
    values: list[bool] = []
    for condition in conditions:
        items = []
        for item in condition.items:
            if item[0] == "lit":
                items.append(assignment[item[1]] == item[2])
            else:
                items.append(values[item[1]])
        values.append(apply_op(condition.op, items))
    return values[-1]


def gold_label(conditions, known: dict[int, bool], uncertain: tuple[int, ...],
               negative: bool = False) -> str:
    """YES/NO if every value of the uncertain variables gives the same answer to the
    (positive) question, else UNKNOWN. negative=True: the rules define the negative outcome."""
    outcomes = set()
    for values in itertools.product((False, True), repeat=len(uncertain)):
        assignment = dict(known)
        assignment.update(zip(uncertain, values))
        outcomes.add(evaluate(conditions, assignment) != negative)
    if outcomes == {True}:
        return "YES"
    if outcomes == {False}:
        return "NO"
    return "UNKNOWN"


def _render_items(op: str, parts: list[str]) -> str:
    if op == "AND":
        return f"both {parts[0]} and {parts[1]}" if len(parts) == 2 else \
            "all of these hold: " + "; ".join(parts)
    if op == "OR":
        return "at least one of these holds: " + "; ".join(parts)
    if op == "EXACTLY_ONE":
        return "exactly one of these holds: " + "; ".join(parts)
    if op == "NOT_ALL":
        return "not all of these hold: " + "; ".join(parts)
    if op == "BOTH_OR_NEITHER":
        return "either both or neither of these hold: " + "; ".join(parts)
    raise ValueError(op)


def render_rules(conditions, variables: list[Var], names: list[tuple[str, str]],
                 outcome: str, closing: str) -> str:
    lines = []
    for index, condition in enumerate(conditions):
        parts = []
        for item in condition.items:
            if item[0] == "lit":
                parts.append(variables[item[1]].clause(item[2]))
            else:
                subject, state = names[item[1]]
                parts.append(f"the {subject} is {state}")
        body = _render_items(condition.op, parts)
        head = outcome if index == len(conditions) - 1 else "the {} is {}".format(*names[index])
        lines.append(f"Rule {index + 1}: {head[0].upper()}{head[1:]} if and only if {body}.")
    lines.append(closing)
    lines.append("No other rule applies.")
    return "\n".join(lines)


def _split_literals(n_vars: int, depth: int, rng: random.Random) -> list[int]:
    if n_vars < depth + 1:
        raise ValueError("n_vars must be at least depth + 1")
    counts = [2] + [1] * (depth - 1)
    for _ in range(n_vars - sum(counts)):
        counts[rng.randrange(depth)] += 1
    return counts


def random_conditions(n_vars: int, depth: int, rng: random.Random) -> tuple[Condition, ...]:
    counts = _split_literals(n_vars, depth, rng)
    order = list(range(n_vars))
    rng.shuffle(order)
    conditions, start = [], 0
    for level, count in enumerate(counts):
        items = [("lit", var, rng.random() < 0.5) for var in order[start:start + count]]
        start += count
        if level > 0:
            items.append(("ref", level - 1))
        rng.shuffle(items)
        ops = OPS_ANY + (OPS_BINARY_ONLY if len(items) == 2 else ())
        conditions.append(Condition(rng.choice(ops), tuple(items)))
    return tuple(conditions)


def _facts(variables, values: dict[int, bool | None], marker: str, order: list[int]) -> str:
    lines = []
    for index in order:
        value = values[index]
        clause = variables[index].clause()
        lines.append(marker.format(p=clause) if value is None else
                     KNOWN.format(v="true" if value else "false", p=clause))
    return "\n".join(lines)


def _prompt(rules: str, facts: str, question: str) -> str:
    return f"{INSTRUCTION}\n\nRules:\n{rules}\nFacts:\n{facts}\n\nQuestion: {question}"


def make_story(story_id: str, *, level: int, domain: str, marker: int, target: str,
               rng: random.Random, pairs_per_story: int = 2, max_tries: int = 500):
    """One story: a rule set, up to pairs_per_story B/C pairs and one D control.

    The B gold target (YES or NO) is fixed per story by the caller; the story is
    resampled until at least one pair with that target exists, and up to
    pairs_per_story distinct pairs are kept (level 1 rules admit only one).
    Returns (pair_rows, control_rows).
    """
    knobs = LEVELS[level]
    n_vars, depth = knobs["n_vars"], knobs["depth"]
    n_unc, n_dis = knobs["n_uncertain"], knobs["n_distractors"]
    positive, negative_outcome, closing, question = DOMAINS[domain]
    for _ in range(max_tries):
        entities = rng.sample(ENTITIES, n_vars + n_dis)
        variables = [Var(entity, rng.choice(PREDICATES)) for entity in entities]
        conditions = random_conditions(n_vars, depth, rng)
        names = rng.sample(CONDITIONS, depth)
        uncertain = tuple(sorted(rng.sample(range(n_vars), n_unc)))
        negative = rng.random() < 0.5
        known_vars = [v for v in range(n_vars) if v not in uncertain]
        candidates = defaultdict(list)
        for values in itertools.product((False, True), repeat=len(known_vars)):
            base = dict(zip(known_vars, values))
            gold_b = gold_label(conditions, base, uncertain, negative)
            if gold_b == "UNKNOWN":
                continue
            for flip in known_vars:
                flipped = dict(base)
                flipped[flip] = not flipped[flip]
                if gold_label(conditions, flipped, uncertain, negative) == "UNKNOWN":
                    candidates[gold_b].append((base, flip))
        if candidates.get(target):
            break
    else:
        raise RuntimeError(f"No reachable B/C pair for {story_id} after {max_tries} tries")

    distractors = list(range(n_vars, n_vars + n_dis))
    dis_values = {d: rng.random() < 0.5 for d in distractors}
    order = list(range(n_vars + n_dis))
    rng.shuffle(order)
    rules = render_rules(conditions, variables, names,
                         negative_outcome if negative else positive, closing)
    marker_text = MARKERS[marker]
    meta = {
        "level": level, "domain": domain, "marker": marker, **knobs,
        "ops": [c.op for c in conditions], "root_op": conditions[-1].op,
        "outcome_polarity": "negative" if negative else "positive",
        "generator": "indetbench.gen_v2", "generator_version": GENERATOR_VERSION,
    }
    pair_rows = []
    chosen = rng.sample(candidates[target], min(pairs_per_story, len(candidates[target])))
    for number, (base, flip) in enumerate(chosen):
        pair_id = f"{story_id}|p{number}"
        for side, assignment in (("B", base), ("C", {**base, flip: not base[flip]})):
            values = {**{u: None for u in uncertain}, **assignment, **dis_values}
            prompt = _prompt(rules, _facts(variables, values, marker_text, order), question)
            pair_rows.append({
                "row_id": f"{pair_id}|{side}", "pair_id": pair_id, "block_id": story_id,
                "side": side, "gold": gold_label(conditions, assignment, uncertain, negative),
                "prompt": prompt, "flipped_fact": variables[flip].clause(),
                "c_flipped_word": "false" if base[flip] else "true", **meta,
            })

    # D control: every rule fact stated, the same number of distractors made uncertain.
    full = {**candidates[target][0][0], **{u: rng.random() < 0.5 for u in uncertain}}
    shaded = tuple(rng.sample(distractors, min(n_unc, len(distractors))))
    values = {**full, **dis_values, **{d: None for d in shaded}}
    control = {
        "row_id": f"{story_id}|D", "pair_id": f"{story_id}|D", "block_id": story_id, "side": "D",
        "gold": "YES" if evaluate(conditions, full) != negative else "NO",
        "prompt": _prompt(rules, _facts(variables, values, marker_text, order), question), **meta,
    }
    return pair_rows, [control]


def generate(*, seed: int, stories_per_cell: int, levels=tuple(LEVELS), domains=tuple(DOMAINS),
             pairs_per_story: int = 2):
    """Deterministic for a given seed and arguments. A cell is (level, domain)."""
    rng = random.Random(seed)
    pairs, controls = [], []
    for level in levels:
        for domain in domains:
            for number in range(stories_per_cell):
                story_id = f"v2-L{level}-{domain}-{number:04d}"
                p, c = make_story(story_id, level=level, domain=domain,
                                  marker=number % len(MARKERS),
                                  target=("YES", "NO")[(number // len(MARKERS)) % 2],
                                  rng=rng, pairs_per_story=pairs_per_story)
                pairs.extend(p)
                controls.extend(c)
    return pairs, controls


# ---------------------------------------------------------------------------
# Shortcut audit (spec section 5): run on the generated text, before any model.
# ---------------------------------------------------------------------------

def _pairs_by_id(rows):
    table = defaultdict(dict)
    for row in rows:
        if row["side"] in ("B", "C"):
            table[row["pair_id"]][row["side"]] = row
    return {k: v for k, v in table.items() if set(v) == {"B", "C"}}


def w_by_story(pairs: dict, score) -> float:
    """W as in the v1 protocol: C>B = 1, tie = 0.5, story-averaged."""
    stories = defaultdict(list)
    for pair in pairs.values():
        b, c = score(pair["B"]), score(pair["C"])
        stories[pair["B"]["block_id"]].append(1.0 if c > b else 0.5 if c == b else 0.0)
    return sum(sum(v) / len(v) for v in stories.values()) / len(stories)


def _tokens(text: str) -> list[str]:
    words = re.findall(r"[a-z]+", text.lower())
    return words + [f"{a}_{b}" for a, b in zip(words, words[1:])]


def bow_heldout_w(rows, holdout_key: str = "domain") -> dict:
    """Multinomial naive Bayes on unigrams+bigrams, trained on all values of
    holdout_key but one and tested on the held-out one; W of log P(C)/P(B)."""
    pairs = _pairs_by_id(rows)
    groups = sorted({p["B"][holdout_key] for p in pairs.values()})
    result = {}
    for held in groups:
        counts = {"B": Counter(), "C": Counter()}
        for pair in pairs.values():
            if pair["B"][holdout_key] != held:
                for side in ("B", "C"):
                    counts[side].update(_tokens(pair[side]["prompt"]))
        vocab = set(counts["B"]) | set(counts["C"])
        totals = {s: sum(counts[s].values()) + len(vocab) for s in counts}

        def score(row):
            return sum(math.log((counts["C"][t] + 1) / totals["C"])
                       - math.log((counts["B"][t] + 1) / totals["B"])
                       for t in _tokens(row["prompt"]) if t in vocab)

        test = {k: p for k, p in pairs.items() if p["B"][holdout_key] == held}
        result[str(held)] = round(w_by_story(test, score), 4)
    return result


def audit(rows) -> dict:
    """Per-cell shortcut and balance statistics. Ideal: heuristic W near 0.5,
    B gold near 50% YES in every cell."""
    pairs = _pairs_by_id(rows)
    true_count = lambda row: row["prompt"].count("It is true")
    report = {"n_pairs": len(pairs), "n_stories": len({p["B"]["block_id"] for p in pairs.values()}),
              "minimal_pair_violations": 0, "cells": {}}
    by_cell = defaultdict(dict)
    for key, pair in pairs.items():
        b, c = pair["B"]["prompt"].split(), pair["C"]["prompt"].split()
        if len(b) != len(c) or sum(x != y for x, y in zip(b, c)) != 1:
            report["minimal_pair_violations"] += 1
        if pair["B"]["gold"] not in ("YES", "NO") or pair["C"]["gold"] != "UNKNOWN":
            report["minimal_pair_violations"] += 1
        by_cell[(pair["B"]["level"], pair["B"]["root_op"])][key] = pair
    for (level, root_op), cell in sorted(by_cell.items()):
        golds = Counter(p["B"]["gold"] for p in cell.values())
        report["cells"][f"L{level}|{root_op}"] = {
            "n_pairs": len(cell),
            "W_true_count": round(w_by_story(cell, true_count), 4),
            "B_share_YES": round(golds["YES"] / len(cell), 4),
        }
    # Rule-level association between (root operator, outcome polarity) and B's answer.
    # B and C share their rules, so this cannot move W; it matters for accuracy and
    # abstention measures and is reported, not hidden (spec section 5).
    by_rule = defaultdict(Counter)
    for pair in pairs.values():
        by_rule[f"L{pair['B']['level']}|{pair['B']['root_op']}|{pair['B']['outcome_polarity']}"][
            pair["B"]["gold"]] += 1
    report["B_share_YES_by_root_op_and_polarity"] = {
        key: round(c["YES"] / sum(c.values()), 4) for key, c in sorted(by_rule.items())}
    report["W_true_count_overall"] = round(w_by_story(pairs, true_count), 4)
    report["B_share_YES_overall"] = round(
        sum(p["B"]["gold"] == "YES" for p in pairs.values()) / len(pairs), 4)
    report["W_bow_heldout_domain"] = bow_heldout_w(rows, "domain")
    return report


def _write_jsonl(path, rows):
    with Path(path).open("w", encoding="utf-8") as file:
        for row in rows:
            file.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def main(argv=None):
    parser = argparse.ArgumentParser(description="IndetBench v2 generator (DRAFT, not frozen)")
    sub = parser.add_subparsers(dest="command", required=True)
    gen = sub.add_parser("generate", help="write B/C pairs and D controls as JSON Lines")
    gen.add_argument("--seed", type=int, required=True)
    gen.add_argument("--stories-per-cell", type=int, default=40)
    gen.add_argument("--pairs-per-story", type=int, default=2)
    gen.add_argument("--output", required=True, help="B/C pairs (hf_runner input)")
    gen.add_argument("--controls", help="optional file for D controls")
    aud = sub.add_parser("audit", help="shortcut audit of a generated pair file")
    aud.add_argument("--input", required=True)
    args = parser.parse_args(argv)
    if args.command == "generate":
        pairs, controls = generate(seed=args.seed, stories_per_cell=args.stories_per_cell,
                                   pairs_per_story=args.pairs_per_story)
        _write_jsonl(args.output, pairs)
        if args.controls:
            _write_jsonl(args.controls, controls)
    else:
        with Path(args.input).open(encoding="utf-8") as file:
            rows = [json.loads(line) for line in file if line.strip()]
        print(json.dumps(audit(rows), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
