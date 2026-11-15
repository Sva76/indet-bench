# p(UNKNOWN) on larger models (15 November 2026)

English version of the owner-approved report `results/larger_models_2026-11-15/Risultati_modelli_grandi_v1.md` (Italian, v1.1). Simona Vargiu approved it on 15 Nov 2026 at 13:45, on condition that every classification is honest and supported by the data. Numbers and wording follow the approved version; nothing was re-analysed.

**Status: EXPLORATORY**, like the 14 November results. They are not an independent validation of the method. "CONFIRMED" means only that the HU1/HI1 rule applied by the code is satisfied (W ≥ 0.60 and lower bound of the 95% interval > 0.5). The comparison with the smaller model of the same family is **descriptive**: no between-model test was pre-registered. Method, thresholds, prompts and the label-mass rule were fixed before the data.

## Run
- Notebook `notebooks/IndetBench_modelli_grandi_v4.ipynb` (N-notebook-4), mode *completo*, NVIDIA A100-SXM4-80GB, transformers 5.22.1, torch 2.14.1+cu130, bitsandbytes 0.50.2, repository at commit `2aa1f62` (scoring identical to `c086e65`).
- Two sessions. The first computed Qwen3-8B, Qwen3-32B, OLMo-2-32B and Gemma-2-27B; Llama-3.3-70B failed with HTTP 403 (gated access not yet granted). The second session skipped the four completed models and computed only Llama. The four models' `punteggi.csv` are byte-identical in the two archives.
- Per-row scores, reports and manifests: [`results/larger_models_2026-11-15/`](../results/larger_models_2026-11-15/) (SHA-256 in `SHA256SUMS`). `tests/test_larger_models_results.py` recomputes W, intervals, competence gate and verdict from the per-row scores with the repository code.

## Summary
- **Technical.** All five models ran on 800/800 pairs, with identical prompts across models and no length exclusions. Qwen3-8B reproduces Test U2 on all 1600 rows. The label-mass rule is passed by all (median ≥ 0.999). An independent recomputation from the raw scores matches the report.
- **Scale within a family (descriptive).** OLMo goes from 0.694 (7B) to 0.886 (32B), Gemma from 0.818 (9B) to 0.870 (27B), Llama from 0.746 (8B, bf16) to 0.908 (70B in 4-bit). Qwen stays at 0.975, already near the maximum with the 8B.
- **Compared with baselines (descriptive):** no general superiority. p(UNKNOWN) is above the best independent baseline in Qwen3-32B (+0.085) and Gemma-2-27B (+0.051), below it in OLMo-2-32B (−0.034) and Llama-3.3-70B (−0.080).
- **Pair structure.** Gemma's weakness on IMPLIES persists at larger size (0.61). Llama is also weaker on IMPLIES (0.78). The NOT variant is no longer always weaker than POS: in Qwen3-32B and Llama-70B it is the opposite.

## 1. Does it work technically?

| Check | Outcome |
|---|---|
| GPU and version | A100-SXM4-80GB for all models, N-notebook-4, same commit |
| CPU check of the 4 Test U2 W values | passed 4/4: 0.975, 0.7825, 0.69375, 0.74625, identical counts per gold label |
| Qwen3-8B positive control | 24 values with difference 8·10⁻¹⁷; on the full run **1600/1600 rows** equal to Test U2 (max difference 3·10⁻²¹), answers equal 1600/1600, W 0.975 = Test U2 |
| Revisions | verified for all: Qwen3-32B `9216db57`, OLMo-2-32B `b9602434`, Gemma-2-27B `aaf20e6b`, Llama-3.3-70B `6f6073b4` |
| Weights | bfloat16 for Qwen, OLMo, Gemma; **Llama in nf4 4-bit** (bitsandbytes 0.50.2, bfloat16 compute), recorded in the manifest |
| Rows and pairs | 1600 rows per model, row_id = frozen benchmark, 800 valid pairs for all |
| Pair identity | same fingerprints (data `ba7ab202…`, benchmark `906c01bf…`) for the 5 models; 800 common pairs |
| Length exclusions | 0 for all |
| Tokenizer | no model used `token_type_ids`; texts and tokenisation identical on 1600/1600 prompts |
| Label coverage (new rule, 24 rows) | median mass: Qwen3-8B 1.000, Qwen3-32B 1.000, OLMo 0.999, Gemma 1.000, Llama 1.000; most likely token among the labels in 100% of cases; no model NOT MEASURABLE |
| Mass on the full set | median ≥ 0.999 for all. Rows with mass < 0.90: 0 for four models, **6/1600 for Llama (0.375%)**, below the 5% caution level |
| ALTRO answers | 0 for four models, **2 for Llama** (see §4) |
| Independent recomputation (pandas, without the indetbench code) | W, accuracies and gate identical to the report for the 5 models; intervals within 0.003 (different bootstrap) |

