"""Competence condition for the 240-pair corpus (smol_stat_v01), applied to
reports written by the UNCHANGED analyzer (analyze_crossmodel_stat.py).

Decided by the owner on 2026-11-14:
- OFFICIAL, binding: B accuracy >= 0.50 overall AND separately on gold YES and
  gold NO cases (same rule as for the 800 original pairs). Below it the model
  is NOT EVALUABLE, whatever W is.
- THEORETICAL sensitivity only, never a verdict: chance level 1/3, the
  expected accuracy of a uniform random choice among the three allowed answers
  (YES, NO, UNKNOWN), required strictly overall and on each gold label. It
  shows what would follow from the lowest threshold that still excludes
  random or constant answering; it does not replace the official rule.
W, AUROC and all statistics are read from the report, never recomputed here.
"""
from __future__ import annotations

import argparse
import json
from math import comb
from pathlib import Path

OFFICIAL_THRESHOLD = 0.50
THEORETICAL_CHANCE = 1.0 / 3.0


def binomial_upper_tail(k, n, p):
    """P(X >= k) for X ~ Binomial(n, p), exact integer arithmetic."""
    from fractions import Fraction
    q = Fraction(p).limit_denominator(10**6)
    return float(sum(comb(n, i) * q**i * (1 - q)**(n - i) for i in range(k, n + 1)))


def gate(report):
    behavior = report["behavior"]
    gold = report["subgroups"]["B_gold"]
    parts = {
        "overall": (behavior["B_accuracy"], report["pairs"]),
        "gold_YES": (gold["YES"]["B_accuracy"], gold["YES"]["pairs"]),
        "gold_NO": (gold["NO"]["B_accuracy"], gold["NO"]["pairs"]),
    }
    official_failed = [k for k, (acc, _) in parts.items() if not acc >= OFFICIAL_THRESHOLD]
    theoretical_failed = [k for k, (acc, _) in parts.items() if not acc > THEORETICAL_CHANCE]
    chance_p = {k: binomial_upper_tail(round(acc * n), n, THEORETICAL_CHANCE)
                for k, (acc, n) in parts.items()}
    return {
        "model": report["model"],
        "B_accuracy": {k: acc for k, (acc, _) in parts.items()},
        "official_threshold": OFFICIAL_THRESHOLD,
        "official_verdict": "EVALUABLE (EXPLORATORY)" if not official_failed else "NOT EVALUABLE",
        "official_failed_parts": official_failed,
        "theoretical_threshold": "> 1/3 (chance, three answers)",
        "theoretical_only_would_be_evaluable": not theoretical_failed,
        "theoretical_failed_parts": theoretical_failed,
        "one_sided_binomial_p_vs_chance": chance_p,
        "W": report["primary"]["W"],
        "W_CI95": report["primary"]["ci95"],
        "AUROC": report["auroc"]["value"],
        "note": "Official verdict is the 0.50 rule. The 1/3 column is a theoretical sensitivity analysis, not a result.",
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument("reports", nargs="+")
    p.add_argument("--output")
    args = p.parse_args()
    rows = [gate(json.loads(Path(r).read_text(encoding="utf-8"))) for r in args.reports]
    text = json.dumps(rows, indent=2)
    if args.output:
        Path(args.output).write_text(text + "\n", encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
