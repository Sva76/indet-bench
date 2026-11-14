# Related work

*Version 1, 14 November 2026. Complements the [literature and originality audit of 13 November](NOVELTY_AND_RELATED_WORK_2026.md).*

This page places IndetBench among published work. For each area it says what has already been done, how IndetBench relates to it, and what IndetBench does **not** claim.

**How the sources were checked.**
- Every work listed was opened on 14 November 2026, at its arXiv, ACL Anthology, OpenReview, NeurIPS or publisher page.
- Its design and findings were read from that page, so the summaries below are ours. Readers should consult the original before quoting a number.
- Where a venue is not given, we found only a preprint.
- The search was targeted, not systematic: English only, about 30 queries, up to November 2026. "We did not find" means that it did not appear in this search, not that it does not exist.

## Summary

- **Not new.** Each of these has been studied before:
  - abstention and unanswerable-question benchmarks;
  - answerable/unanswerable variants built by removing a premise or the context;
  - logical reasoning with an *Unknown* label;
  - the poor cross-task transfer of internal-state probes;
  - the failure of uncertainty estimators under ambiguity;
  - the gap between "the answer may be wrong" and "the question cannot be answered".
- **What we did not find** in the literature we examined: minimal B/C pairs with the **same token length**, in which **the uncertain line is present in both** and a single other value decides whether the answer is determined, used to stress-test **uncertainty estimators and probes** with a within-pair metric and form controls.
- **IndetBench therefore claims to be a controlled diagnostic benchmark**, together with preregistered and mostly negative results on published methods, run on its pairs. It does not claim a new task, a new metric or a new detector.

## 1. Abstention and unanswerable questions