## 2. Does it measure what we intend?

| Model | B acc. | gold NO | gold YES | UNKNOWN on B | UNKNOWN on C | W, no UNKNOWN answer | W AND | W OR | W IMPLIES | W POS | W NOT | W first | W last |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Qwen3-8B (control) | 1.000 | 1.000 | 1.000 | 0.0% | 25.3% | 0.964 | 0.963 | 0.996 | 0.966 | 0.995 | 0.955 | 0.955 | 0.995 |
| Qwen3-32B | 0.995 | 0.985 | 1.000 | 0.0% | 24.4% | 0.969 | 1.000 | 1.000 | 0.924 | 0.950 | **1.000** | 0.975 | 0.975 |
| OLMo-2-32B-Instruct | 0.990 | 1.000 | 0.985 | 0.8% | 19.4% | 0.872 | **0.795** | 0.981 | 0.883 | 0.913 | 0.860 | 0.828 | 0.945 |
| Gemma-2-27B-it | 0.929 | 1.000 | 0.893 | 7.1% | 55.1% | 0.797 | 1.000 | 1.000 | **0.606** | 0.913 | 0.828 | 0.795 | 0.945 |
| Llama-3.3-70B (4-bit) | 1.000 | 1.000 | 1.000 | 0.0% | 27.8% | 0.882 | 1.000 | 0.944 | **0.777** | 0.858 | **0.958** | 0.835 | 0.980 |

- **Competence gate (binding):** passed by all with a wide margin (minimum 0.893, Gemma on gold YES).
- **Not only the generated answer.** On pairs where neither B nor C was answered UNKNOWN, W stays 0.80–0.97.
- **Length:** W 0.5 by construction, no pair excluded.
- **Families (descriptive):** differences ≥ 0.20 in Gemma (IMPLIES 0.61, like the 9B with 0.59) and Llama (IMPLIES 0.78). In OLMo the weakest family is AND (0.80). As on 14 November, the weakest family changes from model to model.
- **NOT variant:** weaker than POS in Qwen3-8B, OLMo and Gemma; **stronger** in Qwen3-32B (+0.050) and Llama-70B (+0.100). The 14 November result "NOT < POS in 5 of 5 models" does not extend to the larger models.
- **Position (descriptive):** lower W when the indeterminate element is in the first position in OLMo, Gemma and Llama (−0.12 to −0.15); equal in Qwen3-32B. On 14 November the effect had no consistent sign.
- **Gemma-2-27B answers UNKNOWN much more often:** 55% on C (9B: 25%) but also 7.1% on B (9B: 1.8%). Gold YES drops to 0.893.

### 2.1 NOT variant: data for the open question (descriptive)

Difference W(NOT) − W(POS), paired by story (each story has 2 NOT and 2 POS pairs), 95% bootstrap interval over the 200 stories (2000 resamples, seed 20261108), recomputed from the raw scores of Test U2 and of the 14 and 15 November runs.

| Family | Small model: NOT − POS [95% CI] | Large model: NOT − POS [95% CI] |
|---|---|---|
| Qwen3 (same version) | 8B: −0.040 [−0.060, −0.020] | 32B: **+0.050 [+0.027, +0.080]** |
| Llama (3.1 → 3.3, 70B in 4-bit) | 3.1-8B: −0.118 [−0.178, −0.058] | 3.3-70B: **+0.100 [+0.058, +0.142]** |
| OLMo-2 (1124 → 0325) | 7B: −0.358 [−0.410, −0.302] | 32B: −0.052 [−0.100, −0.010] |
| Gemma-2 (same version) | 9B: −0.090 [−0.142, −0.040] | 27B: −0.085 [−0.128, −0.045] |
| small only | Mistral-Nemo 12B −0.405 [−0.465, −0.348]; Falcon3-7B −0.138 [−0.178, −0.102]; Phi-4 14B −0.092 [−0.130, −0.060] | — |

