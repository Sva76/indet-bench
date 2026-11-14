"""Original Step 2 logic benchmark (Tests U2/M): export for new models and report.

The frozen file `research_originals/step2/frozen/M_Original_4800_righe.json.gz` holds
the 4,800 prompts used in Test U2 and Test M: 200 stories x 3 families x 2 variants
(POS/NOT) x 2 positions x A/B/C, in prose without the explanatory sentence (set PN,
"P-S" in the reports) and in symbolic form (set SN, "S-S").

Two commands, both CPU-only:

    python -m indetbench.original_benchmark export --set PN --output original_PS.jsonl
    python -m indetbench.original_benchmark report --scores my_model_scores.csv

`export` writes the B/C rows in the input format of `indetbench.hf_runner`;
`report` reads the runner's CSV, recomputes W of p(UNKNOWN) with the story as the
resampling unit, and reports per-family W and the model's generated answers.
"""
from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
from collections import Counter, defaultdict
from dataclasses import asdict
from pathlib import Path

from .metrics import PairScore, w_score

FROZEN_SHA256 = "906c01bf2988607247b4b06f92b15d189bcb49278a6964ae2479b2236f96d459"
DEFAULT_FROZEN = (Path(__file__).resolve().parents[2]
                  / "research_originals/step2/frozen/M_Original_4800_righe.json.gz")
FAMILIES = ("AND", "OR", "IMPLIES")
SETS = {"PN": "prose without explanatory sentence (P-S, primary in Tests U2/M)",
        "SN": "symbolic without explanatory sentence (S-S, descriptive)"}

# Published values for comparison (Test U2, P-S, p(UNKNOWN), 800 pairs, 200 stories,
# 95% story-bootstrap CI). Source: research_originals/step2/results/Risultati_testU2.md.
REFERENCE_W_PS = {
    "Qwen/Qwen3-8B@b968826d9c46dd6066d109eabc6255188de91218": (0.975, 0.964, 0.985),
    "mistralai/Mistral-Nemo-Instruct-2407@04d8a90549d23fc6bd7f642064003592df51e9b3": (0.783, 0.751, 0.811),
    "allenai/OLMo-2-1124-7B-Instruct@470b1fba1ae01581f270116362ee4aa1b97f4c84": (0.694, 0.651, 0.735),
    "meta-llama/Llama-3.1-8B-Instruct@0e9e39f249a16976918f6564b8830bc894c89659": (0.746, 0.704, 0.785),
}
# Binding competence gate for NEW models (owner decision of 14 November 2026, fixed before
# any new-model data). The original protocols of Tests U2/M had no such gate. Overall
# accuracy of the generated answer on the determined B cases of the prose set (PN) must be
# at least 0.50; below it the primary result is NOT EVALUABLE, because the model does not
# perform the task. A 0.80 gate would have excluded Mistral-Nemo (0.57); 0.50 keeps all four
# original models and excludes models that do not answer determined cases (SmolLM2-360M:
# 0.38 on the separate 240-pair set). Per-family accuracy stays descriptive.
COMPETENCE_GATE_B_ACCURACY = 0.50
GATE_SUBSET = "PN"

# Generated-answer accuracy on B, P-S, same runs (env_m1 reference of Test M, identical
# to Test U2). Descriptive: the original protocols had no competence gate on B.
REFERENCE_B_ACCURACY_PS = {
    "Qwen/Qwen3-8B": {"AND": 1.000, "OR": 1.000, "IMPLIES": 1.000, "all": 1.000},
    "mistralai/Mistral-Nemo-Instruct-2407": {"AND": 0.690, "OR": 0.597, "IMPLIES": 0.420, "all": 0.570},
    "allenai/OLMo-2-1124-7B-Instruct": {"AND": 1.000, "OR": 0.802, "IMPLIES": 0.572, "all": 0.792},
    "meta-llama/Llama-3.1-8B-Instruct": {"AND": 0.978, "OR": 0.996, "IMPLIES": 0.852, "all": 0.943},
}


def load_frozen(path: str | Path = DEFAULT_FROZEN) -> list[dict]:
    """Load the frozen rows and refuse any file whose content hash differs."""
    raw = gzip.decompress(Path(path).read_bytes())
    digest = hashlib.sha256(raw).hexdigest()
    if digest != FROZEN_SHA256:
        raise ValueError(f"Frozen benchmark SHA-256 mismatch: {digest}")
    rows = json.loads(raw)
    if len(rows) != 4800:
        raise ValueError(f"Expected 4800 rows, found {len(rows)}")
    return rows


def export_rows(rows: list[dict], subset: str = "PN") -> list[dict]:
    """B/C rows of one subset in hf_runner format; prompts are copied unchanged."""
    if subset not in SETS:
        raise ValueError(f"Unknown subset {subset!r}; choose one of {sorted(SETS)}")
    out = []
    for row in rows:
        if row["set"] != subset or row["kind"] not in ("B", "C"):
            continue
        out.append({
            "row_id": row["row_id"],
            "pair_id": f"{row['set']}|{row['pair_key']}",
            "block_id": row["story_id"],
            "side": row["kind"],
            "prompt": row["prompt"],
            "family": row["family"],
            "variant": row["variant"],
            "position": row["position"],
            "gold": row["condition"],
        })
    pairs = Counter(r["pair_id"] for r in out)
    if len(out) != 1600 or len(pairs) != 800 or set(pairs.values()) != {2}:
        raise ValueError("Export does not contain 800 complete B/C pairs")
    return out


