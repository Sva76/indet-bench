"""Opt-in Hugging Face causal LM runner for p(UNKNOWN) on user B/C pairs.

No model weights are shipped. torch, transformers, and accelerate are optional.
Historical model parity requires pinned revisions and matching environments.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
from pathlib import Path
import re

LABELS = ("YES", "NO", "UNKNOWN")
FIELDS = ("row_id", "pair_id", "block_id", "side", "score", "p_yes", "p_no", "p_unknown",
          "mass_total", "generated", "parsed", "prompt_tokens", "model_id", "model_revision")


def load_pairs(path):
    """Validate input before downloading weights; no silent missing pair sides."""
    pairs, rows, rowids = {}, [], set()
    with Path(path).open(encoding="utf-8") as file:
        for line_number, line in enumerate(file, 1):
            if not line.strip():
                continue
            row = json.loads(line)
            for key in ("row_id", "pair_id", "block_id", "side", "prompt"):
                if not isinstance(row.get(key), str) or not row[key].strip():
                    raise ValueError(f"Line {line_number}: missing or invalid {key}")
            if row["side"] not in ("B", "C"):
                raise ValueError(f"Line {line_number}: side must be B or C")
            if row["row_id"] in rowids:
                raise ValueError(f"Line {line_number}: duplicate row_id")
            rowids.add(row["row_id"])
            pair = pairs.setdefault(row["pair_id"], {"block": row["block_id"], "sides": set()})
            if pair["block"] != row["block_id"] or row["side"] in pair["sides"]:
                raise ValueError(f"Line {line_number}: inconsistent block or duplicate side")
            pair["sides"].add(row["side"])
            rows.append(row)
    if not rows or any(item["sides"] != {"B", "C"} for item in pairs.values()):
        raise ValueError("Input must contain complete and distinct B/C pairs")
    return rows


def token_label_ids(tokenizer):
    """First tokens of six spelling/space variants, as in Test U2/M/C."""
    labels = {}
    for label in LABELS:
        variants = [prefix + word for word in (label, label.capitalize(), label.lower())
                    for prefix in ("", " ")]
        seqs = [tokenizer.encode(v, add_special_tokens=False) for v in variants]
        if any(not seq for seq in seqs):
            raise ValueError("Tokenizer produced an empty label variant")
        labels[label] = sorted({sequence[0] for sequence in seqs})
    allids = [i for tokens in labels.values() for i in tokens]
    if len(set(allids)) != len(allids):
        raise ValueError("Overlapping first tokens for YES/NO/UNKNOWN")
    return labels


def chat_prompt(tokenizer, prompt, *, model_key):
    options = {"enable_thinking": False} if model_key == "qwen" else {}
    return tokenizer.apply_chat_template([{"role": "user", "content": prompt}],
                                         tokenize=False, add_generation_prompt=True, **options)


def parse_label(text):
    m = re.match(r'^\s*[*#\x60"\']*\s*(YES|NO|UNKNOWN)\b', text, re.IGNORECASE)
    return m.group(1).upper() if m else "ALTRO"


def score_pairs(model, tokenizer, rows, *, model_key="auto", model_id="local",
                revision=None, max_new_tokens=8, max_input_tokens=None):
    """Greedy generation; sum first-token probability mass without renormalizing."""
    import torch

    if model_key == "auto":
        name = model_id.lower()
        model_key = "qwen" if "qwen" in name else "mistral" if "mistral" in name else "other"
    ids = token_label_ids(tokenizer)
    pad_id = tokenizer.pad_token_id if tokenizer.pad_token_id is not None else tokenizer.eos_token_id
    if pad_id is None:
        raise ValueError("Tokenizer has no pad_token_id or eos_token_id")
    device = getattr(model, "device", None)
    if device is None:
        device = next(model.parameters()).device
    for row in rows:
        rendered = chat_prompt(tokenizer, row["prompt"], model_key=model_key)
        enc = tokenizer(rendered, return_tensors="pt", add_special_tokens=False)
        if max_input_tokens and enc["input_ids"].shape[1] > max_input_tokens:
            raise ValueError(f"Prompt {row['row_id']} exceeds limit; refusing silent truncation")
        enc = enc.to(device)
        with torch.inference_mode():
            generated = model.generate(**enc, do_sample=False, max_new_tokens=max_new_tokens,
                                       use_cache=True, return_dict_in_generate=True,
                                       output_logits=True, pad_token_id=pad_id)
        first = generated.logits[0].float()
        if not bool(torch.isfinite(first).all()):
            raise ValueError(f"Nonfinite first-step logits: {row['row_id']}")
        distribution = first.softmax(dim=-1)[0]
        probs = {label: float(distribution[ids[label]].sum()) for label in LABELS}
        new_ids = generated.sequences[0, enc["input_ids"].shape[1]:].tolist()
        answer = tokenizer.decode(new_ids, skip_special_tokens=True)
        yield {
            "row_id": row["row_id"], "pair_id": row["pair_id"],
            "block_id": row["block_id"], "side": row["side"],
            "score": probs["UNKNOWN"], "p_yes": probs["YES"],
            "p_no": probs["NO"], "p_unknown": probs["UNKNOWN"],
            "mass_total": sum(probs.values()), "generated": answer,
            "parsed": parse_label(answer), "prompt_tokens": int(enc["input_ids"].shape[1]),
            "model_id": model_id, "model_revision": revision or "UNPINNED",
        }


def validate_revision(revision):
    """Require an immutable 40-character HF Hub commit SHA (not a branch/tag)."""
    if not isinstance(revision, str) or not re.fullmatch(r"[0-9a-fA-F]{40}", revision):
        raise ValueError("Model revision must be a 40-character hexadecimal commit SHA")
    return revision.lower()


def load_hf(model_id, *, revision=None, model_key="auto", hf_token=None):
    """Opt-in third-party download, under the original model's own license."""
    from transformers import AutoModelForCausalLM, AutoTokenizer
    import transformers

    revision = validate_revision(revision)

    key = model_key if model_key != "auto" else ("mistral" if "mistral" in model_id.lower() else "other")
    extra = {"fix_mistral_regex": True} if key == "mistral" else {}
    tokenizer = AutoTokenizer.from_pretrained(model_id, revision=revision, token=hf_token,  # nosec B615
                                              trust_remote_code=False, **extra)
    tokenizer.padding_side = "left"
    if tokenizer.pad_token_id is None and tokenizer.eos_token_id is not None:
        tokenizer.pad_token = tokenizer.eos_token
    ver = tuple(int(x) for x in transformers.__version__.split(".")[:2])
    dtype_arg = "dtype" if ver >= (4, 56) else "torch_dtype"
    model = AutoModelForCausalLM.from_pretrained(model_id, revision=revision,  # nosec B615
                                                 token=hf_token, trust_remote_code=False,
                                                 device_map="auto", use_safetensors=True, **{dtype_arg: "auto"}).eval()
    return model, tokenizer


