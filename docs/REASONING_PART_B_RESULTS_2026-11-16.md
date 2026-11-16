# p(UNKNOWN) with reasoning switched on (part B, 16 November 2026)

English version of `results/reasoning_part_B_2026-11-16/Risultati_parteB_reasoning_v2.md` (Italian, v2). **Status of the report: draft, not yet approved by the owner.** Numbers and wording follow the Italian version; nothing was re-analysed for the translation.

**Status of the results: EXPLORATORY.** They are not an independent validation of the method. "CONFIRMED" means only that the HR1 rule applied by the code is satisfied (W ≥ 0.60 and lower bound of the 95% interval > 0.5). A higher W with reasoning does not show that the method works better, and a lower one would not refute it. Method, thresholds, prompts and the label-mass rule were fixed before the data ([part B protocol](REASONING_PART_B_PROTOCOL.md), with the measurement amendment of §8).

## Run
- Notebook `notebooks/IndetBench_reasoning_v2.ipynb` (R-notebook-2), mode *completo*, **NVIDIA A100-SXM4-40GB**, transformers 5.22.1, torch 2.14.1+cu130, repository at commit `2aa1f62`.
- Reasoning is sampled with the authors' parameters (budget 4096 tokens) at batch with sdpa attention. p(UNKNOWN) is measured at the first answer token after `</think>`, row by row at batch 1 with eager attention.
- Phi-4-reasoning stopped at 1152 of 1600 rows with a CUDA out-of-memory error. It was resumed with `notebooks/IndetBench_reasoning_v2_1.ipynb`, which changes only memory handling ([notes §7](../notebooks/Note_reasoning_v2.md)). The resume reused the saved blocks: the 1152 rows already measured are identical in the final result (difference 0, answers 1152/1152), the manifest is identical, and no measurement was repeated because of memory.
- Per-row scores, reasoning texts, repeatability runs, reports and manifests: [`results/reasoning_part_B_2026-11-16/`](../results/reasoning_part_B_2026-11-16/) (SHA-256 in `SHA256SUMS`). `tests/test_reasoning_part_b_results.py` recomputes W, intervals, competence gate and verdict from the per-row scores with the repository code.
- **Not run:** Qwen3-32B. In bfloat16 it needs the A100-SXM4-80GB, which Colab did not assign. The secondary HR2 has no data.

## Summary
- **Technical.** Qwen3-8B, Phi-4-reasoning and R1-Distill-Llama-8B ran on 800/800 pairs with no length exclusions. All reasoning traces closed by themselves within the budget, except 4 of 1600 for Phi-4. The pipeline check passed (difference 8·10⁻¹⁷, 24/24). Qwen3-8B without reasoning reproduces Test U2 on **1600/1600 rows**. An independent recomputation of W from the per-row scores matches the report.
- **Qwen3-8B (main).** With reasoning W = **1.000** [1.000, 1.000]; without reasoning 0.975. HR2: ΔW = **+0.025** [0.015, 0.036]. The interval excludes 0, so by the rule "reasoning changes W". This is also the largest increase possible from 0.975 (a limit declared before the data).
- **Where the signal comes from in Qwen3-8B with reasoning.** After reasoning, Qwen answers UNKNOWN on 795 of 800 C cases and on 0 of 800 B cases. The generated answer alone (UNKNOWN yes/no) already gives W 0.997. With reasoning the signal is in the explicit answer, and p(UNKNOWN) adds nothing measurable beyond the answer: a ceiling effect.
- **Phi-4-reasoning (descriptive).** W = **0.995** [0.990, 0.999], CONFIRMED. Like Qwen, after reasoning it answers UNKNOWN on 793 of 800 C cases and on no B case. The generated answer alone reaches 0.996, i.e. it **equals p(UNKNOWN)**. The small difference (0.0006) comes entirely from 7 C cases where the model starts with a disclaimer ("Disclaimer: …") instead of the label. Again a ceiling effect. Phi-4 without reasoning (14 November, different weights) had W 0.944.
- **R1-Distill-Llama-8B (descriptive).** W = **0.9225** [0.900, 0.944], CONFIRMED, above the best independent baseline (generated UNKNOWN 0/1, W 0.787). Two limits: the label mass is lower (median 0.837; 75.8% of rows below 0.9), and 89 of 1600 answers cannot be read as YES/NO/UNKNOWN. Individual answers also depend strongly on sampling: only 69–72% of answers agree across seeds, while W per seed stays stable (0.925–0.95).