def _read_scores(path: str | Path) -> list[dict]:
    with Path(path).open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def report(score_rows: list[dict], rows: list[dict], *, n_bootstrap: int = 2000,
           seed: int = 20261108) -> dict:
    """W overall and per family, plus generated-answer behaviour, from runner output."""
    gold = {r["row_id"]: r for r in rows}
    missing = [s["row_id"] for s in score_rows if s["row_id"] not in gold]
    if missing:
        raise ValueError(f"{len(missing)} rows are not in the frozen benchmark, e.g. {missing[0]}")
    subsets = {gold[s["row_id"]]["set"] for s in score_rows}
    if len(subsets) != 1:
        raise ValueError(f"Scores mix subsets {sorted(subsets)}; report one subset at a time")
    models = {(s.get("model_id"), s.get("model_revision")) for s in score_rows}
    pairs = [PairScore(s["pair_id"], s["block_id"], s["side"], float(s["score"])) for s in score_rows]
    result = {
        "subset": subsets.pop(),
        "models": sorted(f"{m}@{r}" for m, r in models),
        "n_rows": len(score_rows),
        "W_p_unknown": asdict(w_score(pairs, n_bootstrap=n_bootstrap, seed=seed)),
        "W_by_family_descriptive": {},
        "behaviour": {},
    }
    for family in FAMILIES:
        subset = [p for p, s in zip(pairs, score_rows) if gold[s["row_id"]]["family"] == family]
        result["W_by_family_descriptive"][family] = w_score(subset, n_bootstrap=0).value
    counts = defaultdict(Counter)
    for s in score_rows:
        g = gold[s["row_id"]]
        key = (g["kind"], g["family"])
        parsed = s.get("parsed", "ALTRO")
        counts[key]["n"] += 1
        counts[key]["correct"] += parsed == g["condition"]
        counts[key][parsed] += 1
    for (side, family), c in sorted(counts.items()):
        result["behaviour"][f"{side}/{family}"] = {
            "n": c["n"], "accuracy": c["correct"] / c["n"],
            "answers": {k: c[k] for k in ("YES", "NO", "UNKNOWN", "ALTRO") if c[k]},
        }
    labels_seen = {s.get("parsed") for s in score_rows}
    result["warnings"] = [f"label never generated: {label}" for label in ("YES", "NO", "UNKNOWN")
                          if label not in labels_seen]
    b_rows = [s for s in score_rows if gold[s["row_id"]]["kind"] == "B"]
    b_accuracy = sum(s.get("parsed") == gold[s["row_id"]]["condition"] for s in b_rows) / len(b_rows)
    passed = b_accuracy >= COMPETENCE_GATE_B_ACCURACY
    result["competence_gate"] = {
        "rule": "accuracy of generated answers on all B cases >= 0.50 (binding for new models, "
                "prose set PN; decided 14 Nov 2026 before new-model data; not part of the "
                "original Test U2/M protocols)",
        "threshold": COMPETENCE_GATE_B_ACCURACY, "accuracy_B": b_accuracy, "n_B": len(b_rows),
        "passed": passed,
        # Descriptive: 532 of 800 B cases have gold YES (OR, IMPLIES) and 268 gold NO (AND),
        # so a model that always answers YES reaches 0.665 overall.
        "accuracy_B_by_gold": {label: sum(s.get("parsed") == label for s in grp) / len(grp)
                               for label in ("NO", "YES")
                               for grp in [[s for s in b_rows if gold[s["row_id"]]["condition"] == label]]
                               if grp},
    }
    result["verdict"] = verdict(result["W_p_unknown"], passed, result["subset"])
    result["published_reference_P-S"] = {k: dict(zip(("W", "ci_lower", "ci_upper"), v))
                                         for k, v in REFERENCE_W_PS.items()}
    return result


def verdict(w: dict, gate_passed: bool, subset: str) -> str:
    """Decision rule of HU1/HI1 (Tests U/U2), preceded by the competence gate."""
    if subset != GATE_SUBSET:
        return "DESCRIPTIVE (only the prose set PN has a decision rule)"
    if not gate_passed:
        return "NOT EVALUABLE (competence gate on B not passed)"
    if w["ci_lower"] is None or w["ci_upper"] is None:
        return "NO INTERVAL (bootstrap disabled; rerun with --bootstrap 2000)"
    if w["ci_lower"] > 0.5 and w["value"] >= 0.60:
        return "CONFIRMED"
    if w["ci_upper"] <= 0.5:
        return "NOT CONFIRMED"
    return "NOT CONCLUSIVE"


def main(argv=None) -> None:
    parser = argparse.ArgumentParser(description="Original Step 2 benchmark: export and report")
    sub = parser.add_subparsers(dest="command", required=True)
    ex = sub.add_parser("export", help="write B/C rows as hf_runner JSONL")
    ex.add_argument("--set", default="PN", choices=sorted(SETS))
    ex.add_argument("--output", required=True)
    ex.add_argument("--frozen", default=str(DEFAULT_FROZEN))
    rp = sub.add_parser("report", help="W and behaviour from an hf_runner CSV")
    rp.add_argument("--scores", required=True)
    rp.add_argument("--frozen", default=str(DEFAULT_FROZEN))
    rp.add_argument("--bootstrap", type=int, default=2000)
    rp.add_argument("--seed", type=int, default=20261108)
    args = parser.parse_args(argv)
    rows = load_frozen(args.frozen)
    if args.command == "export":
        out = export_rows(rows, args.set)
        with Path(args.output).open("w", encoding="utf-8") as handle:
            for row in out:
                handle.write(json.dumps(row, ensure_ascii=False) + "\n")
        print(f"Wrote {len(out)} rows (800 B/C pairs, 200 stories, set {args.set}) to {args.output}")
    else:
        print(json.dumps(report(_read_scores(args.scores), rows, n_bootstrap=args.bootstrap,
                                seed=args.seed), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
