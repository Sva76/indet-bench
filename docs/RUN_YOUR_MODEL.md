# Test your own model (experimental Hugging Face runner)

This is an **experimental adapter API and CLI**; it has passed a CPU smoke test on SmolLM2-360M-Instruct and has been run on CPU on five more small models on the 240-pair set ([competence verdicts](COMPETENCE_240_PAIRS.md)), but general model support and semantic answer correctness are not yet validated. For every row the runner records the generated text, the parsed label (`ALTRO` when the text does not start with YES, NO or UNKNOWN) and `mass_total`, the first-token probability of all label variants, so a model that answers verbosely or with a different first token is visible (`ALTRO` count, low mass). What is still missing is a human check, on a sample of real outputs, that the parsed label matches the meaning of the generated text. It requires a separate GPU/CPU environment suitable for the weights.

## Input schema

Put paired prompts in newline-delimited JSON (JSONL). Each row must have:
`row_id`, `pair_id`, `block_id`, `side` (B or C), and `prompt`.
Rows must form complete B/C pairs. B is logically answer-determined; C is not. Do **not** claim your prompts meet that criterion without independently checking them.

An invented example is in `examples/hf_pairs.jsonl`. It contains **no natural benchmark data**.

## Installation and scoring

```bash
python -m pip install -e '.[hf]'
python -m indetbench.hf_runner --model-id Qwen/Qwen3-8B --revision YOUR_40_CHARACTER_COMMIT_SHA --model-key qwen --input examples/hf_pairs.jsonl --output my_scores.csv --max-new-tokens 8
python -m indetbench --scores my_scores.csv --bootstrap 2000
```

Replace YOUR_40_CHARACTER_COMMIT_SHA with a full immutable commit SHA from the model provider's revision history. Branch names such as `main` are not accepted; this also enables safe supply-chain auditing. The runner currently requires `safetensors` weights and refuses pickle-only models.\n\nFor restricted model repositories, obtain access from the model provider and set `HF_TOKEN` in your own environment (do not store it in the repository). The runner **requires** `--revision` to be a full 40-character commit SHA for every execution.

## What gets measured

The Hugging Face runner:
- applies the model's user chat template, disabling Qwen thinking when selected;
- runs greedy generation, batch size 1, without silently truncating inputs;
- computes the **unconditional** first-token masses of YES/NO/UNKNOWN, including the original upper/lower/title-case variants with/without leading space;
- writes a CSV with `pair_id,block_id,side,score` where score is `p(UNKNOWN)`;
- includes generated answers and metadata for auditing.

Scores are **not** renormalized to the three possible labels. The user must supply logically verified B/C prompts. First-token probabilities are not a universal truth detector. On some tokenizers the first-token ID sets overlap; the runner refuses to score rather than silently generating an invalid benchmark.

## Known limits

Model cards, gated access conditions and third-party licenses still apply. No weights are distributed. GPU memory requirements depend on the selected model. The adapter has unit tests with fake inputs/tokenizers and has run pinned CPU inference on six small Hugging Face models (one smoke test and five 240-pair runs); TinyLlama-1.1B is refused because the first tokens of YES/NO/UNKNOWN collide. The exact archived Test U/M/C model revisions, tokenizer and package versions are needed to claim historical bit-for-bit parity.

## Verified external-model smoke test

A pinned run on [SmolLM2-360M-Instruct](https://huggingface.co/HuggingFaceTB/SmolLM2-360M-Instruct) passed all technical checks on 2026-11-13. It used 4 synthetic B/C pairs and produced 8 valid score rows. W was 0.50 (not a scientific model-performance conclusion). See [smoke-test report](SMOLLM2_EXTERNAL_SMOKE.md) and the linked GitHub Actions artifact.
