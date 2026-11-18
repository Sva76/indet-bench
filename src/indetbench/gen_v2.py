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

Standard library only (plus indetbench.metrics for W intervals). Run as
`python -m indetbench.gen_v2` or `indet-bench-v2`. Output is JSON Lines that `indetbench.hf_runner` reads
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
import statistics

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


def _locate(conditions) -> dict[int, tuple[int, bool]]:
    """Rule index and literal sign of every rule variable (each appears exactly once)."""
    where = {}
    for index, condition in enumerate(conditions):
        for item in condition.items:
            if item[0] == "lit":
                where[item[1]] = (index, item[2])
    return where


def shallow_features(conditions, values: dict[int, bool | None]) -> dict:
    """Counts a shallow reader can take from the text without chaining rules:
    for each rule literal, is it satisfied, unsatisfied or uncertain given the facts."""
    out = {"root_sat": 0, "root_unsat": 0, "root_unc": 0, "root_refs": 0,
           "all_sat": 0, "all_unsat": 0, "all_unc": 0, "rules": []}
    last = len(conditions) - 1
    for index, condition in enumerate(conditions):
        rule = {"op": condition.op, "sat": 0, "unsat": 0, "unc": 0, "refs": 0}
        for item in condition.items:
            if item[0] == "ref":
                rule["refs"] += 1
                if index == last:
                    out["root_refs"] += 1
                continue
            value = values[item[1]]
            kind = "unc" if value is None else "sat" if value == item[2] else "unsat"
            rule[kind] += 1
            out[f"all_{kind}"] += 1
            if index == last:
                out[f"root_{kind}"] += 1
        out["rules"].append(rule)
    return out


def make_story(story_id: str, *, level: int, domain: str, marker: int, target: str,
               rng: random.Random, pairs_per_story: int = 2, sat_target: bool | None = None,
               flip_location: str | None = None, max_tries: int = 2000):
    """One story: a rule set, up to pairs_per_story B/C pairs and one D control.

    The B gold target (YES or NO) is fixed per story by the caller, and so is
    sat_target: whether the flipped literal is satisfied in C (None = no
    constraint). The story is resampled, as a whole and with unchanged rule
    templates, until at least one valid pair meets both targets; up to
    pairs_per_story distinct such pairs are kept (level 1 rules admit only one).
    Within one story both kinds are almost never available, because the operator
    of the rule that holds the flipped literal fixes the kind (spec section 5.3);
    sat_both_available records it. flip_location "root" or "intermediate"
    restricts the rule that holds the flipped literal (spec section 5.4);
    "intermediate" needs a chain (depth >= 2).
    Returns (pair_rows, control_rows).
    """
    knobs = LEVELS[level]
    n_vars, depth = knobs["n_vars"], knobs["depth"]
    n_unc, n_dis = knobs["n_uncertain"], knobs["n_distractors"]
    positive, negative_outcome, closing, question = DOMAINS[domain]
    if flip_location not in (None, "root", "intermediate"):
        raise ValueError("flip_location must be None, 'root' or 'intermediate'")
    if flip_location == "intermediate" and depth < 2:
        raise ValueError(f"Level {level} has no intermediate rule")

    def location_ok(candidate, where, last):
        flip = candidate[1]
        return flip_location is None or (where[flip][0] == last) == (flip_location == "root")

    def admissible(candidate, where, last):
        base, flip = candidate
        if sat_target is not None and ((not base[flip]) == where[flip][1]) != sat_target:
            return False
        return location_ok(candidate, where, last)

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
        where = _locate(conditions)
        if any(admissible(c, where, depth - 1) for c in candidates.get(target, [])):
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
        "flip_location_constraint": flip_location or "any",
        "generator": "indetbench.gen_v2", "generator_version": GENERATOR_VERSION,
    }

    def c_satisfied(candidate):
        base, flip = candidate
        return (not base[flip]) == where[flip][1]

    # Feasibility of within-story balancing, over the candidates this run may draw
    # from (B target and location constraint), before the satisfaction target.
    both_available = len({c_satisfied(c) for c in candidates[target]
                          if location_ok(c, where, depth - 1)}) == 2
    pool = [c for c in candidates[target] if admissible(c, where, depth - 1)]
    chosen = rng.sample(pool, min(pairs_per_story, len(pool)))

    pair_rows = []
    for number, (base, flip) in enumerate(chosen):
        pair_id = f"{story_id}|p{number}"
        rule_index, sign = where[flip]
        info = {
            "flipped_fact": variables[flip].clause(),
            "c_flipped_word": "false" if base[flip] else "true",
            "flipped_rule": rule_index,
            "flipped_rule_op": conditions[rule_index].op,
            "flipped_location": "root" if rule_index == len(conditions) - 1 else "intermediate",
            "flipped_sign": "positive" if sign else "negative",
            "c_flipped_satisfied": c_satisfied((base, flip)),
            "sat_target": sat_target, "sat_both_available": both_available,
        }
        for side, assignment in (("B", base), ("C", {**base, flip: not base[flip]})):
            values = {**{u: None for u in uncertain}, **assignment, **dis_values}
            prompt = _prompt(rules, _facts(variables, values, marker_text, order), question)
            pair_rows.append({
                "row_id": f"{pair_id}|{side}", "pair_id": pair_id, "block_id": story_id,
                "side": side, "gold": gold_label(conditions, assignment, uncertain, negative),
                "prompt": prompt, "shallow": shallow_features(conditions, values),
                **info, **meta,
            })

    # D control: every rule fact stated, the same number of distractors made uncertain.
    full = {**candidates[target][0][0], **{u: rng.random() < 0.5 for u in uncertain}}
    shaded = tuple(rng.sample(distractors, min(n_unc, len(distractors))))
    values = {**full, **dis_values, **{d: None for d in shaded}}
    control = {
        "row_id": f"{story_id}|D", "pair_id": f"{story_id}|D", "block_id": story_id, "side": "D",
        "gold": "YES" if evaluate(conditions, full) != negative else "NO",
        "prompt": _prompt(rules, _facts(variables, values, marker_text, order), question),
        "shallow": shallow_features(conditions, values), **meta,
    }
    return pair_rows, [control]


