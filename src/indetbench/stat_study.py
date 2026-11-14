"""Preregistered CPU statistical analysis for frozen SmolLM2 B/C dataset.

No external dataset or model is bundled. Uses fixed preregistered statistics.
Run: python -m indetbench.stat_study --input data/smol_stat_v01_frozen.jsonl
     --scores model_scores.csv --output stat_study_report.json

Never interpret a CI on 240 generated story templates as evidence for real-world
knowledge or universally reliable abstention.
"""
from __future__ import annotations

import argparse
import csv
from collections import Counter, defaultdict
from importlib.metadata import version
import json
from math import comb, isfinite
from pathlib import Path

import numpy as np

from .hf_runner import load_pairs
from .metrics import auroc

EXPECTED_MODEL = "HuggingFaceTB/SmolLM2-360M-Instruct"
EXPECTED_REVISION = "c15f933c73438218a2bc078446c513173cc4f06a"
FAMILIES = ("OR_FLEETS", "AND_SWITCH", "RULE_DIRECTION", "TEMPORAL_ORDER",
            "NUMERIC_CHOICE", "XOR_BEACONS")
STYLES = ("strict", "short")
FORMATS = ("prose", "facts")
SEED = 20261113
N_BOOT = 10000
N_PAIRS = 240


def _win(b, c):
    return 1.0 if c > b else (0.5 if c == b else 0.0)


def _describe(vals, rng=None, boots=N_BOOT):
    vals = np.asarray(vals, dtype=float)
    if not len(vals):
        raise ValueError("No complete paired scores")
    value = float(vals.mean())
    if not boots or len(vals) < 2:
        return {"value": value, "ci95": None, "n": len(vals)}
    if rng is None:
        rng = np.random.default_rng(SEED)
    replicates = np.empty(boots, float)
    for i in range(boots):
        replicates[i] = vals[rng.integers(0, len(vals), len(vals))].mean()
    return {"value": value,
            "ci95": [float(n) for n in np.quantile(replicates, [0.025, 0.975])],
            "n": len(vals)}


def _sign_test_two_sided(win_values):
    """Exact non-tie sign test; matched pairs are the independent units."""
    wins = sum(x == 1.0 for x in win_values)
    losses = sum(x == 0.0 for x in win_values)
    non_ties = wins + losses
    if not non_ties:
        return 1.0
    k = min(wins, losses)
    p = sum(comb(non_ties, i) for i in range(k + 1)) / 2 ** non_ties
    return min(1.0, 2.0 * p)


def _holm(p_values):
    """Holm family-wise adjustment for all three candidate score rankings."""
    names = sorted(p_values, key=lambda key: p_values[key])
    results = {}
    prev = 0.0
    m = len(names)
    for i, name in enumerate(names):
        prev = max(prev, min(1.0, (m - i) * p_values[name]))
        results[name] = prev
    return results


def _auc_ci(pairs, name, rng, boots=N_BOOT):
    label = [i for _ in pairs for i in (0, 1)]
    score = [x for pair in pairs for x in (pair["scores"][name]["B"],
                                             pair["scores"][name]["C"])]
    value = auroc(label, score)
    if not boots:
        return {"value": value, "ci95": None}
    replica = np.empty(boots, float)
    for i in range(boots):
        idx = rng.integers(0, len(pairs), len(pairs))
        score = [x for j in idx for x in (pairs[int(j)]["scores"][name]["B"],
                                         pairs[int(j)]["scores"][name]["C"])]
        replica[i] = auroc([k for _ in idx for k in (0, 1)], score)
    return {"value": value,
            "ci95": [float(n) for n in np.quantile(replica, [0.025, 0.975])]}


