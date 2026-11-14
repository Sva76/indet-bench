# p(UNKNOWN) on models from new families (14 November 2026)

English version of the owner-approved report `results/new_models_2026-11-14/Risultati_modelli_nuovi_v1.md` (Italian, v1, approved by Simona Vargiu on 14 Nov 2026, 18:56). Numbers and wording follow the approved version; nothing was re-analysed.

**Status: EXPLORATORY.** These results are not an independent validation of the method. "CONFIRMED" below means only that the HU1/HI1 rule applied by the code is satisfied (W ≥ 0.60 and lower bound of the 95% interval > 0.5). Method, thresholds and prompts were fixed before the data and were not changed afterwards.

## Run
- Notebook `notebooks/IndetBench_modelli_nuovi_v3.ipynb` (N-notebook-3), mode *completo*, NVIDIA A100-SXM4-40GB, bfloat16, eager attention, transformers 5.22.1, torch 2.14.1+cu130, repository at commit `c086e65`.
- Frozen original benchmark, set PN (prose without the explanatory sentence): 800 B/C pairs, 200 stories, 1600 rows per model. Data fingerprint `ba7ab202…`, benchmark `906c01bf…`, identical for all five models.
- Models (revisions pinned before the data): Qwen3-8B (positive control), Gemma-2-9B-it, Yi-1.5-9B-Chat, Falcon3-7B-Instruct, Phi-4 (14B).
- Per-row scores, reports and manifests: [`results/new_models_2026-11-14/`](../results/new_models_2026-11-14/) (SHA-256 in `SHA256SUMS`). `tests/test_new_models_results.py` recomputes W, intervals, competence gate and verdict from the per-row scores with the repository code and checks them against the archived reports.