## 1. Does it work technically?

| Check | Qwen3-8B | Phi-4-reasoning | R1-Distill-Llama-8B |
|---|---|---|---|
| GPU and version | A100-SXM4-40GB, R-notebook-2, commit `2aa1f62` | same (resumed with v2_1, same fingerprint) | same |
| Revision | verified (`b968826d`) | verified (`1de18ec9`) | verified (`6a6f4aa4`) |
| Pipeline check (§5.1) | passed: difference 8.3·10⁻¹⁷, answers 24/24 | (Qwen only) | (Qwen only) |
| Reasoning off vs Test U2 | **1600/1600** rows, max difference 1.1·10⁻¹⁶, answers equal 1600/1600 | not planned | not planned |
| CPU check of the 4 Test U2 W values | passed | passed (resume) | — |
| Tokenizer and prompts | 1600/1600 intact in both conditions | 1600/1600 intact (Microsoft system message of the template, declared) | 1600/1600 intact |
| Valid pairs, length exclusions | 800, 0 | 800, 0 | 800, 0 |
| Reasoning closure | 1600/1600 closed by themselves | 1596/1600 by themselves, **4 at the budget** (3 B, 1 C); closed pairs 796 ≥ 760, sensitivity on closed pairs only W 0.995 | 1600/1600 closed by themselves |
| Reasoning length (median B / C, max) | 251 / 303 tokens, max 3457 | 445 / 534.5 tokens, max 4096 | 303 / 354.5 tokens, max 2416 |
| Answer position after `</think>` | first non-blank token (1600/1600) | immediately, position 0 (1600/1600) | first non-blank token (1600/1600) |
| Mass YES+NO+UNKNOWN (median over all rows) | 1.000 | 1.000 (24 control rows 1.000) | **0.837** (24 control rows 0.855; rule ≥ 0.5 passed) |
| Rows with mass < 0.9 / < 0.5 | 0 / 0 | 27 (1.7%) / 14 | **75.8%** / 147 rows (9.2%) |
| OTHER (unreadable) answers | 0 | 14 (7 B, 7 C) | **89** (25 B, 64 C) |
| Time | on 4605 s, off 562 s | on 12 311 s (first session, 1152 rows) + 4709 s (resume) | on 3184 s |

**Independent recomputation.** W was recomputed from `punteggi.csv` with a script separate from the notebook (`ricalcolo_parteB.py` in the results folder): the mean over the 200 stories of the share of pairs with C score > B score (tie = 0.5). The estimates match the report: Qwen on 1.0000, off 0.9750; Phi-4-reasoning 0.9950; R1 0.9225. The 95% intervals differ in the third decimal (R1: 0.901–0.944 vs 0.900–0.944) because the two bootstraps use different random generators.

## 2. Does it measure what we intend?

### Qwen3-8B

| | off | on |
|---|---|---|
| W (95% CI) | 0.975 [0.964, 0.985] | 1.000 [1.000, 1.000] |
| Accuracy on B (NO / YES) | 1.000 (1.000 / 1.000) | 1.000 (1.000 / 1.000) |
| W by family (AND / IMPLIES / OR) | 0.963 / 0.966 / 0.996 | 1.000 / 1.000 / 1.000 |
| W by variant (NOT / POS) | 0.955 / 0.995 | 1.000 / 1.000 |
| W by position (first / last) | 0.955 / 0.995 | 1.000 / 1.000 |
| W with C not answered UNKNOWN | 0.964 (598 pairs) | 1.000 (**5 pairs**, 4 stories) |