**What these data say.**
- The 14 November generalisation ("NOT weaker than POS in every model") **does not hold**: in Qwen3-32B and Llama-3.3-70B the difference is positive, with a 95% interval excluding 0. Owner's decision (15 Nov, 13:48): the rule is falsified and is no longer used.
- Within a family the sign reverses with intervals excluding 0 on opposite sides (Qwen 8B/32B, Llama 8B/70B), so the change of sign **is not explained by chance in resampling the 200 stories**. This says nothing about other stories or wordings.
- With size NOT − POS rises in three families out of four: in Qwen3 and Llama up to a change of sign, in OLMo-2 from −0.358 to −0.052. In Gemma-2 it stays almost the same (−0.090 and −0.085). In Qwen3-32B the positive sign comes in equal parts from NOT rising (0.955 → 1.000, +0.045) and POS dropping (0.995 → 0.950, −0.045). (Corrected on 15 Nov after review: the earlier version attributed the sign mostly to POS.)

**What they do not say.**
- They cannot distinguish a "step" (an abrupt change above some size) from a gradual change: there are **two points per family**, compatible with both.
- They cannot attribute the change to size. In Llama and OLMo the version and training data change too, and the large Llama is quantised. Only Qwen3 and Gemma-2 compare the same version, and they disagree.
- "More samples" can mean two things. More **pairs or stories**: the number of pairs is the same (800) at every size, and the intervals are already narrow enough to separate the signs. More **models**: this is what is missing to see the shape of the trend.

**Design that would be needed (dedicated test, to be pre-registered):** a series of sizes of the **same family and version**, e.g. Qwen3 0.6B, 1.7B, 4B, 8B, 14B and 32B (all Apache-2.0), to see whether the sign changes at one point (step) or gradually, plus a set of **new stories**, to check that the trend does not depend on the 200 frozen stories. The criterion (e.g. NOT − POS per size with 95% CI, and the expected shape of a step) must be fixed before the data.

## 3. Does it add over the baselines? (descriptive only)

Independent baselines from the same outputs: normalised entropy, minus normalised max probability, generated UNKNOWN answer (0/1). ΔW = W of p(UNKNOWN) − W of the best independent baseline, paired by story, 95% bootstrap interval, **descriptive**, not a pre-registered test.

| Model | W p(UNKNOWN) [95% CI] | entropy | minus max p | UNKNOWN answer | ΔW vs best [descriptive 95% CI] | W of the smaller model, same family |
|---|---|---|---|---|---|---|
| Qwen3-8B (control) | 0.975 [0.964, 0.985] | 0.949 | 0.948 | 0.626 | +0.026 [+0.013, +0.041] (entropy) | — |
| Qwen3-32B | 0.975 [0.961, 0.988] | 0.890 | 0.890 | 0.622 | **+0.085 [+0.063, +0.109]** (entropy) | Qwen3-8B 0.975 (Test U2) |
| OLMo-2-32B-Instruct | 0.886 [0.861, 0.910] | 0.920 | 0.919 | 0.593 | **−0.034 [−0.051, −0.018]** (entropy) | OLMo-2-1124-7B 0.694 (Test U2) |
| Gemma-2-27B-it | 0.870 [0.839, 0.900] | 0.819 | 0.816 | 0.740 | **+0.051 [+0.024, +0.079]** (entropy) | Gemma-2-9B 0.818 (14 Nov) |
| Llama-3.3-70B (4-bit) | 0.908 [0.889, 0.928] | 0.988 | 0.988 | 0.639 | **−0.080 [−0.100, −0.061]** (entropy) | Llama-3.1-8B 0.746 (Test U2, bf16) |

