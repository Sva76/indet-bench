"""Pre-answer hidden-state extraction for Hugging Face causal language models.

Opt-in model downloads. No generated answer tokens are passed to the extractor.
This module only produces measurements; it does not establish a scientific effect.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
from pathlib import Path

from indetbench.hf_runner import chat_prompt, load_hf, load_pairs, token_label_ids, validate_revision

FIELDS = ("row_id", "pair_id", "block_id", "side", "model_id", "model_revision",
          "layer", "token_position", "prompt_tokens", "p_yes", "p_no", "p_unknown",
          "mass_total", "entropy", "top1_probability", "hidden_state")


def resolve_model_key(model_key, model_id):
    """Resolve "auto" exactly as hf_runner.score_pairs does.

    Without this, model_key="auto" reached chat_prompt unchanged and Qwen3
    templates were rendered with thinking enabled (the default), unlike every
    archived IndetBench run, which used enable_thinking=False.
    """
    if model_key != "auto":
        return model_key
    name = model_id.lower()
    return "qwen" if "qwen" in name else "mistral" if "mistral" in name else "other"


def extract(model, tokenizer, rows, *, model_id, revision, model_key="other",
            layer=-1, max_input_tokens=768):
    """Yield one final-input-token hidden vector per prompt, plus output baselines.

    layer indexes the transformers output.hidden_states tuple; -1 is final
    normalized hidden state. For architecture comparison, layer must be locked
    separately per model before evaluating held-out cases.
    """
    import torch

    model_key = resolve_model_key(model_key, model_id)
    token_ids = token_label_ids(tokenizer)
    device = next(model.parameters()).device
    for row in rows:
        rendered = chat_prompt(tokenizer, row["prompt"], model_key=model_key)
        encoded = tokenizer(rendered, return_tensors="pt", add_special_tokens=False)
        length = int(encoded["input_ids"].shape[1])
        if length > max_input_tokens:
            raise ValueError(f"Refusing to truncate {row['row_id']}: {length} tokens")
        encoded = encoded.to(device)
        with torch.inference_mode():
            outputs = model(**encoded, output_hidden_states=True, use_cache=False,
                            return_dict=True)
        if outputs.hidden_states is None or not outputs.hidden_states:
            raise ValueError("Model did not expose hidden states")
        if not -len(outputs.hidden_states) <= layer < len(outputs.hidden_states):
            raise ValueError("Requested layer is out of range")
        hidden = outputs.hidden_states[layer][0, -1, :].detach().float().cpu()
        logits = outputs.logits[0, -1, :].detach().float()
        if not torch.isfinite(hidden).all() or not torch.isfinite(logits).all():
            raise ValueError(f"Non-finite activations/logits for {row['row_id']}")
        probs = logits.softmax(-1)
        label_probs = {key: float(probs[ids].sum().item()) for key, ids in token_ids.items()}
        entropy = float((-(probs * probs.clamp_min(1e-30).log()).sum()).item())
        result = {
            "row_id": row["row_id"], "pair_id": row["pair_id"],
            "block_id": row["block_id"], "side": row["side"],
            "model_id": model_id, "model_revision": revision,
            "layer": layer, "token_position": "last_prompt_token",
            "prompt_tokens": length, "p_yes": label_probs["YES"],
            "p_no": label_probs["NO"], "p_unknown": label_probs["UNKNOWN"],
            "mass_total": sum(label_probs.values()), "entropy": entropy,
            "top1_probability": float(probs.max().item()),
            "hidden_state": json.dumps(hidden.tolist(), separators=(",", ":")),
        }
        yield result


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-id", required=True)
    parser.add_argument("--revision", required=True)
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--model-key", choices=("auto", "qwen", "mistral", "other"), default="auto")
    parser.add_argument("--layer", type=int, default=-1)
    parser.add_argument("--max-input-tokens", type=int, default=768)
    args = parser.parse_args(argv)
    revision = validate_revision(args.revision)
    rows = load_pairs(args.input)
    model_key = resolve_model_key(args.model_key, args.model_id)
    model, tokenizer = load_hf(args.model_id, revision=revision,
                               model_key=model_key, hf_token=os.environ.get("HF_TOKEN"))
    source_hash = hashlib.sha256(Path(args.input).read_bytes()).hexdigest()
    with Path(args.output).open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        count = 0
        for result in extract(model, tokenizer, rows, model_id=args.model_id,
                              revision=revision, model_key=model_key,
                              layer=args.layer, max_input_tokens=args.max_input_tokens):
            writer.writerow(result)
            count += 1
    print(json.dumps({"status": "RAW_FEATURES_ONLY_NOT_VALIDATED",
                      "rows": count, "pairs": count // 2,
                      "input_sha256": source_hash, "model_id": args.model_id,
                      "revision": revision, "layer": args.layer,
                      "output": args.output}, indent=2))


if __name__ == "__main__":
    main()
