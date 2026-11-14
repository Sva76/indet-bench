# SmolLM2-360M-Instruct — First external-model CPU integration test

**Status: PASSED (software smoke test only).** Date: 2026-11-13.

## Evidence and provenance

- **External model:** [HuggingFaceTB/SmolLM2-360M-Instruct](https://huggingface.co/HuggingFaceTB/SmolLM2-360M-Instruct)
- **Model license (declared by provider):** Apache-2.0. No weights are committed to IndetBench.
- **Immutable model revision:** `c15f933c73438218a2bc078446c513173cc4f06a`
- **Code commit:** `a09e69310bb72603109aa4d612ffbd2e610b47aa` on the draft feature branch
- **CI:** [GitHub Actions run 43489185819](https://github.com/Sva76/indet-bench/actions/runs/43489185819) — success.
- **Output archive (GitHub Actions artifact):** [smolllm2-360m-cpu-smoke artifact](https://github.com/Sva76/indet-bench/actions/runs/43489185819/artifacts/14069690905), retained by GitHub for 7 days, with independent CSV and metric reports.
- **Runtime:** Python 3.11.18; PyTorch 2.5.1+cpu; Transformers 4.57.1; Accelerate 1.12.0; greedy, 12 maximum generated tokens, float32, batch size 1.
- **Examples:** `examples/smolllm2_smoke.jsonl`, 4 wholly invented B/C pairs (8 prompts) spanning disjunctive inference, conflicting records, assignment and an incomplete inventory.

## Technical results

| Check | Observed |
|---|---|
| Public external model fetched at exact pinned revision | PASS |
| Genuine model forward/generation invoked | PASS |
| Scores exported to CSV | 8 of 8 |
| Complete B/C pairs and consistent block IDs | 4 of 4 |
| First-token probability bounds and label-mass bookkeeping | PASS |
| Model ID/revision and row ID provenance | PASS |
| Installed IndetBench CLI computes W on CSV | PASS |
| GitHub artifact with audit reports | PASS |
| **W(C>B) on these 4 synthetic pairs** | **0.50** |
| Generic CLI bootstrap 95% CI | **[0.00, 1.00]** |

The first-token `p(UNKNOWN)` values on these four B/C pairs were approximately:

| Pair | B | C | C ranks above B? |
|---|---:|---:|---|
| 1 | 0.0420 | 0.0279 | No |
| 2 | 0.0431 | 0.0502 | Yes |
| 3 | 0.1682 | 0.1674 | No |
| 4 | 0.0241 | 0.0357 | Yes |

This is **not a model-quality benchmark**. W=0.50 with four pairs provides no evidence of reliable answerability estimation. The responses include incomplete free-form generations due to the 12-token cap; all 8 were tagged `ALTRO` by the narrow YES/NO/UNKNOWN-only parser. The smoke checker deliberately verifies score provenance and numerical correctness, **not semantic answer correctness, support status or HC4**.

## Remaining release work

1. Add a documented and independently checked answer-normalization protocol before reporting response correctness. Keep `p(UNKNOWN)` scoring distinct from the generation label.
2. Cover more model/tokenizer families and longer generations; record tokenizer, prompt templates and model commit hashes. Do not infer portability to *all* Hugging Face models from this one successful integration.
3. Finish the release readiness checklist, protocol method cards, third-party rights audit and any remaining archival parity checks.
4. Keep the project private and the pull request as draft until the owner approves review. *(Note added 14 Nov 2026: the repository has since been made public; "private" here describes its status when this was written.)*

Earlier workflow-syntax failures were resolved before this run. They were **configuration errors**, not failed inference checks.
