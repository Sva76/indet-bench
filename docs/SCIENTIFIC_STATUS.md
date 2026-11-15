# Scientific status of IndetBench (updated 14 November 2026)

This page states what the research behind IndetBench has shown, what it has not shown, and where each number comes from. Every number below is taken from an archived report in `research_originals/`. When this page and a report disagree, the report is authoritative.

## Two separate bodies of evidence

| | Original research (Steps 1–2) | Hugging Face CPU studies (13–14 Nov) |
|---|---|---|
| Models | Qwen3-8B, Mistral-Nemo-Instruct-2407, OLMo-2-1124-7B-Instruct, Llama-3.1-8B-Instruct (7–12B), pinned revisions in [`hf_revisions_verified.json`](../research_originals/hf_revisions_verified.json) | SmolLM2-360M, SmolLM2-1.7B, Qwen2.5-0.5B, Qwen2.5-1.5B, OLMo-2-0425-1B, TinyLlama-1.1B (all Instruct/Chat) |
| Data | Frozen logic stories (Tests U/U2/M, 800 B/C pairs per format) and synthetic passages (Test C, 600 + 200 pairs) | New 240-pair set `data/smol_stat_v01_frozen.jsonl`, created on 13 Nov, not yet human-reviewed |
| Protocols | Preregistered, owner-approved before each run | Preregistration written minutes before the run |
| Status | Completed and reported; numeric results reproduced from archives with 0 differences | Exploratory; one model evaluable under the competence rule |

The two must not be merged into one conclusion.

## What B and C mean in the original design

B and C are **minimal pairs**: the same story, in which one variable is stated with two possible values. In B the answer is the same whichever value holds, so it is determined. In C the two values lead to opposite answers, so the correct answer is UNKNOWN. B and C differ in one other fact only. In C the information is not missing: it is present, but it does not settle the answer.

## Results that hold (original research)

