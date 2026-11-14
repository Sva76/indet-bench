# Literature and originality audit — 13 November 2026

## Research positioning

**IndetBench is NOT the first framework to study LLM abstention, answerability, uncertainty estimation, context insufficiency, or controlled perturbations.** We cannot claim it is the most comprehensive benchmark overall, and we have not established that it is the first to test SmolLM2 in this way. The search is substantive but not exhaustive (Google Scholar, Semantic Scholar, peer-review citations, unpublished work, other languages and private systems could contain similar protocols).

**Defensible contribution to investigate:** controlled pairs differing in logical determinability with matched format and question; internal first-token log-probability features separated from actual generated abstention; paired bootstrap and sign tests, family-level and prompt-format analysis, explicit coverage, source hashes and archive replay. It is an integrated *diagnostic protocol*, not a new proven detector.

## High-relevance antecedents

| Work and source | Prior achievement | What it does NOT allow us to claim |
|---|---|---|
| [Rajpurkar, Jia & Liang, SQuAD 2.0, ACL 2018](https://aclanthology.org/P18-2124/) | More than 50,000 adversarial unanswerable questions, high-quality QA evaluation | IndetBench invented answerability or unanswerable-context testing |
| [Wen, Howe & Wang, EMNLP 2024](https://aclanthology.org/2024.findings-emnlp.197/) | Alters/removes/replaces contexts, tests when six LLMs abstain | IndetBench is first to use paired or perturbed contexts |
| [Vashurin et al., LM-Polygraph, TACL 2025](https://aclanthology.org/2025.tacl-1.11/) | State-of-the-art uncertainty method benchmark across eleven tasks | IndetBench covers more methods, tasks or a superior UQ leaderboard |
| [Kirichenko et al., AbstentionBench, NeurIPS 2025](https://proceedings.neurips.cc/paper_files/paper/2025/hash/fb122bfc3f0127a94ded048b5b03496f-Abstract-Datasets_and_Benchmarks_Track.html) | Twenty LLMs and twenty datasets, six abstention scenarios, human-validated judges | IndetBench is the broadest behavioral abstention test |
| [Zhang & Wu, Evidence Sufficiency Benchmark, 2026](https://www.techscience.com/cmc/v89n1/68467/html) | Five graded evidence levels (full, partial, irrelevant, absent, contradictory), seven models, three prompts | Graded evidence sufficiency and conflict testing are new |
| [Ling et al., EMNLP 2026](https://aclanthology.org/2026.emnlp-main.549/) | Demonstrates that the mere presence of UNKNOWN can increase abstentions, even when actual knowledge is present | First-token UNKNOWN probability automatically measures true uncertainty |
| [SmolLM2-360M-Instruct official model card](https://huggingface.co/HuggingFaceTB/SmolLM2-360M-Instruct) | Existing general evaluations of instruction following, reasoning, QA and common benchmarks | SmolLM2 has never been evaluated, or every numerical evaluation of it would be new |

## Direct comparison against IndetBench

| Design property | IndetBench target / established status |
|---|---|
| Closed-world answer determinability under carefully constructed B/C counterfactual changes | Core controlled task; also overlaps context-perturbation literature |
| Pre-output `p(UNKNOWN)` vs generated answer and alternate scores on **identical** cases | Core differentiator to evaluate; not conceptually unprecedented |
| Six independent logic families, two surface formats, two prompt styles, balanced B YES/NO | Frozen for the new 240-pair SmolLM2 study; formal generator does NOT replace independent human label audit |
| Paired statistical inference, story-bootstrap, source code/archive checksum | Explicitly preregistered; significance cannot establish broader generalization |
| Natural text, multiple architectures, multiple semantic graders, thorough prompt-artifact neutral-token control | **Not** satisfied by the new synthetic SmolLM2 run |
| Generality to arbitrary Hugging Face models | One SmolLM2 CPU integration test passed; broad external interoperability unproven |

## What would strengthen an originality claim

1. Reproduce official baselines on the **same exact test items** and model revisions; tables comparing numbers from different datasets are invalid.
2. Introduce a genuinely discriminative **negative control** for prompt-artifact inflation: neutral substitute for UNKNOWN and/or forced binary choice with equivalently scored alternative.
3. Independently audit logical B/C labels (especially possible-world cases and ambiguities) with multiple annotators blind to model outputs.
4. Add natural-language stimuli, separate calibration and test splits, and unseen semantic families; keep explicit lexical-length baselines.
5. Replicate frozen statistics on several model families and sizes, with a disjoint later snapshot.
6. Report whether the model *can answer B* as well as whether it ranks C above B; otherwise a poor reasoning model's uncertainty signal may be meaningless.
7. Compare to held-out published tools rather than only alternate transforms of the same label logits.

**Publication-safe wording:** “IndetBench provides a reproducible, controlled-pair diagnostic benchmark for answer determinability and uncertainty-related signals. Its methodological novelty, performance and external validity require head-to-head replication against existing benchmarks and baselines.”
