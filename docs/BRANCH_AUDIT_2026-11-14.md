# Repository audit of all branches and pull requests (2026-11-14)

Scope: read-only audit of the seven branches and four pull requests of `Sva76/indet-bench`, plus the technical fixes made on `claude/correzioni-tecniche-verifica`. No dataset, hypothesis, threshold, scoring rule or statistical rule was changed. Items that touch the method are listed as **open questions for the owner**, not fixed.

Labels: **CONFIRMED** = preregistered result of the original Step 1–2 work; **EXPLORATORY** = new runs without a protocol approved by the owner; **IN PROGRESS** = not finished; **NOT MEASURED** = the measurement was not obtained.

## Branches and pull requests

| Branch | Content | Unit tests (local, Python 3.13) |
|---|---|---|
| `main` | README only | – |
| `feature/initial-cpu-metrics` (PR #1 → main, draft) | package, replay, SmolLM2-360M study, archive | 22 OK |
| `claude/archivio-versioni-approvate` (PR #2 → feature, draft) | approved document versions | 22 OK |
| `claude/verifica-modelli-nuovi` (PR #3 → feature, draft) | scientific status, competence gate, Colab notebook v3 (PR #4 merged here) | 35 OK |
| `claude/notebook-modelli-nuovi` | head of PR #4 (merged) | – |
| `fix/qwen-tinyllama-validation` | CPU runs on the 240-pair corpus | 22 OK |
| `experiment/hidden-uncertainty-probe` | hidden-state extraction design + smoke test | 22 OK (+3 fixture tests in their own workflow) |

CI gap (fixed here): `ci.yml` and `security.yml` ran on pull requests into `main` only, so PR #2 and PR #3 never ran the unit tests in CI.

## Per experiment

### Original Steps 1–2 (Test U, U2, M A/B, C) — CONFIRMED
- Reproducible: the committed replay CLI was run on the original archives on 2026-11-14: Test C 508 values (both exports), M-A 498, M-B 176, **0 differences** (see `REPRODUCIBILITY_STATUS.md`).
- Missing: Test U/U2 numeric replay is not implemented; HC4 is not revalidated by the replay.

### SmolLM2-360M on the 240-pair corpus — NOT EVALUABLE (as documented)
- B accuracy 92/240, never answers NO: the competence condition fails; this is not a negative result about the method.

### Qwen2.5-0.5B, Qwen2.5-1.5B, OLMo-2-0425-1B, SmolLM2-1.7B on the 240-pair corpus — EXPLORATORY
Unchanged analyzer, 480 rows, 240 pairs (B gold: 120 YES, 120 NO), pinned revisions, dataset SHA-256 checked. Run 43607866659 of `reanalyze-archived-cpu-scores.yml` (this branch) re-analysed the existing raw scores; no new inference.

| Model | Scores from run | W [95% CI] | sign p | AUROC | B accuracy | B answers YES/NO/UNKNOWN | C abstention |
|---|---|---|---|---|---|---|---|
| Qwen2.5-0.5B | 43579643007 | 0.592 [0.529, 0.654] | 0.0054 | 0.513 | 0.625 | 52 / 173 / 15 | 0.058 |
| Qwen2.5-1.5B | 43582196401 | 0.613 [0.550, 0.671] | 0.0006 | 0.617 | 0.679 | 117 / 93 / 30 | 0.229 |
| OLMo-2-0425-1B | 43582196401 | 0.579 [0.517, 0.642] | 0.0167 | 0.549 | 0.237 | 52 / 19 / 169 | 0.725 |
| SmolLM2-1.7B | 43582196401 | 0.579 [0.517, 0.642] | 0.0167 | 0.548 | 0.021 | 5 / 0 / 235 | 0.983 |

- Reproducibility: Qwen2.5-1.5B, OLMo-1B and SmolLM2-1.7B were inferred independently up to three times (runs 43582014175, 43582196401 and 43609915878, the last started automatically by the merge into `feature/initial-cpu-metrics`). **W and the sign-test p are identical in every run.** AUROC differs slightly between runs: Qwen2.5-1.5B 0.6174826 / 0.6174653 / 0.6174826; OLMo-1B 0.5494792 / 0.5494792 / 0.5494965; SmolLM2-1.7B 0.5482813 in both runs that completed. *Correction:* an earlier version of this page said that AUROC was also identical; that was wrong.
  Anomaly class: **technique**. Probable cause, not verified: CPU floating-point differences between runner machines change a few p(UNKNOWN) values in the last digits. That is enough to move the global AUROC ranking by at most 2e-5, but not the within-pair ordering, so W does not change. Per-row scores could not be compared from this environment (the artifact download is blocked), so this cause remains a hypothesis.
- SmolLM2-1.7B answers UNKNOWN to 235/240 determined cases and OLMo-1B to 169/240: as for SmolLM2-360M, a W above 0.5 cannot be read as uncertainty detection when the model does not answer the determined cases. Qwen2.5-0.5B answers YES at most 52 times out of 120 YES cases, so its YES accuracy is at most 0.43.
- No competence condition is applied by the 240-pair analyzer; the corpus has no independent human validation. Whether the owner's condition (B accuracy ≥ 0.50 overall and per gold label, fixed for the 800 original pairs) applies here is an open question below. Per-label accuracy for Qwen2.5-1.5B needs the per-row scores.
- SmolLM2-1.7B history: in run 43582014175 shards 1–2 were stopped by a runner shutdown signal (infrastructure); in run 43582196401 all shards succeeded but the `analyze` matrix of `hf-crossmodel-stat.yml` still listed `qwen05, tinyllama11`, so no report was made. **Fixed** (matrix aligned).

### TinyLlama-1.1B — NOT MEASURED
- First tokens of YES/NO/UNKNOWN overlap; the runner correctly refuses. Applicability limit of the first-token measurement, not a result about the model.

### Hidden-state experiment (`experiment/hidden-uncertainty-probe`) — EXPLORATORY, NOT CONTINUED (owner's decision, 2026-11-14)
- Not run: Step 1 Tests 6–7 already showed that probes do not transfer; protocol v2 is archived as a record. Nothing deleted.
- Done: extraction of the last-prompt-token state and output baselines; smoke test on 2 pairs with Qwen2.5-0.5B (4 rows, finite values). No scientific result.
- **Fixed defect**: `--model-key auto` (the default) was passed unchanged to the chat template, so Qwen3 would have been rendered with thinking enabled, unlike every archived run. Now resolved exactly as in `hf_runner.score_pairs`; 3 unit tests added.
- Open questions for the owner (method, not fixed): see below.

## Open questions for the owner (not changed)
1. The hidden-state protocol does not cite Step 1 (Tests 4–7), which already probed pre-answer hidden states on B/C pairs (Test 4 on Qwen3-8B, Mistral-Nemo and OLMo-2-7B; Tests 5–7 on Qwen3-8B and Mistral-Nemo; `research_originals/step1/Riepilogo_Step1.md`) and found in-domain signal without transfer. Its primary endpoint (+0.03 AUROC) was not approved by the owner. **Update:** at the owner's request, protocol v2 (draft) now builds on Tests 4–7; endpoint and criteria await approval.
2. ~~Whether the competence condition applies to the 240-pair corpus.~~ **Decided 2026-11-14:** the 0.50 rule is binding; a 1/3 chance threshold is reported as a theoretical sensitivity only. See `COMPETENCE_240_PAIRS.md`: only Qwen2.5-1.5B is evaluable; SmolLM2-1.7B and OLMo-1B fail under both thresholds.