From off to on: on B nothing changes (800/800 stay correct: 268 NO, 532 YES). On C, 593 answers become UNKNOWN (466 from YES, 127 from NO), the 202 already UNKNOWN stay so, and only 5 stay YES.

**Reading.** Reasoning leads Qwen to declare indeterminacy almost always, and only on C. W = 1.000 is what one expects when the answer itself separates C and B. The check on the pairs where C is not answered UNKNOWN has only 5 pairs: **not evaluable**. So with reasoning on one cannot say whether p(UNKNOWN) carries information beyond the answer.

### Phi-4-reasoning

| | on |
|---|---|
| W (95% CI) | 0.995 [0.990, 0.999] |
| Accuracy on B (NO / YES) | 0.991 (0.993 / 0.991), competence gate passed |
| W by family (AND / IMPLIES / OR) | 0.996 / 0.992 / 0.996 |
| W by variant (NOT / POS) | 0.995 / 0.995 |
| W by position (first / last) | 1.000 / 0.990 |
| Answers on C | 793 UNKNOWN, 7 OTHER, 0 YES, 0 NO |
| Answers on B | 0 UNKNOWN, 527 YES, 266 NO, 7 OTHER |
| W with C not answered UNKNOWN | 0.43 (**7 pairs**, 7 stories) |

**Reading.** Same picture as Qwen3-8B with reasoning: the explicit answer separates C and B almost perfectly; the check on the pairs where C is not answered UNKNOWN (7 pairs) is **not evaluable**. The 4 pairs of 800 where C does not rank above B all have the C answer in OTHER (a disclaimer instead of the label, mass near 0). Compared with Phi-4 without reasoning (14 November: W 0.944, IMPLIES 0.83), W rises and the IMPLIES weakness disappears. This is descriptive only: the weights differ (Phi-4-reasoning is Phi-4 with further training), so it does not measure the effect of reasoning at fixed weights.

### R1-Distill-Llama-8B

| | on |
|---|---|
| W (95% CI) | 0.9225 [0.900, 0.944] |
| Accuracy on B (NO / YES) | 0.955 (0.907 / 0.979), competence gate passed |
| W by family (AND / IMPLIES / OR) | **0.847** / 0.932 / 0.989 |
| W by variant (NOT / POS) | 0.9075 / 0.9375 |
| W by position (first / last) | 0.9175 / 0.9275 |
| Answers on C | 468 UNKNOWN, 109 YES, 159 NO, 64 OTHER |
| Answers on B | 9 UNKNOWN, 521 YES, 245 NO, 25 OTHER |
| W with C not answered UNKNOWN | 0.844 [0.800, 0.887] (332 pairs, 172 stories) |
| W with neither answer UNKNOWN | 0.854 [0.810, 0.897] (327 pairs) |

**Reading.** R1 answers UNKNOWN on 468 of 800 C cases (59%) and on 9 B cases, so the C/B separation is not all in the answer. The check on the pairs where C is not answered UNKNOWN is evaluable here (332 pairs; the B answer and the C answer need not be the same, e.g. C may be OTHER): even then p(UNKNOWN) is higher on C than on B in 84% of comparisons. The values involved are small, though: on YES answers the median p(UNKNOWN) is 3.8·10⁻⁵ on C vs 1.9·10⁻⁶ on B; on NO answers 1.2·10⁻⁴ vs 4.3·10⁻⁵. It is an ordering among very low probabilities, and these data do not establish whether it has practical meaning. AND is the weakest family (0.847), descriptively.

## 3. Does it add over the baselines? (descriptive)

