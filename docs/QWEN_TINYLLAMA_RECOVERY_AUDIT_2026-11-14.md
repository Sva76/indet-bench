# Qwen/TinyLlama exploratory recovery audit (2026-11-14)

Scope: technical audit of existing GitHub Actions run 43496061328, without modifying the frozen experimental method or dataset. These results are exploratory, not an independently validated benchmark.

## Qwen2.5-0.5B-Instruct
- Retrieved four private GitHub Actions artifact ZIPs (IDs 14072340809, 14071673622, 14072890209, 14070984677).
- Each archive contains one CSV with 120 records: total 480 distinct row IDs and 240 pair IDs, each with B and C. All rows report Qwen/Qwen2.5-0.5B-Instruct at revision 7ae557604adf67be50417f59c2c2f167def9a775.
- Independent calculation on the four CSVs: paired W=142/240=0.5916666667 (142 wins, 98 losses, no ties); pair-bootstrap percentile 95% CI [0.52916667, 0.65416667], seed 20261113, 10000 replicates; two-sided exact sign p=0.0053996267.
- Global AUROC on the 240 B and 240 C p_unknown values: 0.5127083333; paired-bootstrap 95% CI [0.5036276, 0.52255252].
- These are independently recomputed values, NOT yet a completed official workflow statistical report. Complete row-by-row identity and SHA-256 verification against the frozen source dataset and every analyzer guard remain pending. The source dataset was not altered.
- Caution: a positive paired W coexists with near-chance global AUROC; do not claim reliable uncertainty detection or generalization.

## TinyLlama-1.1B-Chat-v1.0
- All four inference shards failed at hf_runner.token_label_ids with ValueError: Overlapping first tokens for YES/NO/UNKNOWN.
- The frozen scoring rule sums first-token probabilities for label variants. Token collisions invalidate the mutually exclusive label scoring assumption. **Do not silently change to multi-token sequence probabilities, label spellings, or token filtering:** any such change is a methodological deviation requiring a separately declared protocol and new comparison, not a technical bug fix under the frozen protocol.
- The result is **not** a negative scientific finding about TinyLlama; the measurement was not obtained.
- Recommended: record exact colliding token IDs and label variants in a tokenizer-only diagnostic, then mark model as incompatible with this frozen first-token metric if collisions persist.

## Workflow isolation
- On fix/qwen-tinyllama-validation only, the analyze job was changed from if: success() to if: always() so failure of TinyLlama does not suppress Qwen analysis. This alone does not establish successful report generation; TinyLlama analysis will still fail without artifacts.
- Existing run 43496061328 predates this change. A new run and its actual report artifact must be verified before claiming workflow success.

## Proposed next external Hugging Face candidates (NOT run)
1. Qwen/Qwen2.5-1.5B-Instruct (size comparison within family).
2. HuggingFaceTB/SmolLM2-1.7B-Instruct (cross-family comparison).
3. allenai/OLMo-2-0425-1B-Instruct (cross-family comparison).

For each candidate: confirm license, immutable model revision, CPU/memory feasibility, chat template, distinct first tokens for YES/NO/UNKNOWN variants, then run the unchanged frozen dataset and analyzer. Never interpret the frozen 240 pairs as independently human-validated; all cross-model comparisons remain exploratory.
