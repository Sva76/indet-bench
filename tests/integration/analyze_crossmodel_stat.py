"""Compare new external Hugging Face models on the existing frozen SmolLM2 corpus.

Model-specific extension of the preregistered SmolLM2 design. This is not
an independently held-out dataset nor a fresh preregistration of new hypotheses.
The underlying statistical functions are EXACTLY the ones used for SmolLM2,
including the corrected Python-integer sign-test calculation.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import json
import sys

import analyze_smol_stat as base

EXPECTED_DATASET_SHA256 = "e7d83b1e661ed34ab3c73a37481301bdab1258a5867d1ac1e57f66762f8fc36d"
MODELS = {
    "qwen05": {
        "id": "Qwen/Qwen2.5-0.5B-Instruct",
        "revision": "7ae557604adf67be50417f59c2c2f167def9a775",
        "architecture_family": "Qwen2",
    },
    "qwen15": {
        "id": "Qwen/Qwen2.5-1.5B-Instruct",
        "revision": "989aa7980e4cf806f80c7fef2b1adb7bc71aa306",
        "architecture_family": "Qwen2",
    },
    "smol17": {
        "id": "HuggingFaceTB/SmolLM2-1.7B-Instruct",
        "revision": "31b70e2e869a7173562077fd711b654946d38674",
        "architecture_family": "SmolLM2",
    },
    "olmo1": {
        "id": "allenai/OLMo-2-0425-1B-Instruct",
        "revision": "48d788eca847d4d7548f375ad03d3c9312f6139e",
        "architecture_family": "OLMo2",
    },
    "tinyllama11": {
        "id": "TinyLlama/TinyLlama-1.1B-Chat-v1.0",
        "revision": "fe8a4ea1ffedaf415f4da2f062534de366a451e6",
        "architecture_family": "Llama",
    },
}


def evaluate(input_file, score_files, model_key):
    if model_key not in MODELS:
        raise ValueError("Unknown model in frozen cross-model comparison")
    selected = MODELS[model_key]
    # Underlying analyzer validates full row coverage, all B/C identities,
    # individual model IDs and revisions, probability mass and strata balance.
    base.MODEL = selected["id"]
    base.MODEL_REVISION = selected["revision"]
    pairs, input_sha = base.parse_pairs(input_file, score_files)
    if input_sha != EXPECTED_DATASET_SHA256:
        raise ValueError("Original experimental dataset SHA-256 mismatch")
    result = base.stats(pairs, input_sha)
    result["comparison_scope"] = "secondary fixed-dataset cross-model replication"
    result["original_protocol"] = "docs/SMOLLM2_STAT_STUDY_PREREG.md"
    result["held_out_external_dataset"] = False
    result["independent_human_semantic_labels"] = False
    result["architecture_family"] = selected["architecture_family"]
    result["quality_notes"] = [
        "Secondary comparison on the very same frozen 240 pairs and prompt styles as SmolLM2.",
        "Do not describe this as independent data generalization, or claim the model family is representative.",
        "Synthetic labels are formal-generator labels; blind double-human annotation pending.",
        "Parser of YES/NO/UNKNOWN can undercount correctly worded non-canonical answers.",
        "Sign test uses exact Python integer binomial tail; original first Smol report had a p-value bug.",
        "All 480 raw scores with matched model and immutable revision are required; no selective row exclusion.",
    ]
    return result


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--input", default="data/smol_stat_v01_frozen.jsonl")
    p.add_argument("--scores", nargs="+", required=True)
    p.add_argument("--model-key", choices=tuple(MODELS), required=True)
    p.add_argument("--output", required=True)
    args = p.parse_args()
    result = evaluate(args.input, args.scores, args.model_key)
    Path(args.output).write_text(json.dumps(result, indent=2, ensure_ascii=False)+"\n", encoding="utf-8")
    print(json.dumps({
        "model": result["model"], "model_revision": result["revision"],
        "rows": result["rows"], "pairs": result["pairs"],
        "W": result["primary"]["W"], "W_CI95": result["primary"]["ci95"],
        "p_sign_two_sided": result["primary"]["sign_two_sided_p"],
        "AUROC": result["auroc"], "output": args.output
    }, indent=2))


if __name__ == "__main__":
    main()
