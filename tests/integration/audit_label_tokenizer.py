"""Read-only tokenizer compatibility audit for the frozen first-token metric.

Reports exact overlaps; never changes the frozen scoring rule.
"""
from __future__ import annotations
import argparse
import json
from collections import defaultdict
from transformers import AutoTokenizer

LABELS = ("YES", "NO", "UNKNOWN")

def inspect(model_id: str, revision: str):
    tokenizer = AutoTokenizer.from_pretrained(
        model_id, revision=revision, trust_remote_code=False
    )
    token_owners = defaultdict(list)
    variants = {}
    for label in LABELS:
        variants[label] = {}
        for word in (label, label.capitalize(), label.lower()):
            for prefix in ("", " "):
                spelling = prefix + word
                ids = tokenizer.encode(spelling, add_special_tokens=False)
                variants[label][repr(spelling)] = ids
                if not ids:
                    raise ValueError(f"Empty label encoding: {label}: {spelling!r}")
                token_owners[ids[0]].append({"label": label, "spelling": spelling, "ids": ids})
    collisions = {
        str(token_id): entries for token_id, entries in token_owners.items()
        if len({entry["label"] for entry in entries}) > 1
    }
    return {
        "model_id": model_id, "revision": revision,
        "tokenizer_class": type(tokenizer).__name__,
        "compatible_with_frozen_first_token_metric": not bool(collisions),
        "cross_label_first_token_collisions": collisions,
        "all_label_variants": variants,
        "interpretation": (
            "Incompatible with this implementation of the frozen first-token metric; "
            "not evidence of inability to represent uncertainty."
            if collisions else
            "No first-token collisions found; inference compatibility not yet established."
        ),
    }

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-id", required=True)
    parser.add_argument("--revision", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    result = inspect(args.model_id, args.revision)
    with open(args.output, "w", encoding="utf-8") as handle:
        json.dump(result, handle, ensure_ascii=False, indent=2)
    print(json.dumps({
        "model_id": result["model_id"],
        "compatible": result["compatible_with_frozen_first_token_metric"],
        "collisions": result["cross_label_first_token_collisions"],
    }, indent=2))

if __name__ == "__main__":
    main()
