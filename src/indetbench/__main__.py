"""CPU-only command-line interface; optional model execution comes later."""
from __future__ import annotations

import argparse
from dataclasses import asdict
import json

from . import compare_to_reference, load_pair_scores_csv, w_score


def main() -> None:
    parser = argparse.ArgumentParser(description="IndetBench B/C score evaluation (CPU)")
    parser.add_argument("--scores", required=True, help="CSV: pair_id,block_id,side,score")
    parser.add_argument("--reference", help="Optional CSV with p(UNKNOWN) scores")
    parser.add_argument("--bootstrap", type=int, default=2000)
    parser.add_argument("--seed", type=int, default=20261108)
    args = parser.parse_args()
    rows = load_pair_scores_csv(args.scores)
    if args.reference:
        comparison = compare_to_reference(
            rows, load_pair_scores_csv(args.reference), n_bootstrap=args.bootstrap, seed=args.seed
        )
        result = asdict(comparison)
    else:
        result = asdict(w_score(rows, n_bootstrap=args.bootstrap, seed=args.seed))
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
