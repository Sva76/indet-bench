# IndetBench

**A reproducible benchmark and validation protocol for answer determinability in language models.**

When a passage does or does not uniquely determine an answer, does an uncertainty estimator rank the underdetermined version above the determined one? IndetBench uses paired variants **B** (answer determined) and **C** (answer not determined) and compares candidate methods with a simple, training-free reference: the first-token probability `p(UNKNOWN)`. It is **a benchmark and validation protocol, not a new uncertainty detector**, and it does not certify hallucination detection.

> **Status: public, development / pre-alpha.** Still pending: Test U/U2 replay, HC4 validation, human semantic review of the 240-pair set, broader model compatibility, a tagged release. See [Scientific status](docs/SCIENTIFIC_STATUS.md) and [Roadmap](docs/ROADMAP.md).

## Quickstart

```bash
python -m pip install -e '.[hf,replay]'
python -m unittest discover -s tests -v

# Run the frozen original benchmark (800 prose B/C pairs) on a Hugging Face model
python -m indetbench.original_benchmark export --set PN --output original_PN.jsonl
python -m indetbench.hf_runner --model-id ORG/MODEL --revision FULL_40_CHAR_SHA \
    --model-key other --input original_PN.jsonl --output scores.csv --max-new-tokens 8
python -m indetbench.original_benchmark report --scores scores.csv > report.json
```

Use `--model-key qwen` for Qwen3 (thinking off, as in the original runs) and a 40-character commit hash from the model provider's history as revision. The report gives W of `p(UNKNOWN)` with a 95% interval, the binding competence gate and the verdict. Full procedure and how to read it: [Verify the results on a new model](docs/VERIFY_ON_NEW_MODELS.md). Your own B/C pairs: [Test your model](docs/RUN_YOUR_MODEL.md). Scores from any method, as a CSV `pair_id,block_id,side,score` (higher = more indeterminate; `block_id` = story): `python -m indetbench --scores my_scores.csv --bootstrap 2000` (demo files in `examples/`, invented values). This generic CLI uses its own deterministic bootstrap, so its intervals are not automatically comparable with the historical reports; the archive replayer below follows the original one.

## Main results

W = share of pairs in which C scores above B, averaged within stories (ties count one half).

| Setting | Model | W of p(UNKNOWN) [95% CI] | Status |
|---|---|---|---|
| Test U2, prose, 800 pairs (original) | Qwen3-8B | 0.975 [0.964, 0.985] | preregistered, confirmed |
| | Mistral-Nemo-Instruct-2407 | 0.783 [0.751, 0.811] | preregistered, confirmed |
| | Llama-3.1-8B-Instruct | 0.746 [0.704, 0.785] | preregistered, confirmed |
| | OLMo-2-1124-7B-Instruct | 0.694 [0.651, 0.735] | preregistered, confirmed |
| Same benchmark, new families (14 Nov 2026) | Phi-4 | 0.944 [0.924, 0.963] | exploratory |
| | Falcon3-7B-Instruct | 0.931 [0.911, 0.950] | exploratory |
| | Gemma-2-9B-it | 0.818 [0.788, 0.848] | exploratory |
| | Yi-1.5-9B-Chat | – | not evaluable (technical: label mass ≈ 0 at the first token) |

- **Published methods (Tests M and C, preregistered):** no tested method (LM-Polygraph estimators, SIRIN probe and judge, Obeso et al. probes) showed a *replicated* improvement over `p(UNKNOWN)`. The one positive case, an Obeso LoRA probe on Llama in Test M, did not replicate in Test C. This does **not** mean that `p(UNKNOWN)` is universally better.
- **Not specific, so far:** on the new models, generic uncertainty from the same outputs (entropy, maximum probability) does about as well as `p(UNKNOWN)` and better on Gemma (descriptive). It is not shown that `p(UNKNOWN)` carries information specific to indeterminacy.
- **Limits:** prose format only (weak or reversed in symbolic formats); strong dependence on logical family and wording; the NOT variant is weaker in all new models (open question).
- **Small models (240-pair set, CPU, exploratory):** only Qwen2.5-1.5B passes the competence gate; SmolLM2-360M, SmolLM2-1.7B, Qwen2.5-0.5B and OLMo-2-1B fail it and are not evaluable; TinyLlama is not measurable ([verdicts](docs/COMPETENCE_240_PAIRS.md), [SmolLM2-360M study](docs/SMOLLM2_STAT_STUDY_RESULTS.md)).

Details and sources: [Scientific status](docs/SCIENTIFIC_STATUS.md), [new-model report](docs/NEW_MODELS_RESULTS_2026-11-14.md), [Related work](docs/RELATED_WORK.md).

## Reproducibility

- **Archived results, CPU only:** `python -m indetbench.replay` recomputes the original statistics from per-row scores. On 14 November 2026 it matched Test C (508 values), Test M notebook A (498) and notebook B (176) with **0 differences**. The archives are not public; their SHA-256 values are published so that any copy can be checked ([commands and evidence](docs/REPRODUCIBILITY_STATUS.md)).
- **New-model run:** per-row scores, reports and manifests are in [`results/new_models_2026-11-14/`](results/new_models_2026-11-14/); a unit test recomputes W, gate and verdict from them.
- **Original research material** (Step 1 and Step 2 protocols, reports, generator scripts, frozen datasets): [`research_originals/`](research_originals/README.md), with provenance and SHA-256 in its manifest. It is a partial recovery: what is missing and why is listed there.
- **Data:** the 800-pair benchmark is frozen in `research_originals/step2/frozen/` (SHA-256 checked by the code). `data/smol_stat_v01_frozen.jsonl` (240 pairs, 13 November 2026) was made for a separate experiment and is not original Step 1–2 data.

## Documentation

- [Scientific status](docs/SCIENTIFIC_STATUS.md) · [Verify on a new model](docs/VERIFY_ON_NEW_MODELS.md) · [Test your model](docs/RUN_YOUR_MODEL.md) · [Reproducibility](docs/REPRODUCIBILITY_STATUS.md)
- [Related work](docs/RELATED_WORK.md) (IndetBench is not the first or broadest benchmark on abstention and uncertainty; [2018–2026 precedents](docs/NOVELTY_AND_RELATED_WORK_2026.md)) · [References](docs/REFERENCES.md) ([BibTeX](docs/REFERENCES.bib)) · [Roadmap](docs/ROADMAP.md)
- [Use of AI tools](docs/AI_USAGE.md): research conceived and directed by the author; all Python code generated to her specifications by AI tools (ChatGPT; Claude Opus 5.5 via Claude Code) and validated by execution. Limits of the checks are stated.
- [Third-party terms](docs/THIRD_PARTY.md) · [Security](SECURITY.md) · [Citation](CITATION.cff)

**No third-party model weights, training data, natural SQuAD passages, or proprietary probe files are distributed with this package.**

## License

IndetBench original material (code, documentation, frozen prompt sets written for this project) is licensed under the **[PolyForm Noncommercial License 1.0.0](LICENSE)**, © 2026 Simona Vargiu; see [NOTICE](NOTICE) for the required notice.

- Allowed without asking: noncommercial use, including research at universities and public research organisations, modification and redistribution, provided the license text and the required notice are kept.
- Not allowed without a separate written agreement with the author: commercial use.
- It is source-available, not an OSI-approved open-source license.
- Third-party models, libraries and datasets are not covered and keep their own terms ([THIRD_PARTY.md](docs/THIRD_PARTY.md)); for example Llama 3.1 models need the Llama 3.1 Community License.

Copyright © 2026 Simona Vargiu.
