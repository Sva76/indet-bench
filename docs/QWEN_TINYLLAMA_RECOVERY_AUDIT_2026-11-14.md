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


## Update: observed completed Qwen workflow (run 43579643007)
- The four Qwen inference jobs and its official final statistical report succeeded. Private report artifact: 14107084165.
- The four TinyLlama inference jobs failed and its final statistical report failed because `cross_scores/scores_tinyllama11_0.csv` was absent, as shown in the analyzer log. Overall workflow failure is therefore expected and does not invalidate the completed Qwen analysis.
- The workflow checked the frozen dataset SHA-256. The analyzer requires exactly 480 rows/240 complete pairs, exact input/output row identity, fixed model revision, valid probabilities, and balanced frozen design.
- Qwen's archived exploratory values: W=0.5916666667, 95% paired bootstrap [0.52916667, 0.65416667], two-sided sign p=0.0053996267, AUROC=0.5127083333. This is evidence for a small paired directional effect, NOT reliable global discrimination or external generalization.

## Scope of TinyLlama incompatibility (important negative technical result)
- Llama 3.1-8B and TinyLlama 1.1B are distinct checkpoints/tokenizers. A successful test on the former does not establish token-label compatibility for the latter.
- Under the frozen implementation, a first token may not belong simultaneously to distinct YES/NO/UNKNOWN label sets. The current TinyLlama tokenizer violates that assumption and the runner correctly refuses ambiguous mass assignment.
- This is a **measurement applicability failure** for this checkpoint and scoring implementation, **not** a measured negative W/AUROC, nor evidence that the model cannot internally represent uncertainty.
- A tokenizer-only diagnostic script `tests/integration/audit_label_tokenizer.py` now records exact variant encodings and cross-label token IDs, with a manually triggered, no-inference workflow `.github/workflows/tokenizer-compatibility-audit.yml`. Until that audit executes, exact collisions are not yet archived.
- Do not replace first-token scores with full-string scores under this frozen protocol. That would be a separately declared measurement study.
- **Update 2026-11-14:** the audit has run (run 43580463810); exact collisions and the final verdict are in `QWEN05_TINYLLAMA_REPORT_2026-11-14.md`.

## Follow-up model selection and comparison plan
- Candidate checkpoints: `Qwen/Qwen2.5-1.5B-Instruct`, `HuggingFaceTB/SmolLM2-1.7B-Instruct`, `allenai/OLMo-2-0425-1B-Instruct`.
- Before any inference: verify existence, immutable 40-character commit revision, license, tokenizer label-set disjointness, CPU/RAM budget and template support. None of these new candidates is yet certified or run.
- For each eligible model: same 240 frozen pairs, exact unchanged first-token scoring, same analyzer and bootstrap seed, no cherry-picking. Record W/CI95, AUROC/CI95, B accuracy, C abstention, ALTRO, prompt-length baseline, family/format/style effects and failure modes.
- Scientific comparison must distinguish within-pair ranking (W) from global separation (AUROC), behavioral abstention from probability signal, tokenization artifacts from epistemic uncertainty, and secondary cross-model replication from truly held-out generalization. The frozen synthetic labels still lack independent human semantic validation.