- **SQuAD 2.0** ([Rajpurkar, Jia & Liang, ACL 2018](https://aclanthology.org/P18-2124/)): adversarially written unanswerable questions for extractive QA.
- **UnknownBench** ([Liu et al. 2023, arXiv 2311.09731](https://arxiv.org/abs/2311.09731)): unanswerable questions (invented concepts, false premises, Natural Questions with one noun replaced by a non-existent concept). Each comes with an answerable control group from the same template. Uncertainty is measured through verbalised confidence and refusal.
- **Context perturbations in science QA** ([Wen, Howe & Wang, Findings of EMNLP 2024](https://aclanthology.org/2024.findings-emnlp.197/)): removing, replacing or padding the gold context, six LLMs.
- **FaithEval** ([Ming et al., ICLR 2025, arXiv 2410.03727](https://arxiv.org/abs/2410.03727)): unanswerable, inconsistent and counterfactual contexts. For inconsistent contexts the expected answer is "conflict".
- **AbstentionBench** ([Kirichenko et al., NeurIPS 2025 Datasets and Benchmarks](https://proceedings.neurips.cc/paper_files/paper/2025/hash/fb122bfc3f0127a94ded048b5b03496f-Abstract-Datasets_and_Benchmarks_Track.html)): 20 datasets in six scenarios and 20 models, with abstention judged by an LLM. It reports that reasoning fine-tuning degrades abstention.
- **Missing premises** ([Fan et al. 2025, arXiv 2504.06514](https://arxiv.org/abs/2504.06514); [Tong et al. 2026, arXiv 2608.16554](https://arxiv.org/abs/2608.16554)): ill-posed problems obtained by deleting a necessary premise from a solvable one.
- **Evidence sufficiency** ([Zhang & Wu, CMC 2026](https://www.techscience.com/cmc/v89n1/68467/html)): five graded levels from full support to conflicting evidence.
- **Sufficient context** ([Joren et al., ICLR 2025, arXiv 2411.06037](https://arxiv.org/abs/2411.06037)): with insufficient context, models often answer instead of abstaining.

*Relation to IndetBench.* These works mainly measure **whether the model abstains**. IndetBench uses its pairs to evaluate **scores** (output-based estimators, judges, probes), each against a training-free reference computed on the same pairs. Where earlier work builds the unanswerable version by removing or replacing information, the two versions differ in length and content. In IndetBench, B and C have the same number of tokens and the same uncertain line, and the information in C is present but does not settle the answer.

*Not claimed:* being the first abstention benchmark, the first to use answerable/unanswerable variants, or the broadest one.

## 2. Minimal pairs and contrast sets

- **BLiMP** ([Warstadt et al., TACL 2020, arXiv 1912.00582](https://arxiv.org/abs/1912.00582)): 67,000 grammatical minimal pairs, scored by whether the model assigns the higher probability to the acceptable member.
- **Contrast sets** ([Gardner et al. 2020, arXiv 2004.02709](https://arxiv.org/abs/2004.02709)): small expert edits around a test instance, which typically change the label, expose models that overfit to dataset artefacts.
- **RobustLR** ([Sanyal et al. 2022, arXiv 2205.12598](https://arxiv.org/abs/2205.12598)): logical contrast sets and equivalence sets for rule-based deduction (adding a conjunction, disjunction or negation; contrapositive rewriting), with labels True/False/Unknown. It reports negation as the hardest perturbation.

*Relation to IndetBench.* The principle of comparing scores **within a pair** is established. IndetBench's W (the share of pairs in which the C score exceeds the B score, ties counting one half) is a standard matched-pair concordance, equivalent to an AUROC restricted to matched pairs. RobustLR is the closest logical precedent, but it measures the accuracy and consistency of trained models, not uncertainty signals.

*Not claimed:* a new metric or a new evaluation principle.

## 3. Logical reasoning with an *Unknown* answer

- **Datasets with an *Unknown* label:** ProofWriter, in its open-world setting with True/False/Unknown ([Tafjord, Dalvi Mishra & Clark 2021, arXiv 2012.13048](https://arxiv.org/abs/2012.13048)), and FOLIO, also True/False/Unknown ([Han et al., arXiv 2209.00840](https://arxiv.org/abs/2209.00840)).
- **How models handle *Unknown*:** they get it wrong in both directions, depending on model and dataset ([Ling et al. 2025, WAKENLLM, arXiv 2507.16199](https://arxiv.org/abs/2507.16199)). Merely offering an *Unknown* option can inflate abstention, even when it is replaced by an unrelated word ([Ling et al., EMNLP 2026](https://aclanthology.org/2026.emnlp-main.549/)).
- **Hidden states versus outputs:** on True/False/Unknown tasks, hidden states can decode the correct label while output sequence scores collapse ([Yan, Wang & Pan 2026, arXiv 2608.31068](https://arxiv.org/abs/2608.31068)).

*Relation to IndetBench.*
- The C cases are an instance of an "Unknown" conclusion under a closed set of facts.
- Ling et al. (EMNLP 2026) bear directly on the reference signal. p(UNKNOWN) depends on the instruction that offers UNKNOWN, and IndetBench's own Test U2 found that an explanatory sentence raised generated UNKNOWN answers on the determined B cases too. p(UNKNOWN) should therefore be read as a prompt-dependent score, not as a pure measure of uncertainty.
- The repeated observation that p(UNKNOWN) orders C above B while the models almost never generate UNKNOWN is in line with the internal/output gaps reported by Yan et al. and by Orgad et al. (§5).

*Not claimed:* a new logical-reasoning task.

## 4. Output-based uncertainty: estimators, benchmarks and their limits

- **Self-evaluation from token probabilities:** P(True) and P(IK) ([Kadavath et al. 2022, arXiv 2207.05221](https://arxiv.org/abs/2207.05221)).
- **LM-Polygraph benchmark** ([Vashurin et al., TACL 2025](https://aclanthology.org/2025.tacl-1.11/)): selective QA, generation and claim-level fact-checking. It recommends keeping maximum sequence probability as a strong baseline. It has no unanswerable or paired setting.
- **46 estimators via LM-Polygraph** ([Agnimo et al. 2026, arXiv 2605.27016](https://arxiv.org/abs/2605.27016)): no estimator is reliable across tasks and models, and the dataset drives the ranking more than the model does. Response length is a strong confounder.
- **Length bias in correctness functions** ([Santilli et al., ACL 2025, arXiv 2504.13677](https://arxiv.org/abs/2504.13677)) can distort the AUROC comparisons of uncertainty methods.
- **Ambiguity** ([Tomov et al. 2025, arXiv 2511.04418](https://arxiv.org/abs/2511.04418)): under aleatoric uncertainty, consistency-based estimators, probes and ensembles degrade to near chance.
- **Two axes of abstention** ([Wagner 2026, arXiv 2607.08456](https://arxiv.org/abs/2607.08456)): answer correctness and question answerability are distinct axes. Output confidence separates correct from wrong answers but barely separates wrong-answerable from unanswerable questions.

*Relation to IndetBench.*
- IndetBench reaches the same conceptual conclusion as Wagner (2026) on different data. Estimators of uncertainty *about the answer* are not detectors of an answer that *cannot be determined*. The sharpest case is Mistral-Nemo in Test M, where a confident UNKNOWN is read as low uncertainty (W ≈ 0.30). This explanation is an interpretation, not a test.
- The equal-length pairs are a direct response to the length and lexical confounds documented by Agnimo et al., Santilli et al. and Wagner: by construction they remove those confounds from the B/C comparison.
- The reference p(UNKNOWN) is the probability of an offered abstention label. It is a close relative of maximum probability and P(True), not a new estimator. Whether it carries information beyond generic output uncertainty (entropy, maximum probability) computed on the same outputs is **not established**. The exploratory new-model run of 14 November 2026 points the other way: entropy or maximum probability does about as well as p(UNKNOWN) on Falcon3-7B and Phi-4 and better on Gemma-2-9B (descriptive ΔW −0.074 [−0.099, −0.050]; [report](NEW_MODELS_RESULTS_2026-11-14.md)).

*Not claimed:* that uncertainty estimators failing under indeterminacy is a new finding, or that p(UNKNOWN) is a superior detector.

## 5. Internal-state probes: generalisation and surface cues

- **Probes that transfer poorly:**
  - error-detection probes are largely "skill-specific", and earlier evidence of generalisation was often matched by simple logit baselines ([Orgad et al. 2024, arXiv 2410.02707](https://arxiv.org/abs/2410.02707));
  - probe directions trained on different tasks are nearly orthogonal ([Azizian et al., ICML 2025 workshop, arXiv 2506.08572](https://arxiv.org/abs/2506.08572)).
- **Evidence for transfer:**
  - an answerability direction read at the first generated token transfers across SQuAD 2.0, Natural Questions and MuSiQue, with a drop ([Slobodkin et al., EMNLP 2023, arXiv 2310.11877](https://arxiv.org/abs/2310.11877));
  - truth probes generalise better once polarity (negation) is accounted for ([Bürger et al. 2024, arXiv 2407.12831](https://arxiv.org/abs/2407.12831)).
- **Surface cues:** on SelfAware a bag-of-words model alone reaches 0.87 AUROC on answerability, so much of the probe signal there is lexical ([Wagner 2026](https://arxiv.org/abs/2607.08456)).
- **Published tools evaluated in IndetBench:** the answerability probe and judges of SIRIN ([arXiv 2608.00033](https://arxiv.org/abs/2608.00033)) and the hallucination probes of Obeso et al. (2025), listed in [REFERENCES.md](REFERENCES.md).

*Relation to IndetBench.* Step 1 found that probes separate B from C within the formulations they were trained on and do not transfer to new ones. Probe directions from different training sets often had cosine similarity between 0.1 and 0.4, and about 0 between disjoint training sets. A detector trained on SQuAD 2.0 responded to a change in form, a variable taking two values, rather than to indeterminacy. These results are **consistent with** Orgad et al., Azizian et al. and Wagner. They are a preregistered replication in a new domain (logical determinability), not a discovery.

*Not claimed:* being the first to show that probes do not generalise or that they pick up surface cues.

## 6. Negation

Language models are weak on negation ([Truong et al. 2023, arXiv 2306.08189](https://arxiv.org/abs/2306.08189)). RobustLR (§2) finds negation the hardest logical perturbation, and Bürger et al. (§5) show that polarity distorts truth probes. IndetBench's differences between POS and NOT variants are consistent with this literature and are reported as an open question, not as a new phenomenon.

## What IndetBench contributes, stated cautiously

1. **A controlled diagnostic benchmark for uncertainty-related signals.** The B/C pairs:
   - have the same token length;
   - contain the uncertain line in both members;
   - differ in one value only;
   - come in AND/OR/IMPLIES families and POS/NOT variants, with form controls.

   In the literature we examined we did not find a benchmark with this control.
2. **Preregistered results for published methods on those pairs** (LM-Polygraph estimators, SIRIN, a zero-shot judge, the Obeso et al. probes). None improved on the training-free reference in a replicated way, and most depended strongly on the logical family. These specific results are new. Their general shape ("it depends on the task") agrees with Agnimo et al. (2026).
3. **A validation protocol**:
   - a positive control for each method on its own domain before the pairs;
   - the reference computed in the same environment;
   - paired W and ΔW with story-level bootstrap;
   - a 3-of-4-models rule and reading rules fixed in advance;
   - checksums and archive replay.

   We present this as a practice, not as a first.
4. **Replications in a new domain** of known phenomena, declared as such.

## What IndetBench does not claim

- A new abstention task, metric or detector.
- That p(UNKNOWN) is better than generic output uncertainty, or that it works outside the prose format.
- Validity beyond the tested open-weights models of 7–12B parameters, English, and template texts.
- That any tested method detects contextual hallucinations.
