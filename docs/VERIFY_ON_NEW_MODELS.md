# Verifying the results on a new model

This procedure lets a researcher check the main original result on a model of their choice: **p(UNKNOWN) ranks C above B on the frozen prose benchmark**. It reuses the prompts of Tests U2 and M unchanged.

## Order of the datasets

1. **Primary: the original frozen benchmark** (`research_originals/step2/frozen/M_Original_4800_righe.json.gz`, SHA-256 checked by the code). Use set `PN`: prose without the explanatory sentence, 800 B/C pairs, 200 stories, 3 families. This is the only dataset on which results can be compared with the published ones.
2. **Secondary: the 240-pair set** (`data/smol_stat_v01_frozen.jsonl`). Use it only after a documented human review of its labels and a control for prompt length; prompt length alone gives W 0.583 on SmolLM2.
3. **Exploratory:** any other new set, reported separately.

## Steps

```bash
python -m pip install -e '.[hf,replay]'
python -m indetbench.original_benchmark export --set PN --output original_PS.jsonl
python -m indetbench.hf_runner --model-id ORG/MODEL --revision FULL_40_CHAR_SHA \
    --model-key other --input original_PS.jsonl --output scores.csv --max-new-tokens 8
python -m indetbench.original_benchmark report --scores scores.csv > report.json
```

Use `--model-key qwen` for Qwen3 models, which turns thinking off as in the original runs. Write the model ID, the revision and your analysis rules down **before** running.

## Checks to apply, and how to read them

