# Qwen2.5-0.5B and TinyLlama-1.1B on the 240-pair corpus — report (2026-11-14)

Scope: completion of `QWEN_TINYLLAMA_RECOVERY_AUDIT_2026-11-14.md`. Corpus `data/smol_stat_v01_frozen.jsonl` (240 B/C pairs, frozen, SHA-256 `e7d83b1e…c36d`, **not independently validated**). All results are **EXPLORATORY**. No dataset, prompt, scoring rule, threshold or statistic was changed.

## Qwen2.5-0.5B-Instruct (revision `7ae55760…a775`)

| Item | Before | After |
|---|---|---|
| Report | Official report artifact of run 43579643007 (W, AUROC in the log; B accuracy only inside the artifact) | Re-analysis of the same raw scores with the unchanged analyzer (run of `reanalyze-archived-cpu-scores.yml`), full behaviour block printed |
| W [95% CI] | 0.5916666667 [0.52916667, 0.65416667] | identical |
| AUROC | 0.5127083333 | identical |
| Competence | not applied | applied (`competence_gate_240.py`) |

Analyzer guards passed: 480 rows, 240 complete pairs, row identity with the frozen input, pinned model and revision, valid probabilities.

Behaviour: B accuracy 0.625 overall, **0.383 on gold YES** (46/120), 0.867 on gold NO; B answers YES 52 / NO 173 / UNKNOWN 15; C abstention 0.058.

**Verdict (official rule, ≥ 0.50 overall and per gold label): NOT EVALUABLE** (fails on gold YES). Theoretical sensitivity at chance (1/3): would pass, but its YES accuracy is not distinguishable from chance (one-sided exact binomial p = 0.14). Anomaly class: **model** (answer bias towards NO).

## TinyLlama-1.1B-Chat-v1.0 (revision `fe8a4ea1…51e6`)

| Item | Before | After |
|---|---|---|
| Inference (run 43496061328 and later) | 4 shards failed: `ValueError: Overlapping first tokens for YES/NO/UNKNOWN` | unchanged: the runner correctly refuses (no method change) |
| Analysis job | failed with missing `scores_tinyllama11_*.csv` | no longer scheduled: `hf-crossmodel-stat.yml` analyse matrix lists only models that are run (fixed in PR #5) |
| Cause | not archived | archived from tokenizer audit run 43580463810 (below) |

Cause (from the tokenizer-only audit, no inference): with this SentencePiece tokenizer, every leading-space label variant is encoded as the bare word-boundary token **29871** followed by the word, e.g. `" YES" → [29871, 22483]`, `" NO" → [29871, 11698]`, `" unknown" → [29871, 9815]`. All six space-prefixed variants of YES, NO and UNKNOWN therefore share the first token 29871, so first-token probability mass cannot be assigned to one label. The other audited tokenizers (Qwen2.5-0.5B, Qwen2.5-1.5B, SmolLM2-1.7B, OLMo-2-0425-1B) have no collision.

**Verdict: NOT MEASURED.** Anomaly class: **technique** (applicability limit of the first-token metric to this tokenizer). It is not a result about the model. Making TinyLlama measurable would require a different label-scoring rule (for example skipping a word-boundary token, or full-sequence probabilities); that is a method change and is not made.

## Summary of the 240-pair exploratory runs
See `COMPETENCE_240_PAIRS.md`: under the official rule only Qwen2.5-1.5B is evaluable (W 0.613 [0.550, 0.671]). Qwen2.5-0.5B, OLMo-2-0425-1B, SmolLM2-1.7B and SmolLM2-360M are NOT EVALUABLE; TinyLlama is NOT MEASURED.
