"""Predeclared paired SmolLM2 statistics; no ex-post dataset filtering.

Frozen protocol: docs/SMOLLM2_STAT_STUDY_PREREG.md.
Only accepts all 480 raw inference outputs from the 240 frozen B/C pairs.
"""
from __future__ import annotations
import argparse
from collections import Counter, defaultdict
from hashlib import sha256
import csv
import json
from math import comb, isfinite
from pathlib import Path
import platform

import numpy as np

from indetbench import auroc

MODEL = "HuggingFaceTB/SmolLM2-360M-Instruct"
MODEL_REVISION = "c15f933c73438218a2bc078446c513173cc4f06a"
SEED = 20261113
N_BOOT = 10000
FAMILIES = ("OR_FLEETS", "AND_SWITCH", "RULE_DIRECTION",
            "TEMPORAL_ORDER", "NUMERIC_CHOICE", "XOR_BEACONS")
FORMATS = ("prose", "facts")
STYLES = ("strict", "short")


def qinterval(values):
    a=np.asarray(values, dtype=float)
    return [float(v) for v in np.quantile(a, (0.025,0.975))]


def win(b,c):
    return 1.0 if c>b else 0.5 if c==b else 0.0


def sign_p(wins):
    # Cast NumPy bool sums to Python ints. numpy.int64 exponentiation
    # silently wraps 2**n to zero when n >= 64, falsely giving p=1.
    npos=int(sum(x>0.5 for x in wins))
    nneg=int(sum(x<0.5 for x in wins))
    n=npos+nneg
    if n==0:
        return 1.0
    return min(1.0,2*sum(comb(n,i) for i in range(min(npos,nneg)+1))/(2**n))


def holm_adjust(p):
    order=sorted(range(len(p)), key=lambda i:p[i])
    result=[None]*len(p)
    ceiling=0.0
    for rank,idx in enumerate(order):
        ceiling=max(ceiling, min(1.0,(len(p)-rank)*p[idx]))
        result[idx]=ceiling
    return result


def parse_pairs(frozen_path, score_paths):
    raw=Path(frozen_path).read_bytes()
    frozen=[json.loads(line) for line in raw.splitlines() if line.strip()]
    if len(frozen)!=480:
        raise ValueError(f"Expected 480 frozen input rows, found {len(frozen)}")
    identity={r["row_id"]:r for r in frozen}
    if len(identity)!=len(frozen):
        raise ValueError("Duplicate frozen row_id")
    groups=defaultdict(list)
    for r in frozen:
        if (r.get("dataset_version")!="smol-stat-v0.1-frozen"
            or r.get("gold_response") not in ("YES","NO","UNKNOWN")
            or r.get("side") not in ("B","C")
            or r.get("family") not in FAMILIES
            or r.get("format") not in FORMATS
            or r.get("instruction_style") not in STYLES):
            raise ValueError("Unexpected frozen study schema")
        groups[r["pair_id"]].append(r)
    if len(groups)!=240:
        raise ValueError("Frozen study must contain exactly 240 pairs")
    cell_counts=Counter()
    for pid,rows in groups.items():
        if set(r["side"] for r in rows)!={"B","C"} or len(rows)!=2:
            raise ValueError(f"Invalid B/C pair {pid}")
        b=next(r for r in rows if r["side"]=="B")
        c=next(r for r in rows if r["side"]=="C")
        if (b["gold_response"] not in ("YES","NO") or c["gold_response"]!="UNKNOWN"
            or any(b[field]!=c[field] for field in ("family","format","instruction_style","block_id"))):
            raise ValueError("Invalid frozen labels or pair metadata: "+pid)
        cell_counts[(b["family"],b["format"],b["instruction_style"],b["gold_response"])]+=1
    if any(cell_counts[(f,m,s,label)]!=5 for f in FAMILIES for m in FORMATS
           for s in STYLES for label in ("YES","NO")):
        raise ValueError("Unbalanced frozen experimental design")

    observed={}
    for path in score_paths:
        with Path(path).open(encoding="utf-8",newline="") as f:
            for row in csv.DictReader(f):
                rid=row["row_id"]
                if rid in observed or rid not in identity:
                    raise ValueError("Duplicate or unknown inference row "+rid)
                orig=identity[rid]
                for field in ("pair_id","block_id","side"):
                    if row[field]!=orig[field]:
                        raise ValueError(f"Input/output identity mismatch {rid}: {field}")
                if row["model_id"]!=MODEL or row["model_revision"]!=MODEL_REVISION:
                    raise ValueError(f"Unexpected model revision on {rid}")
                nums={k:float(row[k]) for k in
                      ("score","p_yes","p_no","p_unknown","mass_total")}
                if any(not isfinite(v) or v<0 or v>1+1e-6 for v in nums.values()):
                    raise ValueError(f"Invalid probability {rid}")
                if (abs(nums["score"]-nums["p_unknown"])>1e-8
                    or abs(nums["mass_total"]-sum(nums[k] for k in ("p_yes","p_no","p_unknown")))>1e-6
                    or nums["mass_total"]<=0):
                    raise ValueError(f"Invalid probability identity {rid}")
                token_count=int(row["prompt_tokens"])
                if token_count<=0:
                    raise ValueError(f"Invalid prompt token count {rid}")
                answer=row["parsed"]
                if answer not in ("YES","NO","UNKNOWN","ALTRO"):
                    raise ValueError(f"Unknown generated label {rid}")
                observed[rid]={**row,**nums,"prompt_tokens":token_count}
    if len(observed)!=480 or set(observed)!=set(identity):
        raise ValueError(f"Expected exactly 480 complete inference outputs; got {len(observed)}")
    pairs=[]
    for pid in sorted(groups):
        items={r["side"]:r for r in groups[pid]}
        b,c=(observed[items[side]["row_id"]] for side in ("B","C"))
        pairs.append((items["B"],b,c))
    return pairs,sha256(raw).hexdigest()