1. **p(UNKNOWN) separates C from B in prose, in 4 models out of 4.** The measure is the first-token probability of UNKNOWN, with no training. Test U: W 0.736–0.914 (prose V2). Test U2, prose without the explanatory sentence: Qwen 0.975, Mistral 0.783, OLMo 0.694, Llama 0.746, all preregistered and confirmed. Test C, text passages: W 0.94–0.98. Sources: `Risultati_testU.md`, `Risultati_testU2.md`, `Risultati_testC.md`.
2. **No published method tested beats p(UNKNOWN) in a replicated way.** The methods are LM-Polygraph estimators (M1), the SIRIN answerability probe (M2) and zero-shot judge (M3), and the Obeso et al. probes (M4). This was preregistered in Test M (800 pairs) and Test C (600 pairs). The one exception is M4-LoRA on Llama in Test M (ΔW +0.086 [+0.039, +0.135]). It came from the AND family and was not replicated in Test C (ΔW −0.147). Sources: `Risultati_testM_A.md`, `Risultati_testM_B.md`, `Risultati_testC.md`.
3. **Internal-state probes were tested.** Step 1 (tests 5–7, Qwen and Mistral) and the M2/M4 probes in Tests M and C show the same pattern. Probes separate B from C within the formulations they were trained on, but they do not generalise to new formulations. Source: `step1/Riepilogo_Step1.md`.
3b. **Exploratory, new model families (14 Nov 2026).** On the same frozen prose benchmark, p(UNKNOWN) gives W 0.818 [0.788, 0.848] on Gemma-2-9B-it, 0.931 [0.911, 0.950] on Falcon3-7B-Instruct and 0.944 [0.924, 0.963] on Phi-4, all above the competence gate; the Qwen3-8B control reproduces Test U2 on 1600/1600 rows. Yi-1.5-9B-Chat is NOT EVALUABLE for a technical reason (label mass ≈ 2·10⁻⁶ at the first token; owner's decision). Descriptively, generic baselines from the same outputs do about as well or better (Gemma: entropy 0.891, ΔW −0.074), so these data do not show information specific to indeterminacy beyond generic answer uncertainty. The NOT variant is weaker than POS in all five models: an open question for a dedicated test (see 3c). Not an independent validation. Source: [`NEW_MODELS_RESULTS_2026-11-14.md`](NEW_MODELS_RESULTS_2026-11-14.md).
3c. **Exploratory, larger models (15 Nov 2026).** Same benchmark and rules: Qwen3-32B 0.975 [0.961, 0.988], Llama-3.3-70B-Instruct in 4-bit nf4 0.908 [0.889, 0.928], OLMo-2-0325-32B-Instruct 0.886 [0.861, 0.910], Gemma-2-27B-it 0.870 [0.839, 0.900], all above the competence gate and the label-mass rule; the Qwen3-8B control reproduces Test U2 on 1600/1600 rows. Within a family W is higher than for the smaller model in three families of four (descriptive; versions and training data also differ). Baselines (descriptive): ΔW vs the best independent baseline +0.085 (Qwen3-32B), +0.051 (Gemma-2-27B), −0.034 (OLMo-2-32B), −0.080 (Llama-3.3-70B): no general superiority. The NOT variant is stronger than POS in Qwen3-32B and Llama-3.3-70B (95% intervals exclude 0), so "NOT is always weaker" is falsified (owner's decision, 15 Nov); a step versus a gradual change cannot be distinguished with two sizes per family. Source: [`LARGER_MODELS_RESULTS_2026-11-15.md`](LARGER_MODELS_RESULTS_2026-11-15.md). Reasoning models: protocol approved ([`REASONING_PART_B_PROTOCOL.md`](REASONING_PART_B_PROTOCOL.md)), not yet run.
4. **Strong dependence on logical family and wording.** Many methods, and p(UNKNOWN) in 3 of 4 models, vary strongly between AND, OR and IMPLIES. Part of this was preregistered (families in M2); the rest is exploratory.
5. **Uncertainty-of-answer estimators read a confident abstention as certainty.** Examples: Mistral in Test M, W ≈ 0.30; M1-MSP on Qwen in Test C. This is an observation; the mechanism is an interpretation.

## What has not been shown

- That any method detects hallucinations with context. In Test C, HC4 within B could not be evaluated (0 errors on B), and HC4 within C is confounded with the passage family.
- That the results hold beyond the models tested so far (exploratory evidence on open-weights models from 7B up to 70B), or outside English, template texts and the tested formats.
- That p(UNKNOWN) works in symbolic formats: there it is weak or reversed (Test U, Test U2).
- Anything general about the small models on the 240-pair set. Under the binding competence rule (B accuracy ≥ 0.50 overall and on gold YES and NO) only Qwen2.5-1.5B is evaluable (W 0.613 [0.550, 0.671], exploratory, corpus not human-validated). Qwen2.5-0.5B, OLMo-2-0425-1B, SmolLM2-1.7B and SmolLM2-360M are NOT EVALUABLE; SmolLM2-1.7B and OLMo-1B fail even at the theoretical chance threshold of 1/3. TinyLlama is NOT MEASURED: its tokenizer shares the first token between labels, a limit of the measurement, not a result about the model. Details: [`COMPETENCE_240_PAIRS.md`](COMPETENCE_240_PAIRS.md), [`QWEN05_TINYLLAMA_REPORT_2026-11-14.md`](QWEN05_TINYLLAMA_REPORT_2026-11-14.md).
- Anything new about hidden states: the prospective hidden-state experiment was not run (owner's decision, 14 Nov), because Step 1 already showed that probes do not transfer ([`HIDDEN_UNCERTAINTY_EXPERIMENT_PROTOCOL.md`](HIDDEN_UNCERTAINTY_EXPERIMENT_PROTOCOL.md)).

## Reproducibility already verified

- The original W, ΔW and confidence intervals of Test C (508 values), Test M notebook A (498) and notebook B (176), and every statistic of Test U (8,517 values, HU1, HU2, the lexical "or" control and the polarity screening) and Test U2 (1,319, HI1–HI3), are recomputed from the archived per-row scores with **0 differences**. For HC4 of Test C, the frozen classifier re-derives all 21,582 archived answer labels and the HC4 statistics follow (44,969 values); this is reproducibility, not a check that the labels are right (agreement with the owner's 100-answer sample 0.680, threshold 0.90). Use `python -m indetbench.replay` with the original ZIPs, published in [`research_originals/step2/outputs/`](../research_originals/step2/outputs/README.md) (SHA-256 in [`REPRODUCIBILITY_STATUS.md`](REPRODUCIBILITY_STATUS.md)).
- From the archived Test M reference scores, `python -m indetbench.original_benchmark report` gives the published Test U2 point estimates (0.975, 0.783, 0.694, 0.746) and the per-family values of Test M. Its bootstrap intervals agree to about ±0.004.
- All 12 pinned model and dataset revisions exist on the Hugging Face Hub and match ([`hf_revisions_verified.json`](../research_originals/hf_revisions_verified.json)).

## Known limits

- Single human reviewer for semantics and for the answer classifier; classifier agreement 0.68 (Test C).
- The reference p(UNKNOWN) is close to 1 in Test C, so an advantage of other methods could not have been seen there.
- Many comparisons without multiplicity correction; the 3-of-4 rule mitigates but does not solve this.

To check these results on another model, follow [`VERIFY_ON_NEW_MODELS.md`](VERIFY_ON_NEW_MODELS.md). For new models it adds a binding competence gate, fixed on 14 November 2026 before any new-model data: accuracy ≥ 0.50 on the determined B cases, both overall and separately on gold YES and gold NO (the B cases are 532 YES and 268 NO, so a model that always answered YES would otherwise pass with 0.665). The original protocols had no such gate; all four original models pass all parts (lowest: Mistral-Nemo, 0.509 on gold YES).
