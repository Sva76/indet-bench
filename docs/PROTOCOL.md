# IndetBench evaluation protocol

This page is the single normative description of how IndetBench computes and reads its results. Each rule names the code or report it comes from. When this page and the code disagree, the code is what ran, and the disagreement is a bug to report.

Version: 15 November 2026 (commit that adds this file). Rules marked *original* come from the preregistered protocols of Tests U, U2, M and C (`research_originals/step2/protocols/`). Rules marked *new models* were fixed by the owner on 14 November 2026, before any new-model data.

## 1. Data

- **Primary set:** `PN` of the frozen file `M_Original_4800_righe.json.gz`: prose without the explanatory sentence ("P−S" in the reports), 800 B/C pairs, 200 stories, families AND, OR, IMPLIES, variants POS/NOT, two positions of the uncertain line. The file ships inside the package (`indetbench/data/`) and is byte-identical to the archived original in `research_originals/step2/frozen/`. `load_frozen` refuses any file whose SHA-256 is not `906c01bf…6d459`. *Original.*
- **B and C:** minimal pairs from the same story. In both, one variable is stated with two possible values ("It may be true or false that …"). In B the answer is the same for both values (determined, gold YES or NO); in C the two values give opposite answers (gold UNKNOWN). B and C differ in one other fact only. *Original.*
- **Gold labels** are derived from the formal rule and the truth values, not from human annotation. A human review of the wording has not been documented yet (see §8).
- **Other sets:** `SN` (symbolic) is descriptive only. The 240-pair set `data/smol_stat_v01_frozen.jsonl` is a separate, exploratory set made on 13 November 2026 and not yet human-reviewed.

## 2. Reference score p(UNKNOWN)

- Prompt: the frozen prompt, wrapped in the model's chat template (`hf_runner`). For Qwen3, thinking is off (`--model-key qwen`). *Original.*
- Score: probability of UNKNOWN at the **first generated token**, summed over the first tokens of six spelling and spacing variants (`UNKNOWN`, `Unknown`, `unknown`, with and without a leading space), **not renormalised**. The same is computed for YES and NO; `mass_total` is the sum of the three. *Original.*
- Generated answer: greedy decoding, 8 new tokens, parsed into YES, NO, UNKNOWN or ALTRO (other). *Original.*
- Numerics: the original runs used bf16 weights, eager attention and batch 1 (Test U2 protocol). `hf_runner` uses the model's default dtype and attention on GPU and float32 on CPU, so a rerun gives close, not identical, values. In the reasoning-model diagnostics (24 control rows), sdpa attention and batch padding each changed p(UNKNOWN) against batch 1 eager (largest differences 0.060 with sdpa at batch 1, 0.117 with eager at batch 16); measurements there are therefore taken at batch 1 eager ([part B protocol](REASONING_PART_B_PROTOCOL.md)).
- **Requires token probabilities.** p(UNKNOWN) can be computed only when the first-token distribution, or at least the probabilities of the label tokens, is available. It is not defined for:
  - models whose tokenizer gives YES, NO and UNKNOWN a shared first token (`hf_runner` stops; TinyLlama). Report *not measurable*, not a negative result. *New models.*
  - APIs that do not return log-probabilities. As checked on 15 November 2026, the Anthropic Messages API has no such parameter, Gemini 3.x models do not return them, and OpenAI reasoning models do not support them. Where an API returns only the top 5–20 alternatives, a missing label gives only an upper bound. These cases are outside the reference measurement.

## 3. Other methods

The benchmark is not limited to p(UNKNOWN). Any method that gives a score per prompt, higher = more indeterminate, can be evaluated on the same pairs: `indet-bench --scores my_scores.csv` reads `pair_id,block_id,side,score` and `--reference` gives the paired difference from p(UNKNOWN). This includes black-box methods (verbalised confidence, agreement between samples, the generated answer). Results from methods that need different access, such as black-box methods on closed models, are reported **in a separate table** and are not ranked against p(UNKNOWN) measured on other models.

## 4. The metric W

- For each pair: 1 if score(C) > score(B), 0.5 if equal, 0 otherwise. *Original.*
- W = mean of the pair values **within each story**, then mean over stories (each story weighs the same). *Original.* Code: `indetbench.metrics.w_score`.
- 95% interval: percentile bootstrap over **stories**, 2000 resamples, seed 20261108. *Original.*
- Paired difference ΔW between a method and the reference: computed on the pairs common to both, with the same stories resampled jointly; `headroom` = 1 − W(reference) is the largest ΔW that can be observed. *Original* (HM2/HC2). Code: `compare_to_reference`.
- **Two bootstrap implementations.** The original notebooks and `python -m indetbench.replay` use the numpy bootstrap of the reports. `report` and the generic CLI use the pure-Python bootstrap of `indetbench.metrics`. Point estimates are identical; intervals agree to about ±0.004 on the archived scores. Only the replayer reproduces the published intervals exactly.

