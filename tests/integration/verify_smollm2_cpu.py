"""Validate one real-model IndetBench smoke output without claiming model quality.

Consumes the published synthetic smoke JSONL and generated CSV. Must pass
before a successful integration run may be reported.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
from importlib.metadata import version

from indetbench import PairScore, w_score
from indetbench.hf_runner import load_pairs

MODEL="HuggingFaceTB/SmolLM2-360M-Instruct"
REVISION="c15f933c73438218a2bc078446c513173cc4f06a"


def validate(input_path, score_path):
    source=load_pairs(input_path)
    expected={row["row_id"]:row for row in source}
    with Path(score_path).open(newline="", encoding="utf-8") as f:
        rows=list(csv.DictReader(f))
    if len(rows)!=len(expected):
        raise ValueError(f"Expected {len(expected)} generated rows; got {len(rows)}")
    ids=set()
    scored=[]
    outcomes=[]
    for row in rows:
        rowid=row.get("row_id")
        if rowid in ids or rowid not in expected:
            raise ValueError("Duplicate or unexpected output row_id")
        ids.add(rowid)
        orig=expected[rowid]
        for field in ("pair_id","block_id","side"):
            if row.get(field)!=orig[field]:
                raise ValueError(f"Mismatch in {field}: {rowid}")
        if row.get("model_id")!=MODEL or row.get("model_revision")!=REVISION:
            raise ValueError("Unexpected model identity or revision")
        probs=[float(row[x]) for x in ("p_yes","p_no","p_unknown","mass_total")]
        if any(not math.isfinite(x) or x < 0 or x > 1+1e-5 for x in probs):
            raise ValueError(f"Probability out of bounds: {rowid}")
        if abs(sum(probs[:3])-probs[3])>1e-6:
            raise ValueError("Summed label probability mismatch")
        if abs(float(row["score"])-float(row["p_unknown"]))>1e-8:
            raise ValueError("Reference score differs from p_unknown")
        if int(row["prompt_tokens"])<=0:
            raise ValueError("Missing model prompt token count")
        # The smoke test checks execution, not whether the model understands logic.
        scored.append(PairScore(row["pair_id"],row["block_id"],row["side"],float(row["score"])))
        outcomes.append({"row_id":rowid,"side":row["side"],
                         "p_unknown":float(row["p_unknown"]),
                         "answer":row["generated"][:256],
                         "parsed":row["parsed"]})
    if ids!=set(expected):
        raise ValueError("Missing output IDs")
    est=w_score(scored,n_bootstrap=0)
    return {"smoke_status":"PASS","model":MODEL,"model_revision":REVISION,
            "rows":len(rows),"pairs":est.n_pairs,"blocks":est.n_blocks,
            "W":est.value,"inference_performed":True,
            "model_performance_validated":False,"responses":outcomes}


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--scores", required=True)
    parser.add_argument("--report", required=True)
    args=parser.parse_args()
    result=validate(args.input,args.scores)
    import platform
    result["python"]=platform.python_version()
    result["transformers"]=version("transformers")
    result["torch"]=version("torch")
    Path(args.report).parent.mkdir(parents=True,exist_ok=True)
    Path(args.report).write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"status":result["smoke_status"],"pairs":result["pairs"],
                      "W_descriptive":result["W"],"model":result["model"],
                      "revision":result["model_revision"]},indent=2))


if __name__=="__main__":
    main()
