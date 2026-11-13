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
| Accuracy on determined B cases, by family | `report.json` → `behaviour` | Descriptive flag below 0.80, as HC0-set in Test C. The original protocols of Tests U2/M had **no** competence gate on B. For reference, P−S accuracy on B was Qwen 1.00, Llama 0.94, OLMo 0.79 and Mistral 0.57; Mistral would have failed a 0.80 gate. A gate for new models is a protocol decision that must be fixed before the data; it is not yet fixed. |
| Primary result | `W_p_unknown` | As in Test U/U2 (HU1, HI1): **confirmed** if W ≥ 0.60 and the lower bound of the 95% interval is above 0.5; **not confirmed** if the upper bound is at or below 0.5; otherwise **not conclusive**. |
| Families | `W_by_family_descriptive` | Descriptive only. In the original models W varied strongly by family. |

## Comparison with the published values

`report.json` lists the published Test U2 values for P−S, with 95% intervals: Qwen3-8B 0.975 [0.964, 0.985], Mistral-Nemo 0.783 [0.751, 0.811], OLMo-2 0.694 [0.651, 0.735] and Llama-3.1-8B 0.746 [0.704, 0.785].

Running one of these four models again at its pinned revision should give a close value. Exact equality is not expected. The original runs used bfloat16 weights, eager attention and the package versions recorded in the archives. `hf_runner` uses the model's default dtype and attention on GPU, and float32 on CPU. The `report` bootstrap also differs slightly from the original one: on the archived scores the point estimates are identical and the intervals agree to about ±0.004.

## What a result on a new model can and cannot show

- A confirmed W supports the original finding for that model, in this prose format only.
- A not-confirmed W on a model that answers the determined cases correctly is evidence against generalisation to that model.
- A not-confirmed W on a model that fails the determined cases, or never generates a label, tells nothing about the method.
- None of these results bears on hallucination detection with context, which remains unshown (see [`SCIENTIFIC_STATUS.md`](SCIENTIFIC_STATUS.md)).