def main(argv=None):
    parser = argparse.ArgumentParser(description="Run a local Hugging Face causal LM on B/C pairs")
    parser.add_argument("--model-id", required=True)
    parser.add_argument("--revision", required=True, help="Exact 40-character model commit SHA (required)")
    parser.add_argument("--model-key", choices=("auto", "qwen", "mistral", "other"), default="auto")
    parser.add_argument("--input", required=True, help="JSONL with row_id,pair_id,block_id,side,prompt")
    parser.add_argument("--output", required=True, help="CSV for indetbench scoring")
    parser.add_argument("--max-new-tokens", type=int, default=8)
    parser.add_argument("--max-input-tokens", type=int)
    args = parser.parse_args(argv)
    if args.max_new_tokens < 1:
        parser.error("max-new-tokens must be positive")
    rows = load_pairs(args.input)
    model, tokenizer = load_hf(args.model_id, revision=args.revision,
                               model_key=args.model_key, hf_token=os.environ.get("HF_TOKEN"))
    with Path(args.output).open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=FIELDS)
        writer.writeheader()
        for result in score_pairs(model, tokenizer, rows, model_key=args.model_key,
                                  model_id=args.model_id, revision=args.revision,
                                  max_new_tokens=args.max_new_tokens,
                                  max_input_tokens=args.max_input_tokens):
            writer.writerow(result)
    print(f"Saved {len(rows)} scores to {args.output}")
    print("Model weights and tokenizer were not redistributed by IndetBench.")


if __name__ == "__main__":
    main()