| Baseline from the same outputs | Qwen3-8B off | Qwen3-8B on | Phi-4-reasoning | R1 on |
|---|---|---|---|---|
| **p(UNKNOWN)** | **0.975** | **1.000** | **0.995** | **0.9225** |
| generated answer UNKNOWN (0/1) | 0.626 | 0.997 | **0.996** | 0.787 |
| normalised entropy | 0.949 | 0.990 | 0.029 | 0.694 |
| minus normalised max probability | 0.9475 | 0.990 | 0.029 | 0.694 |
| reasoning length in tokens | — | 0.696 | 0.609 | 0.660 |
| reasoning truncated (0/1) | — | 0.5 | 0.499 | 0.5 |
| prompt length | 0.5 | 0.5 | 0.5 | 0.5 |
| normalised p(UNKNOWN) (not independent) | 0.975 | 1.000 | 1.000 | 0.916 |

- Qwen3-8B on: the generated answer alone reaches 0.997; the gap (+0.003) is inside the ceiling, with no room to show an advantage.
- Phi-4-reasoning: the generated answer **equals** p(UNKNOWN) (0.996 vs 0.995), flagged by the code as an anomaly (A4). The 0.0006 gap is half a pair out of 800 and comes from the 7 C answers in OTHER: Phi-4 never answers UNKNOWN on B, so on those 7 pairs the 0/1 answer scores 0 on both sides and ties (0.5) in all of them. p(UNKNOWN) instead loses 4 of them and wins 3. Net: (4 − 3) × 0.5 / 800 = 0.000625 in favour of the answer. Normalised p(UNKNOWN), which removes the mass effect, reaches 1.000.
- Phi-4-reasoning: entropy and minus max probability are **reversed** (0.029): the model is more confident on C (UNKNOWN with probability ≈ 1) than on B. The same phenomenon was seen for Mistral in Test M; generic uncertainty here points opposite to indeterminacy.
- R1: p(UNKNOWN) is above the best independent baseline by +0.136 (vs generated UNKNOWN 0/1).
- Reasoning length separates C and B a little in all models (0.61–0.70): reasoning is longer on C. It stays well below p(UNKNOWN).
- No superiority test was pre-registered for new models.

## 4. Repeatability and anomalies

### Repeatability (first 20 stories, 160 rows, two extra seeds)

| | Qwen3-8B on | Phi-4-reasoning | R1 |
|---|---|---|---|
| W per seed (20261108 / 09 / 10) | 1.000 / 1.000 / 1.000 | 1.000 / 1.000 / 0.9875 | 0.925 / 0.95 / 0.95 |
| Answers equal to the main seed | 158/160 and 157/160 | 160/160 and 158/160 | **111/160 and 115/160** |
| Where answers change | — | — | 44 and 40 on C, 5 and 5 on B |

R1's aggregate W is stable across seeds, but about one answer in three changes with the sampled reasoning, almost only on C and in all directions. The measure is conditional on the sampled reasoning (protocol §2): for R1 this dependence is strong for single stories and weak for W.

### Anomalies (classified in the four categories)

**A1. R1: 89 unreadable answers (25 B, 64 C).** Category: **model behaviour (answer format)**, supported by the data. All 89 start with "The" and are an explanatory sentence instead of a label. Technical checks passed (template and labels checked, prompts intact 1600/1600, revision verified, answer at the first token after `</think>` in 1600/1600 rows), and the same pipeline gives mass 1.000 for Qwen3-8B. Whether a prompt adapted to R1 would produce labels was not tried, by design (frozen, identical prompts): a declared **protocol limit**. Sensitivity (descriptive, not pre-registered): without pairs with an OTHER answer, W = 0.926 (713 pairs, 199 stories).

**A2. R1: low label mass at the first token** (median 0.837; 75.8% of rows below 0.9; 147 rows below 0.5). Category: **model behaviour (answer format)**, supported for the OTHER rows (median mass 0.33), plausible but not shown for the others (median 0.848 without OTHER). The notebook does not store which tokens take the missing mass. The technical rule (median ≥ 0.5) is passed. Pairs where both rows have mass ≥ 0.9 are 54 (W 1.000): a selection of cases with a clean label, **not interpretable** as an estimate of W.

