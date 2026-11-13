"""Select a reproducible, disjoint shard from the frozen SmolLM2 JSONL."""
from __future__ import annotations
import argparse
import json
from pathlib import Path

def shard_file(input_path, output_path, shard, total):
    if not (0 <= shard < total):
        raise ValueError("Shard index must be in [0,total)")
    rows=[json.loads(line) for line in Path(input_path).read_text(encoding="utf-8").splitlines() if line.strip()]
    if len(rows)!=480 or len({r["pair_id"] for r in rows})!=240:
        raise ValueError("Unexpected frozen study dataset cardinality")
    pairs=sorted({r["pair_id"] for r in rows})
    assigned={pid for i,pid in enumerate(pairs) if i % total==shard}
    selected=[r for r in rows if r["pair_id"] in assigned]
    if len(selected)!=2*len(assigned) or len({r["row_id"] for r in selected})!=len(selected):
        raise ValueError("Shard has incomplete or repeated B/C rows")
    Path(output_path).write_text("".join(json.dumps(r,ensure_ascii=False)+"\n" for r in selected),encoding="utf-8")
    print(f"Shard {shard}/{total}: {len(assigned)} pairs, {len(selected)} rows")

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--input",default="data/smol_stat_v01_frozen.jsonl")
    p.add_argument("--output",required=True)
    p.add_argument("--shard",type=int,required=True)
    p.add_argument("--total",type=int,default=4)
    a=p.parse_args()
    shard_file(a.input,a.output,a.shard,a.total)
