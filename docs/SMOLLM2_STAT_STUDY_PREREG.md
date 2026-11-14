# IndetBench — SmolLM2 determinability study, preregistration v0.1

**Locked design date:** 2026-11-13. This protocol is frozen before running the new 240-pair confirmatory dataset. It is a model-specific evaluation, **not** a claim of first-ever abstention research.

## Objective and closest prior research

Evaluate whether a pinned external Hugging Face model's *first-token uncertainty signal* discriminates logically determined from undetermined answers on strictly paired contexts. This supplements (does not replace) published abstention, answerability and uncertainty benchmarks.

- SQuAD 2.0 (Rajpurkar, Jia & Liang, ACL 2018): answerable/unanswerable question answering.
- Wen, Howe & Wang (EMNLP 2024): context perturbations and behavioral abstention.
- LM-Polygraph benchmark (Vashurin et al., TACL 2025): multiple UQ methods and tasks.
- AbstentionBench (Kirichenko et al., NeurIPS 2025): 20 datasets / 20 frontier models, broader behavioral assessment.
- Evidence Sufficiency Benchmark (Zhang & Wu, 2026): graded evidence sufficiency and conflicting evidence.
- Ling et al. (EMNLP 2026): abstention and UNKNOWN options can introduce prompt artifacts.

**No priority or general superiority claim**. Novelty hypothesis: a tightly paired, controlled logit-plus-behavior diagnostic with baseline comparison and archived replay, not breadth of tasks/models.

## Fixed model / data

- Model: `HuggingFaceTB/SmolLM2-360M-Instruct`.
- Immutable revision: `c15f933c73438218a2bc078446c513173cc4f06a`.
- CPU float32, greedy, temperature disabled, `max_new_tokens=12`; exact environment recorded in run.
- 240 **new**, originally generated story pairs (480 prompts), six logic families × 40 each.
- Within each family: two input surface formats (prose vs enumerated facts) × two instruction styles (strict vs short) × ten stories. In every cell, five B answers YES and five B answers NO.
- Each B is logically determined and each paired C admits both YES and NO (as understood by the formal family generator). These labels require an additional independent semantic audit before publication.
- Identical question, possible names and general story structure across each pair; one or more facts differ to change logical determinability. Prompt lengths and token differences will be audited (not guaranteed matched).
- The whole 240-pair set is confirmatory for this one model; no thresholds, examples, prompts, test families, or exclusions will be changed in response to these results. Earlier four-pair smoke tests are separate and excluded.

## Data integrity / audit

- Generated examples, family IDs, condition, language, and B gold answer must be stored in a frozen JSONL in this private repository. *(Note added 14 Nov 2026: the repository has since been made public; "private" here describes its status when this was written.)* Audit logical truth tables by family and check all complete pairs.
- No examples from SQuAD, AbstentionBench, or other third-party datasets are redistributed.
- Do not remove examples based on observed model behavior or a low W.
- Exclude a complete B/C pair from a score metric **only** for missing/nonfinite model probabilities, with exact exclusions documented. Invalid generated response (`ALTRO`) is a behavioral failure, not a discarded response.
- Check label-mass identity, expected model SHA, tokenizers and language; validate exact row count and IDs.
- If a frozen item is semantically invalid, document it without retroactively changing the primary dataset; release corrected corpus as a separately versioned follow-up.

## Preregistered endpoints

Primary: `W = (sum over 240 pairs of [p_UNKNOWN(C)>p_UNKNOWN(B)] + 0.5*[tie]) / 240`. H0 = 0.5. Use story-level nonparametric percentile bootstrap, 10,000 replicates, deterministic seed 20261113, 95% CI; a two-sided sign/permutation check on non-tied discordance is an additional inference. Only conclude `W>0.5` if CI lower bound > 0.5 and paired sign test Holm-adjusted p < 0.05.

Secondary and exploratory (report all even if negative):
- AUROC and 95% story bootstrap for raw p_UNKNOWN on the 480 B/C responses.
- Comparisons on **the same complete pairs** with normalized UNKNOWN mass `p_U/(p_Y+p_N+p_U)` and `1-max(p_Y,p_N)` as alternative unsupervised scores; paired ΔW relative to raw p_UNKNOWN, 95% story bootstrap and Holm family-wise correction.
- Generated-answer behavior: accuracy on determined B (YES/NO), abstention on C, inappropriate abstention on B, over-answer on C, exact `ALTRO` non-compliance; explicit confusions, not only a single F1.
- W and behavioral rates by family, prompt style, surface format, and true B label, with CIs; **descriptive**, not confirmatory subgroup testing.
- Input length shortcut: B−C token count and character count, proportion of pairs with absolute token diff >3, and W for a predictor using only prompt lengths. If length alone predicts B/C, flag as design confounding rather than dismiss it.
- `p_UNKNOWN` is a baseline, **not** a universal detector. Abstention output and internal probability are not independent evidence of epistemic uncertainty.

No post-hoc selection of favorable subgroups. All numbers exploratory unless named primary above.

## Release / publication gates

The first model is **one 360M-parameter model**. It cannot establish generalization to large LLMs, new language families or out-of-distribution real texts. Benchmarks with more datasets/models may be more comprehensive overall. To strengthen a paper, repeat frozen methods on ≥2 additional model architectures, include genuinely natural independently audited data, human double annotation and inter-annotator agreement, prompt-artifact controls (including replacing UNKNOWN with a neutral token) and compare established uncertainty estimators on identical rows.

Research conclusions should explicitly contrast with cited prior work and avoid claiming universal firstness, measured `truthfulness`, or more comprehensive scope than AbstentionBench and LM-Polygraph.