def stats(pairs, raw_sha):
    rng=np.random.default_rng(SEED)
    n=len(pairs)
    bs=rng.integers(0,n,(N_BOOT,n))
    selectors={"raw":lambda row:row["p_unknown"],
               "normalized":lambda row:row["p_unknown"]/row["mass_total"],
               "one_minus_max_YN":lambda row:1-max(row["p_yes"],row["p_no"]),
               "input_token_length":lambda row:row["prompt_tokens"]}
    arrays={}
    for name,selector in selectors.items():
        arrays[name]=np.asarray([win(selector(b),selector(c)) for _,b,c in pairs])
    output={"dataset_sha256":raw_sha, "model":MODEL, "revision":MODEL_REVISION,
            "rows":2*n,"pairs":n, "bootstrap":"pair/stories, percentile 95%",
            "bootstrap_replicates":N_BOOT, "bootstrap_seed":SEED,
            "inference_is_real":True,
            "claim_of_external_generalization":False}
    w=arrays["raw"]
    output["primary"]={
        "metric":"W = p_UNKNOWN(C) > p_UNKNOWN(B), ties worth 0.5",
        "W":float(w.mean()),
        "ci95":qinterval(w[bs].mean(axis=1)),
        "wins":int(sum(w>0.5)), "losses":int(sum(w<0.5)),
        "ties":int(sum(w==0.5)),
        "sign_two_sided_p":sign_p(w),
        "null":0.5,
    }
    output["primary"]["reject_h0"]=bool(output["primary"]["ci95"][0]>0.5 and output["primary"]["sign_two_sided_p"]<0.05)
    output["alternatives"]={}
    alternate_keys=("normalized","one_minus_max_YN")
    ps=[]
    for name in alternate_keys:
        values=arrays[name]
        diff=values-w
        p=sign_p([0.5+d for d in diff])
        ps.append(p)
        output["alternatives"][name]={"W":float(values.mean()),"ci95":qinterval(values[bs].mean(axis=1)),
                                      "delta_W_vs_raw":float(diff.mean()),
                                      "delta_ci95":qinterval(diff[bs].mean(axis=1)),
                                      "sign_two_sided_p_unadjusted":p}
    for name,p in zip(alternate_keys,holm_adjust(ps)):
        output["alternatives"][name]["sign_p_holm_2"]=p
    length=arrays["input_token_length"]
    output["length_confound"]={"W_using_C_longer":float(length.mean()),
                               "W_using_B_longer":float((1-length).mean()),
                               "abs_token_diff_gt_3":int(sum(abs(b["prompt_tokens"]-c["prompt_tokens"])>3 for _,b,c in pairs)),
                               "mean_C_minus_B_tokens":float(np.mean([c["prompt_tokens"]-b["prompt_tokens"] for _,b,c in pairs]))}
    labels=[0]*n+[1]*n
    pvals=[b["p_unknown"] for _,b,c in pairs]+[c["p_unknown"] for _,b,c in pairs]
    output["auroc"]={"value":auroc(labels,pvals)}
    auc_samples=[]
    for ix in bs:
        bsco=[pairs[i][1]["p_unknown"] for i in ix]
        csco=[pairs[i][2]["p_unknown"] for i in ix]
        auc_samples.append(auroc([0]*n+[1]*n,bsco+csco))
    output["auroc"]["ci95"]=qinterval(auc_samples)

    b_answer=[b["parsed"] for _,b,c in pairs]
    c_answer=[c["parsed"] for _,b,c in pairs]
    correct_b=[1 if b["parsed"]==meta["gold_response"] else 0 for meta,b,c in pairs]
    output["behavior"]={
        "B_correct":sum(correct_b),
        "B_accuracy":sum(correct_b)/n,
        "C_abstain":sum(ans=="UNKNOWN" for ans in c_answer),
        "C_abstain_rate":sum(ans=="UNKNOWN" for ans in c_answer)/n,
        "B_inappropriate_abstain":sum(ans=="UNKNOWN" for ans in b_answer),
        "C_overanswer":sum(ans in ("YES","NO") for ans in c_answer),
        "B_invalid_ALTRO":sum(ans=="ALTRO" for ans in b_answer),
        "C_invalid_ALTRO":sum(ans=="ALTRO" for ans in c_answer),
        "B_label_counts":dict(Counter(b_answer)),
        "C_label_counts":dict(Counter(c_answer)),
    }
    output["subgroups"]={}
    for field,vals in [("family",FAMILIES),("format",FORMATS),("instruction_style",STYLES),
                       ("B_gold",("YES","NO"))]:
        output["subgroups"][field]={}
        for category in vals:
            ids=[i for i,(meta,b,c) in enumerate(pairs) if
                 (meta["gold_response"] if field=="B_gold" else meta[field])==category]
            sub=w[ids]
            output["subgroups"][field][category]={
                "pairs":len(ids),"W":float(sub.mean()),
                "B_accuracy":float(np.mean([correct_b[i] for i in ids])),
                "C_abstention":float(np.mean([c_answer[i]=="UNKNOWN" for i in ids]))}
            # subgroup estimates descriptive only; family tests not preregistered primary
    output["quality_notes"]=[
        "One 360M external model; findings are model-specific and exploratory outside the primary endpoint.",
        "Semantic determinability assertions derive from synthetic generators, not independent double-human annotation.",
        "Model response parser recognizes YES, NO, UNKNOWN only; ALTRO is counted, never excluded.",
        "Results have no unpaired filtering or post-hoc exclusion; input cardinalities strictly checked.",
        "No empirical statement of priority or general superiority over published uncertainty benchmarks."
    ]
    output["runtime"]={"python":platform.python_version()}
    return output


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--input",default="data/smol_stat_v01_frozen.jsonl")
    p.add_argument("--scores",nargs="+",required=True)
    p.add_argument("--output",required=True)
    args=p.parse_args()
    pairs,raw_hash=parse_pairs(args.input,args.scores)
    report=stats(pairs,raw_hash)
    Path(args.output).write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(json.dumps({"rows":report["rows"],"pairs":report["pairs"],
        "W":report["primary"]["W"],"ci95":report["primary"]["ci95"],
        "two_sided_sign_p":report["primary"]["sign_two_sided_p"],
        "primary_reject_h0":report["primary"]["reject_h0"],
        "B_accuracy":report["behavior"]["B_accuracy"],
        "C_abstention":report["behavior"]["C_abstain_rate"],
        "dataset_sha256":report["dataset_sha256"]},indent=2))


if __name__=="__main__":
    main()