| Check | Where | Rule |
|---|---|---|
| Score file | `report` | Refused if a row is not a B/C row of the frozen benchmark, appears twice, has `pair_id`, `block_id` or `side` different from the frozen row, or if the file mixes subsets or, when `model_id` and `model_revision` are present, models. Fewer than 760 complete pairs give a DESCRIPTIVE outcome (`coverage`). See [Protocol §5](PROTOCOL.md#5-decision-rules-set-pn). |
| Tokenizer labels | `hf_runner` | The runner stops if YES, NO and UNKNOWN share a first token (TinyLlama does). Then p(UNKNOWN) is not defined for that model: report it as *not measurable*, not as a negative result. |
| All three labels generated | `report.json` → `warnings` | A model that never generates one of the labels (SmolLM2 never said NO) is flagged. |
| **Competence gate (binding)** | `report.json` → `competence_gate`, `verdict` | Accuracy of the generated answer on the 800 B cases must be **≥ 0.50 overall and separately on the 532 B cases with gold YES and on the 268 with gold NO**. If any part fails, the result is **NOT EVALUABLE** (`failed_parts` says which). See the section below. |
| Accuracy on B by family | `report.json` → `behaviour` | Descriptive only. (Accuracy by gold label is part of the gate.) |
| Primary result | `W_p_unknown` | As in Test U/U2 (HU1, HI1): **confirmed** if W ≥ 0.60 and the lower bound of the 95% interval is above 0.5; **not confirmed** if the upper bound is at or below 0.5; otherwise **not conclusive**. |
| Families | `W_by_family_descriptive` | Descriptive only. In the original models W varied strongly by family. |

## Competence gate on the determined cases

**Rule.** For a new model, the primary result on the prose set is evaluated only if the model's generated answer on the determined B cases is correct

1. on at least **50% of all 800 B cases**, and
2. on at least **50% of the B cases with gold answer YES** (532 cases: OR and IMPLIES families), and
3. on at least **50% of the B cases with gold answer NO** (268 cases: AND family).

All thresholds are inclusive. If any part fails, `report` returns `NOT EVALUABLE` whatever the value of W, and `competence_gate.failed_parts` lists the failed parts (`overall`, `YES`, `NO`). A gold label with no B rows in the scores counts as failed, because the gate cannot be checked on it. Accuracy per family is reported but does not decide.

Parts 2 and 3 imply part 1, since the overall accuracy is a weighted mean of the two per-label accuracies. Part 1 is kept and reported because it was fixed first and is the figure readers expect.

**When and by whom.** The project owner fixed this rule on 14 November 2026, before running the benchmark on any new model. Part 1 was fixed first; parts 2 and 3 were added the same day, also before any new-model data on this benchmark, after the limit described below was found.

**Not in the original protocols.** Tests U, U2 and M had no competence gate on B, neither overall nor by gold label. The rule does not change any original result: all four original models pass all three parts.

| Original model (P−S, archived runs) | Accuracy on B (800) | on gold NO (268, AND) | on gold YES (532, OR + IMPLIES) | W of p(UNKNOWN) | Verdict |
|---|---|---|---|---|---|
| Qwen3-8B | 1.000 (800) | 1.000 (268) | 1.000 (532) | 0.975 | CONFIRMED |
| Llama-3.1-8B-Instruct | 0.943 (754) | 0.978 (262) | 0.925 (492) | 0.746 | CONFIRMED |
| OLMo-2-1124-7B-Instruct | 0.792 (634) | 1.000 (268) | 0.688 (366) | 0.694 | CONFIRMED |
| Mistral-Nemo-Instruct-2407 | 0.570 (456) | 0.690 (185) | 0.509 (271) | 0.783 | CONFIRMED |

Numbers in brackets are correct answers. These values are recomputed by `report` from the archived per-row scores of Test U2 (set PN), which the Test M reference reproduces exactly; the counts are stored in `REFERENCE_B_ACCURACY_BY_GOLD_PS`.

Mistral-Nemo passes the gold-YES part by a small margin: 271 correct where 266 are needed (0.509 against 0.500). This is stated here because the margin is five cases. Its IMPLIES family alone is at 0.420; families are not part of the gate, so this stays descriptive.

**Why 0.50 and not 0.80.**
- A 0.80 gate, the descriptive flag of Test C, would have excluded Mistral (0.57). Yet Mistral's p(UNKNOWN) separates C from B (W 0.783).
- The purpose of the gate is to exclude models that do not perform the task at all. SmolLM2-360M is one: 0.38 on B, and it never answered NO. That figure comes from the separate 240-pair set, not from this benchmark.

**Why the per-label parts (2 and 3).** The B cases are not balanced by answer: 532 have gold YES (OR and IMPLIES families) and 268 gold NO (AND family). With part 1 alone, a model that always answers YES would reach 532/800 = 0.665 and pass, although it does not discriminate between YES and NO at all. Requiring ≥ 0.50 on each gold label separately excludes any constant answer: always YES gives 0.000 on gold NO, always NO gives 0.000 on gold YES. The threshold is the same 0.50 as part 1, so no new free parameter is introduced.

**What the gate does not do.** It sets no threshold per family, and it does not look at the C cases. A model can still pass with weak discrimination (for example 0.50 on each label). The gate only excludes models that do not perform the determined task; it is not a quality ranking.

## Comparison with the published values

`report.json` lists the published Test U2 values for P−S, with 95% intervals: Qwen3-8B 0.975 [0.964, 0.985], Mistral-Nemo 0.783 [0.751, 0.811], OLMo-2 0.694 [0.651, 0.735] and Llama-3.1-8B 0.746 [0.704, 0.785].

Running one of these four models again at its pinned revision should give a close value. Exact equality is not expected. The original runs used bfloat16 weights, eager attention and the package versions recorded in the archives. `hf_runner` uses the model's default dtype and attention on GPU, and float32 on CPU. The `report` bootstrap also differs slightly from the original one: on the archived scores the point estimates are identical and the intervals agree to about ±0.004.

## Results so far

First exploratory run with this procedure (14 November 2026): [`NEW_MODELS_RESULTS_2026-11-14.md`](NEW_MODELS_RESULTS_2026-11-14.md). It also shows a case the rule above does not catch: a model can pass the gate and get CONFIRMED while its YES/NO/UNKNOWN probability mass at the first token is near zero (Yi-1.5-9B-Chat); the owner classified it as NOT EVALUABLE for a technical reason. The notebook flags low label mass only as a caution; it does not change the verdict, so read that flag before reading W.

## What a result on a new model can and cannot show

- A confirmed W supports the original finding for that model, in this prose format only.
- A not-confirmed W on a model that answers the determined cases correctly is evidence against generalisation to that model.
- A model below the competence gate, in any of its parts, is NOT EVALUABLE: its W tells nothing about the method. A model that never generates YES or NO on B fails the per-label part; one that never generates UNKNOWN is flagged by a warning.
- None of these results bears on hallucination detection with context, which remains unshown (see [`SCIENTIFIC_STATUS.md`](SCIENTIFIC_STATUS.md)).
