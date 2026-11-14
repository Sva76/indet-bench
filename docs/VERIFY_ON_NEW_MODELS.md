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
| Tokenizer labels | `hf_runner` | The runner stops if YES, NO and UNKNOWN share a first token (TinyLlama does). Then p(UNKNOWN) is not defined for that model: report it as *not measurable*, not as a negative result. |
| All three labels generated | `report.json` → `warnings` | A model that never generates one of the labels (SmolLM2 never said NO) is flagged. |
| **Competence gate (binding)** | `report.json` → `competence_gate`, `verdict` | Accuracy of the generated answer on all 800 B cases must be **≥ 0.50**. Below it the result is **NOT EVALUABLE**. See the section below. |
| Accuracy on B by family and by gold label | `report.json` → `behaviour`, `competence_gate.accuracy_B_by_gold` | Descriptive only. |
| Primary result | `W_p_unknown` | As in Test U/U2 (HU1, HI1): **confirmed** if W ≥ 0.60 and the lower bound of the 95% interval is above 0.5; **not confirmed** if the upper bound is at or below 0.5; otherwise **not conclusive**. |
| Families | `W_by_family_descriptive` | Descriptive only. In the original models W varied strongly by family. |

## Competence gate on the determined cases

**Rule.** For a new model, the primary result on the prose set is evaluated only if the model's generated answer is correct on at least **50% of the 800 determined B cases**. Below that threshold, `report` returns `NOT EVALUABLE` whatever the value of W. Accuracy per family and per gold label is reported, but it does not decide.

**When and by whom.** The project owner fixed this rule on 14 November 2026, before running the benchmark on any new model.

**Not in the original protocols.** Tests U, U2 and M had no competence gate on B. The rule does not change any original result: all four original models pass it.

| Original model (P−S, archived runs) | Accuracy on B | on gold NO (AND) | on gold YES (OR, IMPLIES) | W of p(UNKNOWN) | Verdict |
|---|---|---|---|---|---|
| Qwen3-8B | 1.000 | 1.000 | 1.000 | 0.975 | CONFIRMED |
| Llama-3.1-8B-Instruct | 0.943 | 0.978 | 0.925 | 0.746 | CONFIRMED |
| OLMo-2-1124-7B-Instruct | 0.792 | 1.000 | 0.688 | 0.694 | CONFIRMED |
| Mistral-Nemo-Instruct-2407 | 0.570 | 0.690 | 0.509 | 0.783 | CONFIRMED |

These values are recomputed by `report` from the archived Test M reference scores, which match Test U2 exactly.

**Why 0.50 and not 0.80.**
- A 0.80 gate, the descriptive flag of Test C, would have excluded Mistral (0.57). Yet Mistral's p(UNKNOWN) separates C from B (W 0.783).
- The purpose of the gate is to exclude models that do not perform the task at all. SmolLM2-360M is one: 0.38 on B, and it never answered NO. That figure comes from the separate 240-pair set, not from this benchmark.

**Known limit of the rule.** The B cases are not balanced by answer: 532 have gold YES (OR and IMPLIES families) and 268 gold NO (AND family). A model that always answers YES therefore reaches 0.665 and passes the gate. `report` makes this visible in two ways: `accuracy_B_by_gold`, and the warning `label never generated: NO`. Such a model must be described with that warning; the gate alone does not exclude it.

## Comparison with the published values

`report.json` lists the published Test U2 values for P−S, with 95% intervals: Qwen3-8B 0.975 [0.964, 0.985], Mistral-Nemo 0.783 [0.751, 0.811], OLMo-2 0.694 [0.651, 0.735] and Llama-3.1-8B 0.746 [0.704, 0.785].

Running one of these four models again at its pinned revision should give a close value. Exact equality is not expected. The original runs used bfloat16 weights, eager attention and the package versions recorded in the archives. `hf_runner` uses the model's default dtype and attention on GPU, and float32 on CPU. The `report` bootstrap also differs slightly from the original one: on the archived scores the point estimates are identical and the intervals agree to about ±0.004.

## What a result on a new model can and cannot show

- A confirmed W supports the original finding for that model, in this prose format only.
- A not-confirmed W on a model that answers the determined cases correctly is evidence against generalisation to that model.
- A model below the competence gate is NOT EVALUABLE: its W tells nothing about the method. The same holds, as a warning, for a model that never generates one of the labels.
- None of these results bears on hallucination detection with context, which remains unshown (see [`SCIENTIFIC_STATUS.md`](SCIENTIFIC_STATUS.md)).