The "normalised p(UNKNOWN)" stays in the report for transparency (owner's decision of 14 November). With mass ≈ 1 it equals p(UNKNOWN) for all five: 0.975, 0.975, 0.886, 0.870, 0.908.

**Reading.** With scale, p(UNKNOWN) separates C from B better in three families out of four, but it does not become generally better than generic uncertainty measures. In the large models the sign of ΔW is split (two positive, two negative). These data do not show that p(UNKNOWN) carries information specific to indeterminacy beyond the generic uncertainty of the answer. With four models and one run each, it cannot be said what the sign of ΔW depends on.

**Llama-70B, where p(UNKNOWN) loses (descriptive, checked on the raw scores).** p(UNKNOWN) gives C ≤ B in 74 of 800 pairs. In all 74 the model answers NO to the C case with probability close to 1 (median p(UNKNOWN) 2·10⁻¹²). In 64 of these, "minus max probability" still wins because the model is slightly less certain on C (median 1 − max p 3·10⁻⁶) than on B (1·10⁻⁹). **Fact:** in these 74 pairs the little probability not given to the chosen answer goes to YES, not to UNKNOWN, and part of the baselines' advantage comes from very small probability differences in near-certain answers. **Not verified:** why this happens (model behaviour or 4-bit quantisation). We do not know whether these differences would be the same at full precision.

## 4. Anomalies and classification

The "Basis" column says whether the category is **supported by the data** (the evidence determines it) or **not classified** (several categories remain possible and the data do not allow a choice). Causes written as "hypothesis" were not verified.

| Model | Anomaly | Category | Basis | Cause | Evidence | Checks done | Still uncertain |
|---|---|---|---|---|---|---|---|
| Llama-70B | HTTP 403 in the first session | **technical problem** (access), resolved | supported by the data | gated licence not yet granted to the token's account (from the error message) | Hugging Face message; after access was granted the model ran | re-run; other models skipped, identical scores | — |
| Llama-70B | an independent baseline beats p(UNKNOWN) (minus max p 0.988 vs 0.908) | **scientific evidence** (descriptive): on this model p(UNKNOWN) is not the best measure | supported by the data (it is a measurement, not an interpretation) | hypothesis: model behaviour or 4-bit quantisation; not verified | ΔW −0.080 [−0.100, −0.061]; 74 pairs lost, all with C = NO near-certain | independent recomputation; analysis of the lost pairs (§3) | why it happens; full-precision result; not a pre-registered test |
| Llama-70B | W very different across families (AND 1.00, IMPLIES 0.78) | not classified: model behaviour or protocol limit | the data do not allow a choice | unknown | W per family | no exclusions; gate passed | whether it depends on the IMPLIES wording or on the model |
| Llama-70B | 2 ALTRO answers and 6 rows with mass < 0.90 (below the 5% caution level, not flagged automatically) | **model behaviour** | supported by the data for the technical part: prompt, tokenizer and revision checked without defects, and the generated text is readable ("MAYBE is not an option,") | why the model writes this text is unknown | all 6 rows are C cases, NOT variant, last position; the 2 ALTRO rows have mass 0.47 and 0.41 | W without the 6 pairs: 0.9075, unchanged | the reason for the generated text |
| OLMo-2-32B | an independent baseline beats p(UNKNOWN) (entropy 0.920 vs 0.886) | **scientific evidence** (descriptive) | supported by the data (it is a measurement) | unknown | ΔW −0.034 [−0.051, −0.018] | independent recomputation | not a pre-registered test |
| Gemma-2-27B | W very different across families (AND and OR 1.00, IMPLIES 0.61) | not classified: model behaviour or protocol limit | the data do not allow a choice | unknown; the same pattern is in the 9B (0.59) | W per family at two model sizes | no exclusions; gate passed | whether it depends on the IMPLIES wording ("in every case except one") or on the Gemma family |
| all | NOT variant inconsistent: weaker than POS in 3 models, stronger in 2 (not flagged automatically) | not classified: protocol limit or model behaviour | the data do not allow a choice | unknown | table in §2 | — | part of the open question on negation (decision of 14 Nov) |

## 5. What can and cannot be said

- **Can be said, as an exploratory result:** on the frozen prose benchmark (800 pairs), p(UNKNOWN) ranks C above B also in the larger models of four families (Qwen3-32B, OLMo-2-32B, Gemma-2-27B, Llama-3.3-70B in 4-bit). In the three families where the small model was not already at the maximum, the large model's W is higher. The positive control reproduces Test U2 exactly.
- **Cannot be said:**
  - that the method is independently validated;
  - that p(UNKNOWN) is better than the output baselines (in OLMo-32B and Llama-70B it is worse);
  - that the increase in W is an effect of size: small and large models also differ in version and training data (e.g. OLMo-2-1124 vs OLMo-2-0325, Llama-3.1 vs 3.3), and there is no between-model test;
  - anything about Llama-70B at full precision: the result is "70B quantised to 4-bit";
  - anything about reasoning models (part B, protocol in [`docs/REASONING_PART_B_PROTOCOL.md`](REASONING_PART_B_PROTOCOL.md), not yet run).
- **General uncertainties:** one run per model; one format and one set of stories; dependence on family, variant and position.

## 6. Owner's decisions
1. **Approval** (15 Nov, 13:45), on condition that classifications are honest and supported by the data; v1.1 applies the condition (§3, §4).
2. **NOT variant** (15 Nov, 13:48): the rule "NOT weaker than POS" is falsified by the larger models and is no longer used. Still open: whether more samples are needed or whether the NOT effect changes with scale, like a step. The current data cannot distinguish the two; the design that would be needed is in §2.1.
3. **Part B (reasoning models)** (15 Nov, 14:11): protocol approved with the 5 recommended choices; notebook `notebooks/IndetBench_reasoning_v1.ipynb` (R-notebook-1).
