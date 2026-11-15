"""95% intervals for the output baselines of the 14-15 November 2026 runs (post hoc).

Analysis added on 15 November 2026, AFTER the results were known: it is descriptive and
was not preregistered. It changes no verdict. It adds intervals to numbers that the
reports gave as point estimates only.

For each model folder in results/new_models_2026-11-14/ and results/larger_models_2026-11-15/
it reads punteggi.csv and computes, with the definitions of the original notebooks:
  - entropy   : Shannon entropy of (p_yes, p_no, p_unknown) renormalised to sum 1
  - neg_p_max : minus the largest renormalised label probability
  - unknown01 : 1 if the generated answer is UNKNOWN, else 0
  - p_unknown : the reference score (column `score`)
W of each score with a 95% story bootstrap, and the paired difference
delta_W = W(p_unknown) - W(baseline) with the stories resampled jointly
(indetbench.metrics.compare_to_reference, 2000 resamples, seed 20261108).

The bootstrap is that of indetbench.metrics (Python `random`), not the numpy one of the
notebooks, so intervals can differ from the notebook ones by a few thousandths; point
estimates are identical. No correction for multiple comparisons is applied.

Run from the repository root:  python results/baseline_intervals_2026-11-15/compute.py
"""
from __future__ import annotations

import csv
import math
import sys
from pathlib import Path

from indetbench.metrics import PairScore, compare_to_reference

ROOT = Path(__file__).resolve().parents[2]
RUNS = ("results/new_models_2026-11-14", "results/larger_models_2026-11-15")
BASELINES = ("entropy", "neg_p_max", "unknown01")
OUT = Path(__file__).resolve().parent / "baseline_intervals.csv"
N_BOOT, SEED = 2000, 20261108
# Status as in the approved reports; the Qwen3-8B control appears once per run.
STATUS = {"qwen_controllo": "positive control (Qwen3-8B)",
          "yi15_9b": "NOT EVALUABLE (technical: label mass ~0; owner decision 14 Nov 2026)"}


def baseline_scores(row: dict) -> dict:
    p = [float(row["p_yes"]), float(row["p_no"]), float(row["p_unknown"])]
    total = sum(p)
    n = [x / total for x in p]
    return {"entropy": -sum(x * math.log(max(x, 1e-300)) for x in n),
            "neg_p_max": -max(n),
            "unknown01": 1.0 if row["parsed"] == "UNKNOWN" else 0.0}


def rows_for(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def compute() -> list[dict]:
    out = []
    for run in RUNS:
        for folder in sorted((ROOT / run).glob("*-*/")):
            rows = rows_for(folder / "punteggi.csv")
            model = folder.name.rsplit("-", 1)[0]
            ref = [PairScore(r["pair_id"], r["block_id"], r["side"], float(r["score"])) for r in rows]
            extra = [baseline_scores(r) for r in rows]
            for name in BASELINES:
                method = [PairScore(r["pair_id"], r["block_id"], r["side"], e[name])
                          for r, e in zip(rows, extra)]
                # compare_to_reference(method, reference) gives W(method) - W(reference);
                # here the sign is flipped so that positive favours p(UNKNOWN).
                c = compare_to_reference(method, ref, n_bootstrap=N_BOOT, seed=SEED)
                out.append({
                    "run": run.split("/")[-1], "model": model,
                    "status": STATUS.get(model, "exploratory"), "baseline": name,
                    "n_pairs": c.method.n_pairs, "n_stories": c.method.n_blocks,
                    "W_p_unknown": round(c.reference.value, 6),
                    "W_baseline": round(c.method.value, 6),
                    "W_baseline_lo": round(c.method.ci_lower, 6),
                    "W_baseline_hi": round(c.method.ci_upper, 6),
                    "dW_punknown_minus_baseline": round(-c.delta_w.value, 6),
                    "dW_lo": round(-c.delta_w.ci_upper, 6),
                    "dW_hi": round(-c.delta_w.ci_lower, 6),
                })
    return out


def main() -> None:
    table = compute()
    with OUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(table[0]))
        writer.writeheader()
        writer.writerows(table)
    print(f"Wrote {len(table)} rows to {OUT}", file=sys.stderr)


if __name__ == "__main__":
    main()