## 5. Decision rules (set PN)

Applied by `indet-bench-original report` (`python -m indetbench.original_benchmark report`), in this order:

1. **Input checks** (added 15 November 2026). The score file is refused if a `row_id` is not a B or C row of the frozen benchmark, appears twice, or has `pair_id`, `block_id` or `side` different from the frozen row; if it mixes subsets; or if it mixes models (`model_id` and `model_revision`, when those columns are present; `hf_runner` always writes them, a hand-built file without them cannot be checked). Before this date a swapped B/C column inverted W without an error.
2. **Coverage.** At least **760 complete pairs of 800** (95%); below it the outcome is DESCRIPTIVE. All statistics use complete pairs only; an orphan B or C row is counted as an incomplete pair. *New models* (notebooks since 14 November 2026); applied by `report` since 15 November 2026.
3. **Competence gate (binding).** Accuracy of the generated answer on B ≥ 0.50 overall **and** separately on gold YES (532) and gold NO (268); otherwise NOT EVALUABLE. *New models.* Details: [VERIFY_ON_NEW_MODELS.md](VERIFY_ON_NEW_MODELS.md#competence-gate-on-the-determined-cases).
4. **Primary result.** CONFIRMED if W ≥ 0.60 and the lower bound of the 95% interval > 0.5; NOT CONFIRMED if the upper bound ≤ 0.5; otherwise NOT CONCLUSIVE. *Original* (HU1/HI1).

Applied by the new-model notebooks, not (yet) by `report`:

- **Length exclusion.** A pair whose B and C prompts have a different number of tokens is excluded from the primary analysis; excluded pairs are still scored and reported, with a sensitivity W including them. *Original* (Test U2 cell 4), extended for new models.
- **Label mass.** If the median `mass_total` is below 0.5 the model is NOT MEASURABLE; rows below 0.9 are flagged. *New models* (notebook v4, 15 November 2026). Yi-1.5-9B-Chat was classified NOT EVALUABLE for this reason by an owner decision of 14 November, before the rule existed.

Descriptive only, never deciding: W by family, variant, position; accuracy on B by family; baselines from the same outputs (entropy and −max of the renormalised label probabilities, generated UNKNOWN); W of prompt length (0.5 by construction, because B and C have the same length).

## 6. What W does not measure

- **W measures ranking, not abstention.** A model can rank almost every C above its B and still answer YES or NO to most C cases. Qwen3-32B: W 0.975, but the generated answer is UNKNOWN on 24.4% of the C cases (195 of 800) and on 0% of the B cases. Across the evaluable new and larger models the generated UNKNOWN rate on C is 19–55%. This is partly a design choice: the primary format has no explanatory sentence, because in Test U2 that sentence mainly changed the generated answer (Llama: UNKNOWN on 79% of the B cases with it, 5% without), while W changed little.
- **W is not specificity.** A high W does not show that the score reacts to indeterminacy rather than to generic answer uncertainty. With 95% intervals, p(UNKNOWN) is above the best generic baseline in four of the new and larger models, below it in three, and in one (Phi-4) the interval of the difference includes 0, which is inconclusive, not equality ([baseline intervals](../results/baseline_intervals_2026-11-15/README.md), post hoc).
- **W is not hallucination detection,** and not answer accuracy.

## 7. Preregistration and its limits

- Tests U, U2, M and C were run under protocols approved by the owner before each run. The protocols carry their dates in the text. They were added to this repository on 13–14 November 2026, after the runs, so their timing cannot be verified externally from the repository history.
- From 15 November 2026, a new protocol is committed, and tagged, **before** the run it governs; analyses added after the data are labelled post hoc.

## 8. Open points

- No human review of the gold labels has been documented. An annotation protocol (two independent human annotators, blind to gold, Krippendorff's alpha) is ready and waiting for annotators; LLM annotations, if any, will be reported separately and cannot replace the human agreement.
- The answer classifier of Test C agrees with the owner's blind reading on 0.680 of 100 answers (threshold 0.90): HC4 is read with that warning.
- Code and tests were generated with AI tools ([AI_USAGE.md](AI_USAGE.md)); an independent human review of the metric and replay code is pending.