## Summary
- **Technical.** All five models ran on 800/800 pairs, with identical prompts across models and no pair excluded for length. Qwen3-8B reproduces Test U2 on all 1600 rows. An independent recomputation from the raw scores (pandas, without the indetbench code) matches the report.
- **Yi-1.5-9B-Chat: NOT EVALUABLE for a technical reason (owner's decision, 14 Nov, 18:51)**, although the code returns CONFIRMED (W 0.86). At the first token the total probability of YES/NO/UNKNOWN is about 2·10⁻⁶ (median), while the generated answers are correct labels 99% of the time. The measured p(UNKNOWN) is therefore not the quantity defined by the protocol. The value stays archived but is not part of the results.
- **Gemma-2-9B-it, Falcon3-7B-Instruct and Phi-4** pass the competence gate and satisfy the rule: W 0.818 [0.788, 0.848], 0.931 [0.911, 0.950] and 0.944 [0.924, 0.963]. This is exploratory support for p(UNKNOWN) ranking C above B in prose in three new model families.
- **Compared with generic baselines (descriptive):** p(UNKNOWN) does **not** add in a general way over generic uncertainty measures from the same outputs. Falcon is slightly above entropy (+0.031), Phi-4 equals "minus max probability", Gemma is below entropy (−0.074). It cannot be said that p(UNKNOWN) is better than these baselines.
- **Dependence on pair structure:** strong in some models. Gemma has W 0.59 on IMPLIES and 1.00 on AND. The NOT variant has a lower W than POS in every model.

## 1. Does it work technically?

| Check | Outcome |
|---|---|
| Mode and version | `completo`, N-notebook-3, same commit and same GPU for all 5 models |
| CPU check of the 4 Test U2 W values | passed 4/4: 0.975, 0.7825, 0.69375, 0.74625, identical counts per gold label |
| Qwen3-8B positive control | 24 values with difference 8·10⁻¹⁷; on the full run **1600/1600 rows** equal to Test U2 (max difference 3·10⁻²¹), answers equal 1600/1600, W 0.975 = Test U2 |
| Rows and pairs | 1600 rows per model, no duplicates, row_id = frozen benchmark, 800 valid pairs for all |
| Excluded for length | 0 for all models: B and C have the same number of tokens in every pair |
| Tokenizer | no model used `token_type_ids`; texts and tokenisation identical on 1600/1600 prompts |
| ALTRO (unparsable) answers | 0 for all |
| YES+NO+UNKNOWN mass at the first token (median) | Qwen 1.00, Gemma 1.00, Falcon 1.00, Phi-4 0.99 (2.9% of rows < 0.90, under the 5% caution level), **Yi ≈ 2·10⁻⁶ (100% of rows < 0.90)** |
| Independent recomputation | W, accuracies and gate identical to the report for the 5 models; intervals within 0.003 (different bootstrap) |

### Yi-1.5-9B-Chat: technical anomaly
- **Facts.** The label mass at the first token has median 2.2·10⁻⁶ and maximum 2.0·10⁻⁵, yet the generated answers are readable labels (0 ALTRO) and correct on B in 99.1% of cases. The first generated token is therefore not among the tokens used to measure p(YES), p(NO), p(UNKNOWN). Also, there are 3 label IDs per label instead of 6: the variants with and without a leading space map to the same first token.
- **Hypothesised cause (not verified).** Yi's SentencePiece tokenizer adds the leading space when encoding the isolated word, so "YES" and " YES" both give "▁YES". After `<|im_start|>assistant\n` the model generates the form without a leading space, which is not among the 6 variants. The variants are the Test U2 rule; for the four original models they covered the generated token (mass ≈ 1).
- **Consequence.** Yi's W 0.86 is computed on residual probabilities of tokens the model does not use to answer; it does not measure what the protocol intends.
- **Classification:** technical problem (label tokenisation), revealed by a protocol limit: low mass is only a "caution" flag and does not block the verdict.
- **Open diagnostic checks** (results unchanged): print Yi's `label_ids` tokens and the first generated token on about ten rows; check which token corresponds to "YES" after the assistant prefix. Any correction would be a method variant decided after the data, to be documented and run separately, not to replace this result.

## 2. Does it measure what we mean?

| Model | B acc. | gold NO | gold YES | UNKNOWN on B | UNKNOWN on C | W, no UNKNOWN answer | W AND | W OR | W IMPLIES | W POS | W NOT |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Qwen3-8B (control) | 1.000 | 1.000 | 1.000 | 0.0% | 25.3% | 0.964 | 0.963 | 0.996 | 0.966 | 0.995 | 0.955 |
| Gemma-2-9B-it | 0.945 | 1.000 | 0.917 | 1.8% | 24.9% | 0.807 | 1.000 | 0.858 | **0.591** | 0.863 | 0.773 |
| Falcon3-7B-Instruct | 0.961 | 1.000 | 0.942 | 1.1% | 28.0% | 0.913 | 0.993 | **0.806** | 0.996 | 1.000 | 0.863 |
| Phi-4 | 0.994 | 1.000 | 0.991 | 0.5% | 34.8% | 0.933 | 1.000 | 1.000 | 0.830 | 0.990 | 0.898 |
| Yi-1.5-9B-Chat (see §1) | 0.991 | 0.978 | 0.998 | 0.0% | 12.6% | 0.829 | 0.828 | 0.840 | 0.913 | 0.958 | 0.763 |

- **Competence gate (binding):** passed by all, with a wide margin (lowest 0.917, Gemma on gold YES).
- **Not only the generated answer.** Restricted to pairs where neither B nor C was answered UNKNOWN, W stays high (0.81–0.96).
- **Length:** W 0.5 by construction (B and C always have the same length).
- **Families (descriptive):** differences ≥ 0.20 in Gemma (IMPLIES 0.59); smaller in Falcon (OR 0.81) and Phi-4 (IMPLIES 0.83). The weakest family changes from model to model.
- **NOT variant:** lower W than POS in all 5 models (−0.04 to −0.20). **Owner's decision (14 Nov, 18:52):** recorded as an **open question arising from the data**, to be studied with a dedicated test whose protocol is fixed in advance. It changes no result here. Question to settle: does the effect come from the negation in the rule (pair wording, a protocol limit) or from how models process negation (model behaviour)?

## 3. Does it add over the baselines? (descriptive only)
Independent baselines from the same outputs: normalised entropy, minus normalised max probability, generated answer UNKNOWN (0/1). ΔW = W of p(UNKNOWN) − W of the best independent baseline, paired by story, 95% bootstrap interval, **descriptive**: no preregistered superiority test.

| Model | W p(UNKNOWN) | entropy | minus p max | answer UNKNOWN | ΔW vs best [95% CI, descriptive] |
|---|---|---|---|---|---|
| Qwen3-8B (control) | 0.975 | 0.949 | 0.948 | 0.626 | +0.026 [+0.013, +0.041] (entropy) |
| Gemma-2-9B-it | 0.818 | 0.891 | 0.891 | 0.616 | **−0.074 [−0.099, −0.050]** (entropy) |
| Falcon3-7B-Instruct | 0.931 | 0.900 | 0.893 | 0.634 | +0.031 [+0.006, +0.056] (entropy) |
| Phi-4 | 0.944 | 0.939 | 0.944 | 0.671 | 0.000 [−0.018, +0.018] (minus p max) |
| Yi-1.5-9B-Chat (see §1) | 0.860 | 0.850 | 0.849 | 0.563 | not interpretable |

"Normalised p(UNKNOWN)" stays in the archived report for transparency (owner's decision). With mass ≈ 1 it equals p(UNKNOWN); on Yi it differs (0.835 vs 0.860) because the mass is not ≈ 1.

**Reading.** In the three evaluable new models p(UNKNOWN) separates C from B, but generic uncertainty on the same outputs does almost as well (Falcon, Phi-4) or better (Gemma). These data do not show that p(UNKNOWN) carries information specific to indeterminacy beyond generic answer uncertainty.

## 4. What can and cannot be said
- **Can be said, as an exploratory result:** on the frozen prose benchmark (800 pairs), p(UNKNOWN) ranks C above B also in Gemma-2-9B-it, Falcon3-7B-Instruct and Phi-4, three families different from the four original ones. The Qwen3-8B positive control reproduces Test U2 exactly, so the environment introduces no differences.
- **Cannot be said:** that the method is independently validated; that p(UNKNOWN) is better than output baselines (in Gemma it is worse); that the result holds outside the prose format or for hallucinations with context; anything about Yi (NOT EVALUABLE, technical reason).
- **General uncertainties:** one run per model; one format and one set of stories; dependence on family and variant; Colab package versions differ from the original ones (no effect on Qwen, which matches).
