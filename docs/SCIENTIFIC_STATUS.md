# Scientific status of IndetBench (13 November 2026)

This page states what the research behind IndetBench has shown, what it has not shown, and where each number comes from. Every number below is taken from an archived report in `research_originals/`. When this page and a report disagree, the report is authoritative.

## Two separate bodies of evidence

| | Original research (Steps 1–2) | Hugging Face CPU studies (13 Nov) |
|---|---|---|
| Models | Qwen3-8B, Mistral-Nemo-Instruct-2407, OLMo-2-1124-7B-Instruct, Llama-3.1-8B-Instruct (7–12B), pinned revisions in [`hf_revisions_verified.json`](../research_originals/hf_revisions_verified.json) | SmolLM2-360M-Instruct; Qwen2.5-0.5B-Instruct and TinyLlama-1.1B-Chat (incomplete) |
| Data | Frozen logic stories (Tests U/U2/M, 800 B/C pairs per format) and synthetic passages (Test C, 600 + 200 pairs) | New 240-pair set `data/smol_stat_v01_frozen.jsonl`, created on 13 Nov, not yet human-reviewed |
| Protocols | Preregistered, owner-approved before each run | Preregistration written minutes before the run |
| Status | Completed and reported; numeric results reproduced from archives with 0 differences | Technical checks; no substantive scientific result yet |

The two must not be merged into one conclusion.

## What B and C mean in the original design

B and C are **minimal pairs**: the same story, in which one variable is stated with two possible values. In B the answer is the same whichever value holds, so it is determined. In C the two values lead to opposite answers, so the correct answer is UNKNOWN. B and C differ in one other fact only. In C the information is not missing: it is present, but it does not settle the answer.

## Results that hold (original research)

1. **p(UNKNOWN) separates C from B in prose, in 4 models out of 4.** The measure is the first-token probability of UNKNOWN, with no training. Test U: W 0.736–0.914 (prose V2). Test U2, prose without the explanatory sentence: Qwen 0.975, Mistral 0.783, OLMo 0.694, Llama 0.746, all preregistered and confirmed. Test C, text passages: W 0.94–0.98. Sources: `Risultati_testU.md`, `Risultati_testU2.md`, `Risultati_testC.md`.
2. **No published method tested beats p(UNKNOWN) in a replicated way.** The methods are LM-Polygraph estimators (M1), the SIRIN answerability probe (M2) and zero-shot judge (M3), and the Obeso et al. probes (M4). This was preregistered in Test M (800 pairs) and Test C (600 pairs). The one exception is M4-LoRA on Llama in Test M (ΔW +0.086 [+0.039, +0.135]). It came from the AND family and was not replicated in Test C (ΔW −0.147). Sources: `Risultati_testM_A.md`, `Risultati_testM_B.md`, `Risultati_testC.md`.
3. **Internal-state probes were tested.** Step 1 (tests 5–7, Qwen and Mistral) and the M2/M4 probes in Tests M and C show the same pattern. Probes separate B from C within the formulations they were trained on, but they do not generalise to new formulations. Source: `step1/Riepilogo_Step1.md`.
4. **Strong dependence on logical family and wording.** Many methods, and p(UNKNOWN) in 3 of 4 models, vary strongly between AND, OR and IMPLIES. Part of this was preregistered (families in M2); the rest is exploratory.
5. **Uncertainty-of-answer estimators read a confident abstention as certainty.** Examples: Mistral in Test M, W ≈ 0.30; M1-MSP on Qwen in Test C. This is an observation; the mechanism is an interpretation.

## What has not been shown

- That any method detects hallucinations with context. In Test C, HC4 within B could not be evaluated (0 errors on B), and HC4 within C is confounded with the passage family.
- That the results hold outside 4 open-weights models of 7–12B, English and template texts.
- That p(UNKNOWN) works in symbolic formats: there it is weak or reversed (Test U, Test U2).
- Anything about the four new small models. SmolLM2 answered only 92/240 B cases correctly and never generated NO, so the study is not evaluable. Qwen2.5-0.5B lacks its aggregate report. TinyLlama stopped because its tokenizer shares first tokens between the labels: this is a limit of the measurement, not a result about the model.

## Reproducibility already verified

- The original W, ΔW and confidence intervals of Test C (508 values), Test M notebook A (498) and notebook B (176) are recomputed from the archived per-row scores with **0 differences**. Use `python -m indetbench.replay` with the original ZIPs (SHA-256 in [`REPRODUCIBILITY_STATUS.md`](REPRODUCIBILITY_STATUS.md)).
- From the archived Test M reference scores, `python -m indetbench.original_benchmark report` gives the published Test U2 point estimates (0.975, 0.783, 0.694, 0.746) and the per-family values of Test M. Its bootstrap intervals agree to about ±0.004.
- All 12 pinned model and dataset revisions exist on the Hugging Face Hub and match ([`hf_revisions_verified.json`](../research_originals/hf_revisions_verified.json)).

## Known limits

- Single human reviewer for semantics and for the answer classifier; classifier agreement 0.68 (Test C).
- The reference p(UNKNOWN) is close to 1 in Test C, so an advantage of other methods could not have been seen there.
- Many comparisons without multiplicity correction; the 3-of-4 rule mitigates but does not solve this.

To check these results on another model, follow [`VERIFY_ON_NEW_MODELS.md`](VERIFY_ON_NEW_MODELS.md). For new models it adds a binding competence gate, fixed on 14 November 2026 before any new-model data: accuracy ≥ 0.50 on the determined B cases. The original protocols had no such gate; all four original models pass it.
