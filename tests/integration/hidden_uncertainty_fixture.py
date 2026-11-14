"""Deterministic, paired, closed-world pilot corpus for hidden-uncertainty probes.

This is a TECHNICAL FIXTURE, not a validated scientific evaluation corpus.
The final study requires independent scenario families and blind semantic review.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import random
from pathlib import Path

NAMES = ("Mira", "Taro", "Lena", "Oren", "Suri", "Vela", "Niko", "Rami")
OBJECTS = ("badge", "parcel", "key", "folder", "ticket", "tablet", "lamp", "camera")


def build(seed: int = 20261114, count: int = 32) -> list[dict]:
    if count < 2 or count % 2:
        raise ValueError("count must be even and at least 2")
    rng = random.Random(seed)
    rows = []
    for i in range(count):
        name, other = rng.sample(NAMES, 2)
        obj = OBJECTS[i % len(OBJECTS)]
        yes = (i % 2 == 0)
        # B has a decisive positive/negative fact. C omits that fact.
        base = f"In this fictional registry, {name} and {other} are employees. The item is a {obj}. "
        decisive = f"The registry explicitly says {name} {'holds' if yes else 'does not hold'} the {obj}. "
        neutral = f"The registry lists the {obj} as an item but does not state who holds it. "
        question = f"Based only on the registry, does {name} hold the {obj}? Answer YES, NO or UNKNOWN."
        pair_id = f"fixture-{i:04d}"
        for side, fact, target in (("B", decisive, "YES" if yes else "NO"), ("C", neutral, "UNKNOWN")):
            rows.append({"row_id": f"{pair_id}-{side}", "pair_id": pair_id, "block_id": f"fixture-{i//4}",
                         "side": side, "prompt": base + fact + question, "gold": target,
                         "underdetermined": side == "C", "family": "explicit-registry-fixture",
                         "split": "technical-fixture"})
    rng.shuffle(rows)
    return rows


def validate(rows: list[dict], count: int) -> None:
    if len(rows) != 2 * count:
        raise ValueError("incorrect row count")
    ids = [x["row_id"] for x in rows]
    if len(set(ids)) != len(ids):
        raise ValueError("duplicate row IDs")
    pairs = {}
    for row in rows:
        pairs.setdefault(row["pair_id"], set()).add(row["side"])
        if (row["side"] == "C") != row["underdetermined"]:
            raise ValueError("incorrect labels")
    if len(pairs) != count or any(v != {"B", "C"} for v in pairs.values()):
        raise ValueError("incomplete B/C pairs")


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--output", required=True)
    p.add_argument("--count", type=int, default=32)
    p.add_argument("--seed", type=int, default=20261114)
    a = p.parse_args()
    rows = build(a.seed, a.count)
    validate(rows, a.count)
    raw = "".join(json.dumps(x, sort_keys=True, ensure_ascii=False) + "\n" for x in rows).encode()
    Path(a.output).write_bytes(raw)
    print(json.dumps({"status": "TECHNICAL_FIXTURE_ONLY", "rows": len(rows),
                      "pairs": a.count, "sha256": hashlib.sha256(raw).hexdigest()}))


if __name__ == "__main__":
    main()