**A3. Phi-4-reasoning: 14 unreadable answers (7 B, 7 C).** Category: **model behaviour (answer format)**, supported by the data. All 14 start with a disclaimer ("Disclaimer: This response is provided for informational purposes only…") instead of the label; label mass in these rows is between 0 and 0.42. In the other 1586 rows the label comes right after `</think>`. That the disclaimer depends on the template's Microsoft system message is possible but not shown. These are the 4 pairs of 800 where p(UNKNOWN) does not rank C above B.

**A4. Phi-4-reasoning: an independent baseline equals p(UNKNOWN)** (generated UNKNOWN 0/1: 0.996 vs 0.995). Classification: **scientific evidence, descriptive**, supported by the data. With reasoning on, in Phi-4-reasoning as in Qwen3-8B, the indeterminacy signal is in the explicit answer; p(UNKNOWN) at the first answer token reproduces the answer and adds no measurable information. Not a technical problem: the 0.0006 gap is explained pair by pair by the 7 OTHER answers on C. Limit: with a ceiling at 0.995–0.996 no measure can show an advantage; the data say that p(UNKNOWN) **does not add** here, not that it is worse.

**Qwen3-8B: no anomaly flagged by the code.** W = 1.000 is a ceiling effect of the explicit answer, foreseen as a limit before the data.

## 5. Phi-4-reasoning: memory error and resume

At 1152 of 1600 rows the GPU ran out of memory ("Tried to allocate 2.92 GiB … 32.15 GiB allocated by PyTorch, 4.49 GiB reserved but unallocated"). 2.92 GiB is the float32 eager attention matrix of a row of about 4400 tokens (40 heads) in the batch-1 measurement. It was not a capacity limit: the 3 rows that reached the budget, up to 4418 tokens, had already been measured without error. Category: **technical problem (memory management)**, supported by the data: memory from the batch-8 generation stayed reserved and fragmented when the eager measurement started.

Fix in `IndetBench_reasoning_v2_1.ipynb`, memory only, no computation changed: `expandable_segments` allocator set in cell 1 before torch is imported; generation outputs and the CUDA cache freed before measurement; after an OOM the same measurement is repeated once and recorded in `esito.json` (`memoria_cuda`). VERSION and manifest are unchanged, so the resume reused the 36 saved blocks. In a dry run with simulated OOM errors `punteggi.csv` was byte-identical to v2. In the real resume no measurement was repeated.

## 6. Conclusions (exploratory)

1. **Works technically:** yes, for Qwen3-8B, Phi-4-reasoning and R1. The pipeline reproduces Test U2 exactly; reasoning closes by itself except for 4 of 1600 Phi-4 rows (796 closed pairs, above the 760 threshold). The resume of Phi-4 changed no value.
2. **Measures what we intend:** with reasoning the C/B separation stays high in all three models. In Qwen3-8B and Phi-4-reasoning it moves almost entirely into the explicit answer, so the contribution of p(UNKNOWN) cannot be separated from that of the answer. In R1 part of the separation remains on the pairs where C is not answered UNKNOWN, but on very small probabilities.
3. **Adds over baselines:** not in Qwen3-8B on or Phi-4-reasoning (generated answer 0.997 and 0.996, at the level of p(UNKNOWN)); in Phi-4-reasoning the generic uncertainty baselines are reversed. In R1 yes, descriptively (+0.136 over the generated answer), with the mass, format and repeatability limits of §4.
4. HR2 (Qwen3-8B): reasoning changes W (+0.025, 95% CI excludes 0). The increase equals the maximum possible, so the data do not say how much reasoning would help without a ceiling.
5. Overall reading (exploratory): in the two models that, after reasoning, almost always declare indeterminacy, p(UNKNOWN) coincides with the answer. Only in R1, which answers UNKNOWN on 59% of C cases, does some separation remain beyond the answer, on very small probabilities and with low repeatability. Qwen3-32B is still to be run (needs the 80 GB A100); without it the secondary HR2 has no data.
