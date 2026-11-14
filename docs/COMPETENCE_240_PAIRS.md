# Competence condition on the 240-pair corpus (decided 2026-11-14)

Corpus: `data/smol_stat_v01_frozen.jsonl`, 240 B/C pairs (B gold: 120 YES, 120 NO), exploratory, no independent human validation.

## Rules
- **Official, binding.** B accuracy (generated answer) ≥ 0.50 overall **and** separately on gold YES and gold NO cases: the same rule fixed for the 800 original pairs. Below it the model is **NOT EVALUABLE**, whatever W is.
- **Theoretical sensitivity, not a verdict.** Chance level 1/3: the expected accuracy of a uniform random choice among the three allowed answers (YES, NO, UNKNOWN), required strictly overall and on each gold label. It is the lowest threshold that still excludes random answering; the per-label part excludes constant answering (a model that always says YES scores 1 on YES and 0 on NO). Any threshold below 1/3 would accept a model doing worse than chance, so none is considered.

History, stated plainly: the owner asked for this after seeing that SmolLM2-1.7B and OLMo-1B fail at 0.50. Because the theoretical threshold was considered after the data, it can never change a verdict. It only reports what a lower threshold would give.

## Results
W, AUROC and accuracies come from the unchanged analyzer (`tests/integration/analyze_crossmodel_stat.py`); the verdict comes from `tests/integration/competence_gate_240.py`. p = one-sided exact binomial probability of an accuracy at least this high under chance (1/3), descriptive.

| Model | B acc. overall | gold YES | gold NO | Official (≥ 0.50) | Theoretical (> 1/3) | W [95% CI] |
|---|---|---|---|---|---|---|
| Qwen2.5-1.5B | 0.679 | 0.750 | 0.608 | **EVALUABLE (exploratory)** | would pass | 0.613 [0.550, 0.671] |
| Qwen2.5-0.5B | 0.625 | 0.383 (p = 0.14) | 0.867 | NOT EVALUABLE (YES) | would pass | 0.592 [0.529, 0.654] |
| SmolLM2-360M | 0.383 | 0.767 | 0.000 | NOT EVALUABLE (overall, NO) | would fail (NO) | 0.479 (documented study) |
| OLMo-2-0425-1B | 0.238 | 0.350 | 0.125 | NOT EVALUABLE (all three) | **would fail** (overall, NO) | 0.579 [0.517, 0.642] |
| SmolLM2-1.7B | 0.021 | 0.042 | 0.000 | NOT EVALUABLE (all three) | **would fail** (all three) | 0.579 [0.517, 0.642] |

SmolLM2-360M: 92/240 correct and never answers NO (`docs/SMOLLM2_STAT_STUDY_RESULTS.md`), so every correct answer is on a gold YES case: 92/120 YES, 0/120 NO.

## Reading
- Under the official rule only **Qwen2.5-1.5B** is evaluable. Its W is above 0.5 with a CI excluding 0.5, an exploratory result on an unvalidated corpus.
- Even under the theoretical chance threshold, **SmolLM2-1.7B and OLMo-1B remain NOT EVALUABLE**: SmolLM2-1.7B answers UNKNOWN to 235 of 240 determined cases, OLMo-1B to 169, and both are below chance on gold NO. Their W of 0.579 cannot be read as detecting indeterminacy, because the models do not answer the determined cases.
- Qwen2.5-0.5B would pass only theoretically. Its YES accuracy (46/120) is not distinguishable from chance (p = 0.14).
