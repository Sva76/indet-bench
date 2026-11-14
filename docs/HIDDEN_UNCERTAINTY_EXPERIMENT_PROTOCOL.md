# Pre-answer hidden states — protocol v2 (DRAFT, awaiting owner approval)

Status: **design only; no inference, no result.** The endpoint and criteria in §5 are **proposals** to be approved by the owner before any data are generated. This replaces v1, which did not take Step 1 into account and set an unapproved primary endpoint (+0.03 AUROC). Italian master copy: `PHI/Step3_libreria/Protocollo_stati_interni_v2_bozza.md` (owner's project files).

## 1. What is already known (Step 1, Tests 4–7; `research_originals/step1/Riepilogo_Step1.md`, approved v3)
| Test | Result |
|---|---|
| 4 | A detector built on SQuAD works on SQuAD (3 models) but does not separate C from B on the stories (AUROC 0.46–0.57); it reacts to the surface form "x = a or b". |
| 5 | In domain, the probe separates C from B (W 0.975 Qwen3-8B, 0.983 Mistral-Nemo) and beats the output regression (ΔW +0.142, +0.083). A post-hoc output regression by family × variant orders 120/120 pairs without hidden states. |
| 6 | No transfer to new operators (W 0.50 Qwen, 0.44 Mistral; sign flips by operator). Raw p(UNKNOWN) 0.901 and 0.828. |
| 7 (exploratory) | Criterion for Test 8 not met: 1 round of 6 passes (Qwen, ADD + V1 → prose), not replicated on Mistral. No common direction (cosine ~0 between trainings sharing no stories). Raw p(UNKNOWN) is the strongest reference in 4 of 6 rounds. |

Step 2 adds: no published method (LM-Polygraph, SIRIN, zero-shot judge, Obeso et al. probes) showed a replicated advantage over p(UNKNOWN); the M4-LoRA exception on Llama in Test M did not replicate in Test C.

**Consequence.** Whether hidden states carry information about indeterminacy is already answered: yes, in domain. The open question is whether they give a **transferable advantage over p(UNKNOWN) and the other output measures on formulations never seen**. This is the Test 8 foreseen by Test 7 and not run because its entry criterion was not met.

## 2. Hypothesis
H-S1 (primary): on formulations never used in any previous test, the detector U1 + states orders C above B within the pair better than **each** output reference (U1, U2, raw p(UNKNOWN)), by the criterion of §5. Given Tests 6–7 the expected outcome is negative; the test confirms or refutes it on new data with rules fixed in advance.

## 3. Data
- Minimal B/C pairs as in Test 5: same story, same uncertain line, only the value of another variable changes; two rule versions (with and without NOT) so that value alone does not predict the label.
- **New formulations**, chosen and frozen before inference (§8), different from ADD, V1, V2, V3, POL and from Tests U, U2, M, C. Training: ADD + V1 + V2. Verification: new formulations only, looked at once.
- Token check per model: B and C of the same version have the same token count; exclusions counted by family, position and version; zero exclusions allowed in the main verification, otherwise stop before inference.
- Generator seed, version and SHA-256 frozen; human spot check before the run.
- The 240 pairs `smol_stat_v01` are **not** used (generated outside the protocols, no human validation).

## 4. Measurements (as in Tests 5–7)
- State: last prompt token after the chat template (`enable_thinking=False` for Qwen), all grid layers (every 4th plus the last). No generated token enters the input.
- Probe: standardisation and 64-component PCA inside folds, L2 logistic regression C = 1; layer chosen by 5-fold group CV by story; B/C pairs only (C = 1).
- Output references, without family or variant: U1 (logistic regression on log p(YES), log p(NO), log p(UNKNOWN)), U2 (with quadratic terms), **raw p(UNKNOWN)** (untrained).
- Detector: U1 + probe score (out of fold with nested CV on training).
- Primary metric: paired within-story W (ties = 0.5), comparable with all previous tests. Story bootstrap, 2000 paired resamples; permutation in "probe" mode (only the probe is retrained with labels swapped by story).
- Alignment gate: from the new states, rebuild the Test 6 probe (ADD → V2) on Qwen and Mistral: same layer, Spearman > 0.999, W within 0.005; otherwise stop.

## 5. Criterion (PROPOSAL: Test 7 criterion, unchanged)
Fixed before data in Test 7 for exactly this test; reused without changes so that no new threshold is chosen:
- on **both** Qwen3-8B and Mistral-Nemo, on the new formulations:
  - against **each** reference, ΔW = W(U1 + states) − W(R) has bootstrap lower bound > 0 and exceeds the 97.5th permutation percentile;
  - against the **strongest** reference (point estimate), ΔW ≥ 0.05;
  - no cell (operator × version × position) with W of U1 + states < 0.40.
- If not met: "on new formulations the transferable advantage of hidden states over outputs was not confirmed under the fixed criterion". Method, layer and threshold are not changed after seeing data.

## 6. Descriptive only
AUROC C vs B without pairing, AUPRC, calibration; generated answers on B and C; C cases answered YES/NO with low p(UNKNOWN) vs matched B; W by layer and by cell; direction cosines as in Test 7; output regression by family × variant (Test 5 lesson), descriptive because unavailable on unseen formulations.

## 7. Models
Qwen3-8B (`b968826`) and Mistral-Nemo-Instruct-2407 (`04d8a90`), as in Tests 5–7. Step 1 entry rule: a model enters only if it confirms H5a (in-domain probe). OLMo-2-7B and Llama-3.1-8B afterwards under the same rule; reported separately, they do not change the primary criterion.

## 8. Owner decisions required before data
1. Primary criterion = Test 7 criterion unchanged?
2. Which new formulations (proposal: two, one symbolic with a different structure and one prose with vocabulary different from V2), and how many stories (proposal: 200 each).
3. 500 permutations as in Test 5 (confirmatory) instead of 200 (Test 7, exploratory)?
4. Run it although Test 7's entry criterion was not met (proposal: yes, declared as a confirmation test of the Test 7 result in either direction).

## 9. Technical work after approval
`src/indetbench/hidden_uncertainty.py` stores one layer per call; it must be extended to the layer grid and to the Test 5 coherence checks (identical prefix tokens, relative L2 distance < 2%). The generator must be written and dry-run tested before any inference.