def _scores(row):
    try:
        y, n, u = [float(row[k]) for k in ("p_yes", "p_no", "p_unknown")]
        mass = float(row["mass_total"])
        primary = float(row["score"])
        tokens = int(row["prompt_tokens"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("Missing or invalid model score value") from exc
    if not all(isfinite(v) and 0 <= v <= 1+1e-5 for v in (y, n, u, mass, primary)):
        raise ValueError("Nonfinite or out-of-range model probabilities")
    if abs(mass - (y+n+u)) > 1e-5 or abs(primary-u) > 1e-7:
        raise ValueError("Label mass or score mismatch")
    if tokens <= 0 or mass <= 0:
        raise ValueError("Invalid token count or zero label mass")
    if row["model_id"] != EXPECTED_MODEL or row["model_revision"] != EXPECTED_REVISION:
        raise ValueError("Model ID or immutable revision mismatch")
    if row["parsed"] not in {"YES", "NO", "UNKNOWN", "ALTRO"}:
        raise ValueError("Invalid generated answer category")
    return {"raw_unknown": u, "normalized_unknown": u / mass,
            "inverse_max_yes_no": 1.0-max(y,n), "tokens": tokens,
            "parsed": row["parsed"]}


def analyze(input_path, score_path, *, seed=SEED, boots=N_BOOT):
    original = load_pairs(input_path)
    frozen = {row["row_id"]:row for row in original}
    if len(frozen) != 2*N_PAIRS or len(original) != 2*N_PAIRS:
        raise ValueError("Expected exactly 480 original rows and 240 B/C pairs")
    by_pair = defaultdict(dict)
    counters = Counter()
    for row in original:
        fam, fmt, style, side = [row[k] for k in ("family","format","instruction_style","side")]
        if fam not in FAMILIES or fmt not in FORMATS or style not in STYLES:
            raise ValueError("Unexpected family/format/style in frozen corpus")
        if row["gold_response"] != ("UNKNOWN" if side=="C" else row["gold_response"]):
            raise ValueError("C gold label must be UNKNOWN")
        if side=="B" and row["gold_response"] not in ("YES","NO"):
            raise ValueError("B gold label must be YES or NO")
        by_pair[row["pair_id"]][side] = row
        if side=="B":
            counters[(fam,fmt,style,row["gold_response"])] += 1
    if len(by_pair)!=N_PAIRS or any(set(v)!={"B","C"} for v in by_pair.values()):
        raise ValueError("Missing frozen story pair")
    if any(counters[(f,m,s,y)]!=5 for f in FAMILIES for m in FORMATS
           for s in STYLES for y in ("YES","NO")):
        raise ValueError("Frozen stratum balance invalid")
    for pair in by_pair.values():
        b,c = pair["B"], pair["C"]
        for key in ("family", "format","instruction_style","block_id","pair_id"):
            if b[key]!=c[key]:
                raise ValueError(f"B/C do not share {key}")
        if b["prompt"]==c["prompt"]:
            raise ValueError("B/C identical prompts")

    with Path(score_path).open(newline="", encoding="utf-8") as f:
        generated = list(csv.DictReader(f))
    if len(generated)!=len(frozen):
        raise ValueError(f"Incomplete run: {len(generated)} of {len(frozen)} rows")
    result, used = {}, set()
    for row in generated:
        key = row.get("row_id")
        if key in used or key not in frozen:
            raise ValueError("Duplicate or unexpected model row_id")
        used.add(key)
        for attr in ("pair_id","block_id","side"):
            if row.get(attr)!=frozen[key][attr]:
                raise ValueError(f"Inconsistent {attr} for {key}")
        result[key] = _scores(row)
    if used!=set(frozen):
        raise ValueError("Missing scored row")

    pairs=[]
    for key in sorted(by_pair):
        original = by_pair[key]
        b,c = original["B"], original["C"]
        scored = {"B":result[b["row_id"]], "C":result[c["row_id"]]}
        values = {n:{side:scored[side][n] for side in ("B","C")}
                  for n in ("raw_unknown","normalized_unknown","inverse_max_yes_no")}
        pairs.append({
            "pair_id":key, "family":b["family"],"format":b["format"],
            "instruction_style":b["instruction_style"],"gold_B":b["gold_response"],
            "scores":values,"parsed_B":scored["B"]["parsed"],"parsed_C":scored["C"]["parsed"],
            "token_difference_C_minus_B":scored["C"]["tokens"]-scored["B"]["tokens"],
            "char_difference_C_minus_B":len(c["prompt"])-len(b["prompt"])
        })

    names=("raw_unknown","normalized_unknown","inverse_max_yes_no")
    wins={name:[_win(p["scores"][name]["B"],p["scores"][name]["C"]) for p in pairs]
          for name in names}
    pvals={name:_sign_test_two_sided(wins[name]) for name in names}
    adjusted=_holm(pvals)
    output={"prereg_version":"smol-stat-v0.1-frozen","model":EXPECTED_MODEL,
            "model_revision":EXPECTED_REVISION,"sample_pairs":N_PAIRS,
            "raw_score_rows":len(result),"seed":seed,"bootstrap_resamples":boots,
            "metrics":{},"comparisons":{}, "subgroups":{},
            "interpretation_restriction":"Closed-world synthetic cases; independent semantic audit pending",
            "source_input":str(input_path),"source_scores":str(score_path)}
    for name in names:
        rng=np.random.default_rng(seed)
        output["metrics"][name]={"W":_describe(wins[name],rng,boots),
                                 "AUROC":_auc_ci(pairs,name,np.random.default_rng(seed+1),boots),
                                 "sign_test_two_sided_p":pvals[name],
                                 "sign_test_holm_p":adjusted[name],
                                 "wins":wins[name].count(1.0),
                                 "losses":wins[name].count(0.0),
                                 "ties":wins[name].count(0.5)}
        if name!="raw_unknown":
            diff=[x-y for x,y in zip(wins[name],wins["raw_unknown"])]
            output["comparisons"][name+"_minus_raw"]=_describe(
                diff,np.random.default_rng(seed+2),boots)
    for key,groups in (
        ("family",FAMILIES),("format",FORMATS),("instruction_style",STYLES),
        ("gold_B",("YES","NO"))
    ):
        output["subgroups"][key]={}
        for group in groups:
            selected=[p for p in pairs if p[key]==group]
            w=[_win(p["scores"]["raw_unknown"]["B"],
                    p["scores"]["raw_unknown"]["C"]) for p in selected]
            output["subgroups"][key][group]={"n_pairs":len(selected),
                                             "W_raw":sum(w)/len(w),
                                             "B_accuracy":sum(p["parsed_B"]==p["gold_B"] for p in selected)/len(selected),
                                             "C_abstention":sum(p["parsed_C"]=="UNKNOWN" for p in selected)/len(selected)}
    output["behavior"]={
        "B_correct":sum(p["parsed_B"]==p["gold_B"] for p in pairs),
        "B_incorrect_yes_no":sum(p["parsed_B"] in {"YES","NO"} and p["parsed_B"]!=p["gold_B"] for p in pairs),
        "B_false_abstention":sum(p["parsed_B"]=="UNKNOWN" for p in pairs),
        "B_invalid_format":sum(p["parsed_B"]=="ALTRO" for p in pairs),
        "C_correct_abstention":sum(p["parsed_C"]=="UNKNOWN" for p in pairs),
        "C_unsupported_yes_no":sum(p["parsed_C"] in {"YES","NO"} for p in pairs),
        "C_invalid_format":sum(p["parsed_C"]=="ALTRO" for p in pairs)}
    lengths=[p["token_difference_C_minus_B"] for p in pairs]
    charlens=[p["char_difference_C_minus_B"] for p in pairs]
    output["length_control"]={
        "mean_C_minus_B_tokens":float(np.mean(lengths)),
        "median_C_minus_B_tokens":float(np.median(lengths)),
        "proportion_abs_token_diff_gt_3":sum(abs(x)>3 for x in lengths)/len(lengths),
        "W_length_C_gt_B":sum(_win(0,x) for x in lengths)/len(lengths),
        "mean_C_minus_B_characters":float(np.mean(charlens))}
    primary=output["metrics"]["raw_unknown"]
    output["primary_conclusion"]={
        "criteria":"W 95% lower CI >0.5 and Holm-adjusted sign-test p<0.05",
        "met":primary["W"]["ci95"] is not None and
              primary["W"]["ci95"][0]>0.5 and primary["sign_test_holm_p"]<0.05}
    return output


def main(argv=None):
    p=argparse.ArgumentParser(description="Preregistered synthetic B/C study, CPU analysis")
    p.add_argument("--input",required=True)
    p.add_argument("--scores",required=True)
    p.add_argument("--output",required=True)
    p.add_argument("--bootstrap",type=int,default=N_BOOT)
    args=p.parse_args(argv)
    if not 0 <= args.bootstrap <= 20000:
        p.error("bootstrap must be 0..20000")
    report=analyze(args.input,args.scores,boots=args.bootstrap)
    Path(args.output).write_text(json.dumps(report,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({"model":report["model"],"pairs":report["sample_pairs"],
        "primary_W":report["metrics"]["raw_unknown"]["W"],
        "primary_conclusion":report["primary_conclusion"],
        "report":str(args.output)},indent=2))


if __name__=="__main__":
    main()
