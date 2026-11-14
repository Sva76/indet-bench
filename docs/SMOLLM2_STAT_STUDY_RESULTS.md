# External statistical validation — SmolLM2-360M-Instruct (13 November 2026)

**Result: primary numeric endpoint not confirmed; model-task competence gate failed, making substantive uncertainty-detection validation NOT EVALUABLE.** One fixed external model, 240 controlled synthetic B/C pairs, 480 genuine model inferences. No claim that IndetBench is the first abstention benchmark or more comprehensive than LM-Polygraph/AbstentionBench.

## Frozen study and evidence

- [Preregistered protocol](SMOLLM2_STAT_STUDY_PREREG.md) created before inference.
- [Frozen inputs](../data/smol_stat_v01_frozen.jsonl), 240 B/C pairs, six families × 40, two formats and two instruction styles. Input SHA-256: `e7d83b1e661ed34ab3c73a37481301bdab1258a5867d1ac1e57f66762f8fc36d`.
- Pinned Hugging Face model `HuggingFaceTB/SmolLM2-360M-Instruct`, immutable SHA `c15f933c73438218a2bc078446c513173cc4f06a`.
- [Successful four-shard model inference and analysis](https://github.com/Sva76/indet-bench/actions/runs/43493566268) with original CSV outputs and machine-readable report in time-limited GitHub Actions artifacts.
- Computations verified independently from the four original CSV shards: exactly 480 distinct responses, 240 complete B/C pairs, same model revision; W, sign counts and bootstrapped CI reproduced without using the tabular report as inputs.

## Preregistered primary result

| Statistic | Result |
|---|---|
| W(C higher p_UNKNOWN than B) | **0.47917** |
| 95% pair-bootstrap CI, 10,000 resamples | **[0.41667, 0.54583]** |
| Paired wins / losses / ties | **115 / 125 / 0** |
| Exact two-sided sign-test p-value (corrected) | **0.5613667387** |
| AUROC of p_UNKNOWN across B/C | **0.50106 [0.48422, 0.51819]** |

The data **do not support** W > 0.5 numerically. **Scientific interpretation is NOT EVALUABLE for this model**, because the model fails the prerequisite of answering straightforward determined questions (B: 92/240 correct, 0 NO generations). This is not evidence of a lack of an uncertainty signal in otherwise competent models. The sign-test p-value is the *unadjusted* exact test; any multiple-testing adjustment cannot make it more significant.

### Statistical software correction — transparent disclosure

The first archived report (original four-shard run) incorrectly printed `sign_two_sided_p=1.0` because `2**n`, with `n` a `numpy.int64`, silently overflowed when `n=240`. Independent recomputation with Python arbitrary-precision integers gives `p=0.5613667387`. The output `W`, bootstrap confidence interval, win/loss counts and AUROC **were unaffected**. A specific fix casting counts to Python `int` and a regression test were committed on the review branch, without modifying the preregistration or model-generated scores. The original report remains in GitHub Actions as audit evidence; this explanation is not an attempt to rewrite history.

## What the model actually answered

| Behavioral check | Observed |
|---|---|
| Correct YES/NO on answerable B | **92/240 (38.3%)** |
| Unnecessary UNKNOWN on B | **64/240 (26.7%)** |
| Correct UNKNOWN on underdetermined C | **68/240 (28.3%)** |
| Unsupported YES/NO on C | **172/240 (71.7%)** |
| Invalid output format (ALTRO) | 0 |

No `NO` answers were emitted on either side; observed behavior was only `YES` and `UNKNOWN`. All B=NO items were missed (0/120 correct). This limits any interpretation of the uncertainty ranking as substantive reasoning.

## Differences by family and presentation (exploratory)

| Family | Pairs | W |
|---|---:|---:|
| OR_FLEETS | 40 | 0.375 |
| AND_SWITCH | 40 | 0.450 |
| RULE_DIRECTION | 40 | 0.725 |
| TEMPORAL_ORDER | 40 | 0.500 |
| NUMERIC_CHOICE | 40 | 0.350 |
| XOR_BEACONS | 40 | 0.475 |

The score changes greatly across family structure. The two **separately generated** sets by presentation format differ:

| Format | Pairs | W | C abstention |
|---|---:|---:|---:|
| Prose | 120 | 0.417 | 1/120 (0.8%) |
| Enumerated facts | 120 | 0.542 | 67/120 (55.8%) |

**This is an association, not a clean causal format experiment**, because the specific stories appearing in prose vs enumerated conditions were different (although balanced by family and gold B label). A proper within-story format counterfactual is needed to isolate the effect.

## Weak alternative baselines and confounds

- Renormalized `p_UNKNOWN/(p_YES+p_NO+p_UNKNOWN)` also gave W = 0.479, ΔW = 0.
- Alternative `1-max(p_YES,p_NO)` gave W = 0.458, ΔW = −0.021 (CI approximately −0.075 to 0.033).
- **Prompt-token-length-only ranking** gave W = 0.583. Since C prompts were on average 0.83 tokens longer (20/240 pairs had >3-token difference), the design retains a superficial cue. Treat as a confound rather than as proof the length predictor captures logic.
- First-token p_UNKNOWN is not an independent window into true reasoning; prompt-artifact work (Ling et al., EMNLP 2026) directly warns of this.

## Scientific conclusion and next independent gates

The code can run a real external Hugging Face model and produce reproducible score-based and behavioral reports. **On this small model, the intended signal does not reliably distinguish underdetermined from determined cases.** That is a reproducible **numerical null result** for this frozen setting, but NOT a substantive validation of uncertainty detection: the model did not execute the base YES/NO/UNKNOWN task adequately. It is not evidence against other models or other uncertainty methods.

Before publication or broader generalization:
1. Double-blind or at least independent two-person semantic audit of a stratified sample, recording agreement.
2. Within-story paired reformatting and neutral-token substitution to expose prompt artifacts.
3. A second, substantially different model architecture and a larger capable model; report success on B as a prerequisite to interpreting B/C.
4. A natural-text corpus with clear licensing and contrastive controls.
5. Head-to-head published method baselines on **identical** examples, not juxtaposed numbers from incompatible benchmarks.

The repository is public and reviewable; these results do not justify declaring this method **better** or **more complete overall** than existing benchmarks.
