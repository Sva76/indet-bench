# Hidden uncertainty beyond verbal abstention — prospective experiment

Status: DESIGN ONLY; NO MODEL INFERENCE OR SCIENTIFIC RESULT YET.
Branch: experiment/hidden-uncertainty-probe. The frozen IndetBench corpus, original scores, main and PR branches must remain untouched.

## Question
Do pre-answer hidden states predict whether a question is *underdetermined by the supplied evidence*, even when the language model produces a confident YES/NO answer, beyond output-token probabilities and response behavior?

## Operational targets
Y=1: context is logically insufficient to determine YES or NO; Y=0: context logically determines a unique YES or NO. These are properties of the *evidence*, not whether the model says UNKNOWN or is factually correct. Separately flag confidently answered Y=1 cases using a frozen confidence rule defined before inspecting results. Do not conflate model errors with underdetermination.

## Data / splits
Generate a NEW, independently reviewed synthetic closed-world corpus with paired determined/underdetermined counterfactuals. Freeze seeds, generator version, SHA256, label rubric and blind human checks. Hold out entire reasoning families and lexical templates, not merely random prompts. Balance answer polarity, length, prompt style and lexical cues; keep each counterfactual pair in one split. Existing 240 B/C pairs are development-only, not a novel held-out test.

## Models
Pilot Qwen3-8B and Mistral-Nemo-Instruct-2407, then test OLMo-2-1124-7B-Instruct and Llama-3.1-8B-Instruct where permissions and GPU permit. Pin exact HF commit SHAs, inference software, random seeds, layer index and token position. Verify each model's tokenizer and chat template. Never silently replace models or methods.

## Measurements
Capture hidden activations at a fixed pre-answer position with forward hooks, without using generated answer tokens as input. Train a simple regularized linear probe on training families only; tune hyperparameters and choose layers only on validation families; lock choices before evaluating test families. Compare:
B0 majority/class-prior baseline;
B1 response category (YES/NO/UNKNOWN);
B2 first-token YES/NO/UNKNOWN probabilities;
B3 entropy, top-token margin, response confidence and prompt length;
B4 B1+B2+B3;
H hidden-state probe;
H+B4 combined.
For the crucial subset, report separately the underdetermined questions answered YES/NO with high output confidence, versus matched determined questions with the same answer and similar confidence. Prevent test-set selection or leakage.

## Primary endpoint and uncertainty
Primary endpoint: paired test-family AUROC improvement of H+B4 over B4, with a predeclared minimum meaningful improvement of 0.03 AUROC, cluster bootstrap CI by scenario/family, and family-level permutation test. Also report AUROC(H), AUROC(B4), AUPRC, calibration, confusion matrix, coverage and abstention, family-wise heterogeneity, and full negative results. A point estimate >0.03 is insufficient without uncertainty bounds. Model-wise claims are separate; any pooled claim requires a prespecified pooling rule.

## Integrity and interpretation
Assert exact sample counts, unique IDs, label balance, split disjointness, frozen hashes, absence of generated-answer leakage and paired completeness. Log GPU, versions, model SHA, output JSON and raw predictions as private artifacts. A positive result demonstrates additional *predictive information about evidence sufficiency* in hidden states under these controls; it does NOT establish conscious knowledge, deception, or a universal uncertainty signature. No claim until real model runs and artifacts are audited.

## Execution gates
1. Implement and unit-test dataset generator + blind audit sample.
2. Implement hidden-state extraction and output baselines.
3. Run tiny technical smoke test (not scientific evidence).
4. Freeze protocol and held-out split before full GPU execution.
5. Run, audit artifacts, and publish only after explicit authorization.