def dataset_tag(*, seed: int, stories_per_cell: int, pairs_per_story: int,
                flip_location: str | None, levels=tuple(LEVELS), domains=tuple(DOMAINS)) -> str:
    """Prefix of every story id. It binds ids to the generator version and to every
    argument that changes the prompts, including the order of levels and domains
    (one random stream runs across cells), so a score file made on another
    dataset cannot match."""
    import hashlib
    cells = json.dumps({"levels": list(levels), "domains": list(domains)}, sort_keys=True)
    digest = hashlib.sha256(cells.encode("utf-8")).hexdigest()[:8]
    return (f"v2g{GENERATOR_VERSION}-s{seed}-{flip_location or 'any'}"
            f"-c{stories_per_cell}-p{pairs_per_story}-{digest}")


def generate(*, seed: int, stories_per_cell: int, levels=tuple(LEVELS), domains=tuple(DOMAINS),
             pairs_per_story: int = 2, flip_location: str | None = None):
    """Deterministic for a given seed and arguments. A cell is (level, domain).
    Story number n = 8q + r sets marker r % 4, B gold target r // 4 and the
    satisfaction target (marker + gold + q) % 2, so every block of 8 stories has
    each marker twice, each gold target 4 times and each satisfaction target 4 times.
    flip_location applies only to levels with a chain (depth >= 2); depth-1 levels
    have no intermediate rule and are generated without the constraint."""
    rng = random.Random(seed)
    tag = dataset_tag(seed=seed, stories_per_cell=stories_per_cell,
                      pairs_per_story=pairs_per_story, flip_location=flip_location,
                      levels=levels, domains=domains)
    pairs, controls = [], []
    for level in levels:
        for domain in domains:
            for number in range(stories_per_cell):
                story_id = f"{tag}-L{level}-{domain}-{number:04d}"
                marker, gold = number % 4, (number % 8) // 4
                p, c = make_story(story_id, level=level, domain=domain, marker=marker,
                                  target=("YES", "NO")[gold],
                                  sat_target=(marker + gold + number // 8) % 2 == 0,
                                  flip_location=flip_location if LEVELS[level]["depth"] >= 2 else None,
                                  rng=rng, pairs_per_story=pairs_per_story)
                pairs.extend(p)
                controls.extend(c)
    return pairs, controls


# ---------------------------------------------------------------------------
# Integrity checks
# ---------------------------------------------------------------------------

REQUIRED = ("row_id", "pair_id", "block_id", "side")
# Story and pair metadata that B and C must share (spec section 5.1).
PAIR_SHARED = ("level", "domain", "marker", "ops", "root_op", "outcome_polarity", "depth",
               "flip_location_constraint", "flipped_fact", "flipped_rule", "flipped_rule_op",
               "flipped_location", "flipped_sign", "c_flipped_word", "c_flipped_satisfied")


def pairs_by_id(rows, *, sides=("B", "C")) -> dict[str, dict[str, dict]]:
    """Strict pairing. Raises ValueError on a missing field, a side outside `sides`,
    a duplicate row_id, a duplicate side within a pair, a pair split across stories
    or an incomplete pair. Nothing is dropped silently."""
    table: dict[str, dict[str, dict]] = {}
    seen, blocks = set(), {}
    for number, row in enumerate(rows, 1):
        if not isinstance(row, dict):
            raise ValueError(f"Row {number}: not a JSON object")
        for key in REQUIRED:
            if not isinstance(row.get(key), str) or not row[key].strip():
                raise ValueError(f"Row {number}: missing or blank {key}")
        if row["side"] not in sides:
            raise ValueError(f"Row {number}: side {row['side']!r} not allowed here")
        if row["row_id"] in seen:
            raise ValueError(f"Row {number}: duplicate row_id {row['row_id']}")
        seen.add(row["row_id"])
        if blocks.setdefault(row["pair_id"], row["block_id"]) != row["block_id"]:
            raise ValueError(f"Row {number}: pair {row['pair_id']} spans two stories")
        pair = table.setdefault(row["pair_id"], {})
        if row["side"] in pair:
            raise ValueError(f"Row {number}: duplicate side {row['side']} in {row['pair_id']}")
        pair[row["side"]] = row
    incomplete = sorted(k for k, v in table.items() if set(v) != {"B", "C"}) if "B" in sides else []
    if incomplete:
        raise ValueError(f"{len(incomplete)} incomplete pair(s), first: {incomplete[0]}")
    if "B" in sides:
        for pid, pair in table.items():
            for key in PAIR_SHARED:
                if key in pair["B"] or key in pair["C"]:
                    if pair["B"].get(key) != pair["C"].get(key):
                        raise ValueError(f"Pair {pid}: B and C disagree on {key}")
    if not table:
        raise ValueError("No pairs")
    return table


# ---------------------------------------------------------------------------
# Shortcut audit (spec section 5): run on the generated text, before any model.
# ---------------------------------------------------------------------------

_FACT = re.compile(r"It is (true|false) that (.+)\.")


def minimal_pair_ok(b_prompt: str, c_prompt: str) -> bool:
    """True if the prompts differ in exactly one word and that word is the truth
    value of the same stated fact, in the Facts block."""
    b_words, c_words = b_prompt.split(), c_prompt.split()
    if len(b_words) != len(c_words) or sum(x != y for x, y in zip(b_words, c_words)) != 1:
        return False
    b_lines, c_lines = b_prompt.splitlines(), c_prompt.splitlines()
    if len(b_lines) != len(c_lines) or "Facts:" not in b_lines:
        return False
    start = b_lines.index("Facts:")
    diff = [i for i, (x, y) in enumerate(zip(b_lines, c_lines)) if x != y]
    if len(diff) != 1 or diff[0] <= start:
        return False
    mb, mc = _FACT.fullmatch(b_lines[diff[0]]), _FACT.fullmatch(c_lines[diff[0]])
    return bool(mb and mc and mb.group(2) == mc.group(2) and mb.group(1) != mc.group(1))


def _story_w(pairs: dict, score) -> float:
    """W as in the v1 protocol: C>B = 1, tie = 0.5, averaged within stories."""
    stories = defaultdict(list)
    for pair in pairs.values():
        b, c = score(pair["B"]), score(pair["C"])
        stories[pair["B"]["block_id"]].append(1.0 if c > b else 0.5 if c == b else 0.0)
    return sum(sum(v) / len(v) for v in stories.values()) / len(stories)


def _w_ci(pairs: dict, scores: dict[str, float], *, n_bootstrap: int, seed: int) -> dict:
    """W with the story-bootstrap interval of indetbench.metrics (v1 implementation)."""
    from .metrics import PairScore, w_score

    rows = [PairScore(p[s]["pair_id"], p[s]["block_id"], s, scores[p[s]["row_id"]])
            for p in pairs.values() for s in ("B", "C")]
    est = w_score(rows, n_bootstrap=n_bootstrap, seed=seed)
    return {"W": round(est.value, 4),
            "ci95": None if est.ci_lower is None else [round(est.ci_lower, 4), round(est.ci_upper, 4)],
            "n_pairs": est.n_pairs, "n_stories": est.n_blocks}


def _tokens(text: str) -> list[str]:
    words = re.findall(r"[a-z]+", text.lower())
    return words + [f"{a}_{b}" for a, b in zip(words, words[1:])]


def _folds(pairs: dict, key, k: int, seed: int) -> dict[str, int]:
    """pair_id -> fold. key(pair) gives the grouping unit (story or structure);
    every unit is in exactly one fold, so no unit is seen in training and test."""
    units = sorted({key(p) for p in pairs.values()})
    random.Random(seed).shuffle(units)
    fold_of = {u: i % k for i, u in enumerate(units)} if k else {u: i for i, u in enumerate(units)}
    return {pid: fold_of[key(p)] for pid, p in pairs.items()}


def _crossfit(pairs: dict, fold: dict[str, int], fit, apply) -> dict[str, float]:
    """Score every row with a model fitted on the pairs of the other folds only."""
    scores = {}
    for f in sorted(set(fold.values())):
        train = [p for pid, p in pairs.items() if fold[pid] != f]
        model = fit(train)
        for pid, p in pairs.items():
            if fold[pid] == f:
                for side in ("B", "C"):
                    scores[p[side]["row_id"]] = apply(model, p[side])
    return scores


def _fit_nb(train):
    counts = {"B": Counter(), "C": Counter()}
    for pair in train:
        for side in ("B", "C"):
            counts[side].update(_tokens(pair[side]["prompt"]))
    vocab = set(counts["B"]) | set(counts["C"])
    totals = {s: sum(counts[s].values()) + len(vocab) for s in counts}
    return counts, vocab, totals


def _apply_nb(model, row):
    counts, vocab, totals = model
    return sum(math.log((counts["C"][t] + 1) / totals["C"])
               - math.log((counts["B"][t] + 1) / totals["B"])
               for t in _tokens(row["prompt"]) if t in vocab)


def _key_with_operator(row):
    f = row["shallow"]
    return (row["level"], row["outcome_polarity"], row["root_op"],
            f["root_sat"], f["root_unsat"], f["root_unc"], f["root_refs"])


def _key_without_operator(row):
    f = row["shallow"]
    return (row["level"], f["all_sat"], f["all_unsat"], f["all_unc"])


def _key_single_rule(k: int):
    """One rule read on its own: rule k (0 = Rule 1), with the root operator and
    outcome polarity; rows whose story has fewer rules get a constant key."""
    def key(row):
        rules = row["shallow"]["rules"]
        if k >= len(rules):
            return ("absent",)
        r = rules[k]
        return (row["level"], row["outcome_polarity"], row["root_op"], k, r["op"],
                r["sat"], r["unsat"], r["unc"], r["refs"])
    return key


def _lookup(keyfunc):
    def fit(train):
        table = defaultdict(lambda: [0, 0])
        for pair in train:
            for side in ("B", "C"):
                table[keyfunc(pair[side])][side == "C"] += 1
        return dict(table)

    def apply(model, row):
        n_b, n_c = model.get(keyfunc(row), (0, 0))
        return (n_c + 1) / (n_b + n_c + 2)  # unseen feature value: 0.5
    return fit, apply


def _by_level(pairs: dict, scores: dict, *, n_bootstrap: int, seed: int,
              by_root_op: bool = False) -> dict:
    out = {}
    for level in sorted({p["B"]["level"] for p in pairs.values()}):
        sub = {k: p for k, p in pairs.items() if p["B"]["level"] == level}
        out[f"L{level}"] = _w_ci(sub, scores, n_bootstrap=n_bootstrap, seed=seed)
        if by_root_op:
            for op in sorted({p["B"]["root_op"] for p in sub.values()}):
                cell = {k: p for k, p in sub.items() if p["B"]["root_op"] == op}
                out[f"L{level}|{op}"] = _w_ci(cell, scores, n_bootstrap=n_bootstrap, seed=seed)
    return out


def heldout_baselines(rows, *, k: int = 5, seed: int = 20261118, n_bootstrap: int = 1000) -> dict:
    """Spec section 5.2. Every score comes from a model that never saw the
    test story (story folds) or the test logical structure (structure folds)."""
    pairs = pairs_by_id(rows)
    story = _folds(pairs, lambda p: p["B"]["block_id"], k, seed)
    domain = _folds(pairs, lambda p: p["B"]["domain"], 0, seed)
    structure = _folds(pairs, lambda p: (p["B"]["level"], tuple(p["B"]["ops"]),
                                         p["B"]["outcome_polarity"]), k, seed)
    with_op, without_op = _lookup(_key_with_operator), _lookup(_key_without_operator)
    plans = {
        "bow_nb|story_folds": (story, _fit_nb, _apply_nb),
        "bow_nb|domain_held_out": (domain, _fit_nb, _apply_nb),
        "shallow_with_operator|story_folds": (story, *with_op),
        "shallow_without_operator|story_folds": (story, *without_op),
        "shallow_without_operator|structure_folds": (structure, *without_op),
    }
    depth = max(p["B"]["depth"] for p in pairs.values())
    for k in range(depth):
        plans[f"single_rule_{k + 1}|story_folds"] = (story, *_lookup(_key_single_rule(k)))
    out = {}
    for name, (folds, fit, apply) in plans.items():
        scores = _crossfit(pairs, folds, fit, apply)
        out[name] = _by_level(pairs, scores, n_bootstrap=n_bootstrap, seed=seed,
                              by_root_op=name.startswith("single_rule_"))
        if name == "shallow_with_operator|story_folds":
            for loc in ("root", "intermediate"):
                sub = {k: p for k, p in pairs.items() if p["B"]["flipped_location"] == loc}
                if sub:
                    out[f"{name}|flipped_in_{loc}"] = _by_level(sub, scores, n_bootstrap=n_bootstrap,
                                                                seed=seed)
    return out


def audit(rows, *, min_n: int = 10, baselines: bool = True) -> dict:
    """Per-cell shortcut and balance statistics, with cell sizes.
    Ideal: heuristic W near 0.5 and B gold near 50% YES in every cell."""
    pairs = pairs_by_id(rows)
    true_count = lambda row: row["prompt"].count("It is true")
    report = {"n_pairs": len(pairs), "n_stories": len({p["B"]["block_id"] for p in pairs.values()}),
              "minimal_pair_violations": 0, "min_n": min_n}
    for pair in pairs.values():
        if not minimal_pair_ok(pair["B"]["prompt"], pair["C"]["prompt"]):
            report["minimal_pair_violations"] += 1
        if pair["B"]["gold"] not in ("YES", "NO") or pair["C"]["gold"] != "UNKNOWN":
            report["minimal_pair_violations"] += 1

    def table(keyfunc):
        groups = defaultdict(dict)
        for pid, pair in pairs.items():
            groups[keyfunc(pair["B"])][pid] = pair
        return {key: {"n_pairs": len(cell),
                      "W_true_count": round(_story_w(cell, true_count), 4),
                      "B_share_YES": round(sum(p["B"]["gold"] == "YES" for p in cell.values())
                                           / len(cell), 4),
                      "C_share_flipped_satisfied": round(
                          sum(p["B"]["c_flipped_satisfied"] for p in cell.values()) / len(cell), 4)}
                for key, cell in sorted(groups.items())}

    report["W_true_count_overall"] = round(_story_w(pairs, true_count), 4)
    report["B_share_YES_overall"] = round(
        sum(p["B"]["gold"] == "YES" for p in pairs.values()) / len(pairs), 4)
    report["cells_level_root_op"] = table(lambda r: f"L{r['level']}|{r['root_op']}")
    report["cells_level_flipped_rule_op"] = table(lambda r: f"L{r['level']}|{r['flipped_rule_op']}")
    fine = table(lambda r: "|".join([f"L{r['level']}", r["flipped_rule_op"], r["outcome_polarity"],
                                     r["flipped_sign"], r["flipped_location"]]))
    report["subcells_fine"] = fine
    report["cells_level_flipped_location"] = table(lambda r: f"L{r['level']}|{r['flipped_location']}")
    # Share of pairs in fine subcells where the "It is true" count separates B and C
    # perfectly (W = 0 or 1), separately for subcells large enough to judge.
    summary = {}
    for level in sorted({p["B"]["level"] for p in pairs.values()}):
        cells = {k: v for k, v in fine.items() if k.startswith(f"L{level}|")}
        total = sum(v["n_pairs"] for v in cells.values())
        det_big = sum(v["n_pairs"] for v in cells.values()
                      if v["n_pairs"] >= min_n and v["W_true_count"] in (0.0, 1.0))
        small = sum(v["n_pairs"] for v in cells.values() if v["n_pairs"] < min_n)
        summary[f"L{level}"] = {"n_pairs": total, "n_subcells": len(cells),
                                "share_in_deterministic_subcells_n_ge_min": round(det_big / total, 4),
                                "share_in_subcells_n_lt_min": round(small / total, 4)}
    report["deterministic_subcells_by_level"] = summary
    feas = defaultdict(lambda: [0, 0])
    for p in pairs.values():
        cell = feas[f"L{p['B']['level']}|{p['B']['flipped_rule_op']}"]
        cell[0] += 1
        cell[1] += p["B"]["sat_both_available"]
    report["balance_feasibility_within_story"] = {
        key: {"n_pairs": n, "share_story_has_both_kinds": round(both / n, 4)}
        for key, (n, both) in sorted(feas.items())}
    report["C_share_flipped_satisfied_by_level"] = {
        f"L{level}": round(sum(p["B"]["c_flipped_satisfied"] for p in pairs.values()
                               if p["B"]["level"] == level)
                           / sum(p["B"]["level"] == level for p in pairs.values()), 4)
        for level in sorted({p["B"]["level"] for p in pairs.values()})}
    by_rule = defaultdict(Counter)
    for pair in pairs.values():
        by_rule[f"L{pair['B']['level']}|{pair['B']['root_op']}|{pair['B']['outcome_polarity']}"][
            pair["B"]["gold"]] += 1
    report["B_share_YES_by_root_op_and_polarity"] = {
        key: {"n_pairs": sum(c.values()), "share_YES": round(c["YES"] / sum(c.values()), 4)}
        for key, c in sorted(by_rule.items())}
    if baselines:
        report["heldout_baselines"] = heldout_baselines(rows)
    return report


# ---------------------------------------------------------------------------
# Report on model scores (spec section 6)
# ---------------------------------------------------------------------------

LABELS = ("YES", "NO", "UNKNOWN", "ALTRO")
PAIR_SCORE_REQUIRED = ("row_id", "pair_id", "block_id", "side", "parsed")
CONTROL_ANSWER_REQUIRED = ("row_id", "parsed")


def _read_csv(path) -> list[dict]:
    import csv
    with Path(path).open(encoding="utf-8", newline="") as file:
        return list(csv.DictReader(file))


def _finite(value, what: str, number: int) -> float:
    try:
        x = float(value)
    except (TypeError, ValueError):
        raise ValueError(f"Score row {number}: {what} is not a number") from None
    if not math.isfinite(x):
        raise ValueError(f"Score row {number}: {what} is not finite")
    return x


def _check_scores(score_rows, generated_rows, *, required):
    """Score rows must name generated rows (ids are dataset-specific, see
    dataset_tag), repeat their pair, story and side, carry every required field,
    have no duplicates, one model, labels in LABELS and finite numbers. A column
    present in some rows must be present in all. Returns row_id -> row."""
    by_id = {r["row_id"]: r for r in generated_rows}
    out, models = {}, set()
    columns = None
    for number, row in enumerate(score_rows, 1):
        missing = [k for k in required if not str(row.get(k) or "").strip()]
        if missing:
            raise ValueError(f"Score row {number}: missing {', '.join(missing)}")
        present = {k for k in ("score", "mass_total", "prompt_tokens", "model_id", "model_revision")
                   if str(row.get(k) or "").strip()}
        if columns is None:
            columns = present
        elif present != columns:
            raise ValueError(f"Score row {number}: optional columns differ from the first row")
        rid = row["row_id"]
        if rid not in by_id:
            raise ValueError(f"Score row {number}: row_id {rid!r} is not in the generated file")
        if rid in out:
            raise ValueError(f"Score row {number}: duplicate row_id {rid}")
        ref = by_id[rid]
        for key in ("pair_id", "block_id", "side"):
            if key in row and row[key] != ref[key]:
                raise ValueError(f"Score row {number}: {key} differs from the generated row")
        if row["parsed"] not in LABELS:
            raise ValueError(f"Score row {number}: parsed must be one of {LABELS}")
        for key in ("score", "mass_total"):
            if key in present:
                _finite(row[key], key, number)
        if "prompt_tokens" in present:
            try:
                tokens = int(str(row["prompt_tokens"]).strip())
            except ValueError:
                raise ValueError(f"Score row {number}: prompt_tokens is not an integer") from None
            if tokens <= 0:
                raise ValueError(f"Score row {number}: prompt_tokens must be positive")
        if "model_id" in present or "model_revision" in present:
            models.add((row.get("model_id", ""), row.get("model_revision", "")))
        out[rid] = row
    if len(models) > 1:
        raise ValueError(f"Scores mix models: {sorted(models)}")
    return out, models, columns or set()


def _share_ci(items: list[tuple[str, bool]], *, n_bootstrap: int, seed: int) -> dict:
    """Pooled share with a story-cluster bootstrap 95% interval. items: (story, success)."""
    if not items:
        return {"share": None, "ci95": None, "n": 0}
    stories = defaultdict(list)
    for story, ok in items:
        stories[story].append(ok)
    keys = sorted(stories)
    share = sum(ok for _, ok in items) / len(items)
    rng, samples = random.Random(seed), []
    for _ in range(n_bootstrap):
        pick = [keys[rng.randrange(len(keys))] for _ in keys]
        hits = sum(sum(stories[k]) for k in pick)
        samples.append(hits / sum(len(stories[k]) for k in pick))
    samples.sort()
    ci = None if not samples else [round(samples[int(0.025 * (len(samples) - 1))], 4),
                                   round(samples[int(0.975 * (len(samples) - 1))], 4)]
    return {"share": round(share, 4), "ci95": ci, "n": len(items)}


def _rules_block(prompt: str) -> str:
    return prompt.split("\nFacts:\n", 1)[0]


def report(pair_rows, score_rows, *, control_rows=None, control_answers=None,
           n_bootstrap: int = 2000, seed: int = 20261108) -> dict:
    """Per-level report of one model (spec section 6).

    Populations: answer measures (accuracy, abstention) use every scored row of
    the side concerned; W of the generated answer uses complete pairs; W of
    p(UNKNOWN), the primary measure, uses complete pairs whose B and C prompts
    have the same token count (all complete pairs as a sensitivity value).

    Statuses, in this order: NOT MEASURABLE (median label mass < 0.5); NOT
    EVALUABLE (accuracy on B < 0.5 overall, on gold YES or on gold NO);
    DESCRIPTIVE (the primary population, or complete pairs for an answer-only
    file, below 95% of generated pairs, compared on counts); ANSWERS ONLY (no
    probability scores: no verdict); DESCRIPTIVE (probability scores without
    prompt_tokens, so the length check cannot be applied); then the v1 verdict
    rule applied provisionally."""
    generated = pairs_by_id(pair_rows)
    all_rows = [r for p in generated.values() for r in (p["B"], p["C"])]
    scores, models, columns = _check_scores(score_rows, all_rows, required=PAIR_SCORE_REQUIRED)
    has_prob = "score" in columns
    has_mass = "mass_total" in columns
    has_len = "prompt_tokens" in columns
    controls, ctl_by_id = {}, {}
    if control_answers is not None:
        if control_rows is None:
            raise ValueError("control answers need the controls file")
        ctl_by_id = {r["row_id"]: r for p in pairs_by_id(control_rows, sides=("D",)).values()
                     for r in p.values()}
        rules_of = {p["B"]["block_id"]: _rules_block(p["B"]["prompt"]) for p in generated.values()}
        for r in ctl_by_id.values():
            if r["block_id"] not in rules_of:
                raise ValueError(f"D control {r['row_id']}: story not in the B/C file")
            if _rules_block(r["prompt"]) != rules_of[r["block_id"]]:
                raise ValueError(f"D control {r['row_id']}: rules differ from its story's B/C pairs")
        controls, ctl_models, _ = _check_scores(control_answers, list(ctl_by_id.values()),
                                                required=CONTROL_ANSWER_REQUIRED)
        if ctl_models and models and ctl_models != models:
            raise ValueError(f"D answers come from another model: {sorted(ctl_models)}")
    boot = {"n_bootstrap": n_bootstrap, "seed": seed}

    def parsed(row):
        return scores[row["row_id"]]["parsed"]

    def answer_block(pairs_in, b_rows, c_rows):
        out = {
            "W_generated_answer": _w_ci(pairs_in, {r["row_id"]: float(parsed(r) == "UNKNOWN")
                                                   for p in pairs_in.values()
                                                   for r in (p["B"], p["C"])}, **boot)
            if pairs_in else None,
            "abstention_C": _share_ci([(r["block_id"], parsed(r) == "UNKNOWN") for r in c_rows], **boot),
            "false_abstention_B": _share_ci([(r["block_id"], parsed(r) == "UNKNOWN") for r in b_rows], **boot),
        }
        return out

    def prob_block(primary, complete):
        if not has_prob:
            return {}
        p_unknown = {r["row_id"]: float(scores[r["row_id"]]["score"])
                     for p in complete.values() for r in (p["B"], p["C"])}
        return {"W_p_unknown": _w_ci(primary, p_unknown, **boot) if primary else None,
                "W_p_unknown_sensitivity_all_lengths": _w_ci(complete, p_unknown, **boot)
                if complete else None}

    result = {"model": sorted(models), "levels": {},
              "has_probability_scores": has_prob, "has_label_mass": has_mass,
              "length_check": "prompt_tokens" if has_len else "unavailable (no prompt_tokens column)",
              "rules": report.__doc__.split("Statuses,", 1)[1].strip()}
    for level in sorted({p["B"]["level"] for p in generated.values()}):
        cell = {k: p for k, p in generated.items() if p["B"]["level"] == level}
        b_rows = [p["B"] for p in cell.values() if p["B"]["row_id"] in scores]
        c_rows = [p["C"] for p in cell.values() if p["C"]["row_id"] in scores]
        complete = {k: p for k, p in cell.items()
                    if p["B"]["row_id"] in scores and p["C"]["row_id"] in scores}
        primary = {k: p for k, p in complete.items()
                   if not has_len or int(scores[p["B"]["row_id"]]["prompt_tokens"])
                   == int(scores[p["C"]["row_id"]]["prompt_tokens"])}
        entry = {"n_pairs_generated": len(cell), "n_pairs_complete": len(complete),
                 "n_pairs_primary": len(primary), "n_B_scored": len(b_rows), "n_C_scored": len(c_rows),
                 "coverage_complete": round(len(complete) / len(cell), 4),
                 "coverage_primary": round(len(primary) / len(cell), 4)}
        entry.update(prob_block(primary, complete))
        entry.update(answer_block(complete, b_rows, c_rows))
        entry["accuracy_B"] = _share_ci([(r["block_id"], parsed(r) == r["gold"]) for r in b_rows], **boot)
        for gold in ("YES", "NO"):
            entry[f"accuracy_B_gold_{gold}"] = _share_ci(
                [(r["block_id"], parsed(r) == gold) for r in b_rows if r["gold"] == gold], **boot)
        scored = b_rows + c_rows
        entry["share_ALTRO"] = round(sum(parsed(r) == "ALTRO" for r in scored) / len(scored), 4) \
            if scored else None
        d_rows = [r for rid, r in ctl_by_id.items() if rid in controls and r["level"] == level]
        if d_rows:
            entry["false_abstention_D"] = _share_ci(
                [(r["block_id"], controls[r["row_id"]]["parsed"] == "UNKNOWN") for r in d_rows], **boot)
            entry["accuracy_D"] = _share_ci(
                [(r["block_id"], controls[r["row_id"]]["parsed"] == r["gold"]) for r in d_rows], **boot)
        for name, field in (("by_flipped_rule_op", "flipped_rule_op"),
                            ("by_flipped_location", "flipped_location")):
            groups = sorted({p["B"][field] for p in cell.values()})
            entry[name] = {}
            for g in groups:
                sel = lambda d: {k: p for k, p in d.items() if p["B"][field] == g}
                entry[name][g] = {**prob_block(sel(primary), sel(complete)),
                                  **answer_block(sel(complete),
                                                 [r for r in b_rows if r[field] == g],
                                                 [r for r in c_rows if r[field] == g])}
        masses = [float(scores[r["row_id"]]["mass_total"]) for r in scored] if has_mass else []
        median_mass = statistics.median(masses) if masses else None
        entry["median_label_mass"] = None if median_mass is None else round(median_mass, 4)
        gate = [entry["accuracy_B"]["share"], entry["accuracy_B_gold_YES"]["share"],
                entry["accuracy_B_gold_NO"]["share"]]
        eligible = len(primary) if has_prob else len(complete)
        below_coverage = eligible < 0.95 * len(cell)  # on counts, before rounding
        w = entry.get("W_p_unknown")
        if not scored:
            entry["status"] = "NO DATA"
        elif median_mass is not None and median_mass < 0.5:
            entry["status"] = "NOT MEASURABLE"
        elif any(g is None or g < 0.5 for g in gate):
            entry["status"] = "NOT EVALUABLE"
        elif below_coverage:
            entry["status"] = "DESCRIPTIVE"
        elif not has_prob:
            entry["status"] = "ANSWERS ONLY"
        elif not has_len:
            entry["status"] = "DESCRIPTIVE"
            entry["status_reason"] = "no prompt_tokens: the length check of the primary W cannot be applied"
        elif w is None:
            entry["status"] = "NO DATA"
        elif w["W"] >= 0.60 and w["ci95"] and w["ci95"][0] > 0.5:
            entry["status"] = "CONFIRMED"
        elif w["ci95"] and w["ci95"][1] <= 0.5:
            entry["status"] = "NOT CONFIRMED"
        else:
            entry["status"] = "NOT CONCLUSIVE"
        result["levels"][f"L{level}"] = entry
    return result


def _write_jsonl(path, rows):
    with Path(path).open("w", encoding="utf-8") as file:
        for row in rows:
            file.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def _read_jsonl(path) -> list[dict]:
    with Path(path).open(encoding="utf-8") as file:
        return [json.loads(line) for line in file if line.strip()]


def main(argv=None):
    parser = argparse.ArgumentParser(description="IndetBench v2 generator (DRAFT, not frozen)")
    sub = parser.add_subparsers(dest="command", required=True)
    gen = sub.add_parser("generate", help="write B/C pairs and D controls as JSON Lines")
    gen.add_argument("--seed", type=int, required=True)
    gen.add_argument("--stories-per-cell", type=int, default=40)
    gen.add_argument("--pairs-per-story", type=int, default=2)
    gen.add_argument("--output", required=True, help="B/C pairs (hf_runner input)")
    gen.add_argument("--controls", help="optional file for D controls")
    gen.add_argument("--flip-location", choices=("any", "root", "intermediate"), default="any",
                     help="rule holding the flipped fact, for levels with a chain")
    aud = sub.add_parser("audit", help="shortcut audit of a generated pair file")
    aud.add_argument("--input", required=True)
    aud.add_argument("--min-n", type=int, default=10)
    aud.add_argument("--no-baselines", action="store_true")
    rep = sub.add_parser("report", help="per-level report of one model's scores")
    rep.add_argument("--pairs", required=True, help="generated B/C pair file")
    rep.add_argument("--scores", required=True, help="hf_runner CSV for the pair file")
    rep.add_argument("--controls", help="generated D control file")
    rep.add_argument("--control-answers", help="CSV row_id,parsed for the D controls")
    rep.add_argument("--bootstrap", type=int, default=2000)
    rep.add_argument("--seed", type=int, default=20261108)
    args = parser.parse_args(argv)
    if args.command == "generate":
        pairs, controls = generate(seed=args.seed, stories_per_cell=args.stories_per_cell,
                                   pairs_per_story=args.pairs_per_story,
                                   flip_location=None if args.flip_location == "any" else args.flip_location)
        _write_jsonl(args.output, pairs)
        if args.controls:
            _write_jsonl(args.controls, controls)
    elif args.command == "audit":
        print(json.dumps(audit(_read_jsonl(args.input), min_n=args.min_n,
                               baselines=not args.no_baselines), indent=2, sort_keys=True))
    else:
        result = report(_read_jsonl(args.pairs), _read_csv(args.scores),
                        control_rows=_read_jsonl(args.controls) if args.controls else None,
                        control_answers=_read_csv(args.control_answers) if args.control_answers else None,
                        n_bootstrap=args.bootstrap, seed=args.seed)
        print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
