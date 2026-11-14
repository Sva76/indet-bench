# IndetBench

**A reproducible benchmark and validation protocol for answer determinability in language models.**

> **Status: public, development / pre-alpha.** The repository now includes CPU archive replay for **Test C** and **Test M notebooks A and B**, plus an experimental Hugging Face model runner. Full U/U2 replay, HC4 validation, method-card/release checks and broader model compatibility are still pending. The Hugging Face runner has been run on CPU on six small external models (SmolLM2-360M, SmolLM2-1.7B, Qwen2.5-0.5B, Qwen2.5-1.5B, OLMo-2-0425-1B, TinyLlama-1.1B) on the separate 240-pair set; only Qwen2.5-1.5B passes the competence gate, TinyLlama is not measurable (first-token collision), and all these results are exploratory ([status](docs/COMPETENCE_240_PAIRS.md)). This project does not certify hallucination detection.

## Research question

When a passage does or does not uniquely determine an answer, does an uncertainty estimator rank the underdetermined version above the determined version? We use paired variants **B** (answer determined) and **C** (answer not determined), and compare candidate methods to a simple, training-free first-generation-step `p(UNKNOWN)` reference.

IndetBench is **a benchmark and validation protocol, not a new uncertainty detector**. In the underlying experiments, no tested published method established a *replicated, generalizable* improvement over `p(UNKNOWN)` across the evaluated settings. An Obeso LoRA probe on Llama showed a positive result in Test M but did not replicate in Test C. This statement **does not** assert universal superiority of `p(UNKNOWN)`.

## Install locally (development)

```bash
python -m pip install -e .
python -m unittest discover -s tests -v
```

## First CPU-only evaluation

Use a CSV with columns `pair_id,block_id,side,score`; higher scores mean **greater predicted indeterminacy**. The `block_id` identifies the common story/passage for dependent variants.

```bash
python -m indetbench --scores examples/sample_scores.csv --reference examples/sample_reference.csv --bootstrap 2000
```

The command computes block-averaged W(C>B), ties worth 0.5, paired delta-W using **common complete pairs**, and block-bootstrap confidence intervals. The example files contain invented demonstration values, not actual experiment scores.

**Important:** the generic CSV CLI uses its own deterministic bootstrap; do not equate its confidence intervals automatically with the historical reports. The separate [archived-results replayer](docs/REPRODUCIBILITY_STATUS.md) follows the original NumPy bootstrap and was run on the original archives on 14 November 2026 and matched Test C (508 values), Test M notebook A (498) and notebook B (176) with 0 differences. See [Test your model](docs/RUN_YOUR_MODEL.md) for the Hugging Face runner, which has been run on CPU on six small external models (see the status note above).

## Scientific, licensing and AI transparency

- **[Scientific status](docs/SCIENTIFIC_STATUS.md)**: what the original research has and has not shown, with sources.
- **[Verify the results on a new model](docs/VERIFY_ON_NEW_MODELS.md)**: run the frozen original benchmark (800 prose B/C pairs) on any Hugging Face model and compare with the published values.
- [Development plan, acceptance and limits](docs/ROADMAP.md).
- [AI assistance disclosure](docs/AI_USAGE.md) — AI-assisted planning, coding, analysis and writing, with human oversight and documented limits.
- **[Related work](docs/RELATED_WORK.md)**: closest published work, what IndetBench adds and what it does not claim.
- [References and attribution](docs/REFERENCES.md) — verified core paper citations in [BibTeX](docs/REFERENCES.bib); model revisions and remaining references require further checks.
- [Third-party terms](docs/THIRD_PARTY.md) — per-model, library and dataset licensing.
- [License](LICENSE) — **PolyForm Noncommercial 1.0.0**, © 2026 Simona Vargiu, for original IndetBench material only ([NOTICE](NOTICE)). Noncommercial research use, modification and distribution are permitted; commercial use needs a separate written agreement. This is source-available, not OSI open source. Third-party models and datasets keep their own terms.

**No third-party model weights, training data, natural SQuAD passages, or proprietary probe files are distributed with this package.**

Copyright © 2026 Simona Vargiu.

## License

IndetBench original material (code, documentation, frozen prompt sets written for this project) is licensed under the **[PolyForm Noncommercial License 1.0.0](LICENSE)**, © 2026 Simona Vargiu; see [NOTICE](NOTICE) for the required notice.

- Allowed without asking: noncommercial use, including research at universities and public research organisations, modification and redistribution, provided the license text and the required notice are kept.
- Not allowed without a separate written agreement with the author: commercial use.
- It is source-available, not an OSI-approved open-source license.
- Third-party models, libraries and datasets are not covered and keep their own terms ([THIRD_PARTY.md](docs/THIRD_PARTY.md)); for example Llama 3.1 models need the Llama 3.1 Community License.

## Historical research archive — source material preserved

The owner's **original Step 1 and Step 2** research material is archived in [`research_originals/`](research_originals/README.md), separate from new Hugging Face synthetic studies. It includes original summaries, protocols, written results, two Test C notebooks, **seven exact historical generator/selection/verification scripts**, and frozen synthetic datasets from Test M and Test C compressed without changing their bytes.

The provenance and original-input SHA-256 values are in [`research_originals/manifest_originals.json`](research_originals/manifest_originals.json). The M-A and M-B original frozen inputs were checked to be identical. **This is a substantial partial recovery, not yet the entire historical research archive:** complete natural SQuAD-derived rows, several original U/U2 and Step 1 files, model-output ZIPs, environment captures and weights remain excluded pending byte access or rights review. The original full ZIPs are retained separately in the owner's private ChatGPT Library.

**The 240-pair `data/smol_stat_v01_frozen.jsonl` dataset was created for a separate experiment on 13 November 2026; it is NOT original Step 1 or Step 2 data.** It is covered by the root license as original IndetBench material.

## Reproduce frozen experiments without GPU

Install the NumPy-only optional analysis dependencies: `python -m pip install -e '.[replay]'`.

Given the original complete-results archives (not redistributed here):

```bash
python -m indetbench.replay /path/to/completo-20261113T082301Z-1-001.zip --kind C --expected-sha256 da84d9bfb81df8ef15c39524b9e507ffa13eb1e563ce18715b432a1638b5bbed --json-out testC_parity.json
python -m indetbench.replay /path/to/testM_A_risultati_completo.zip --kind M-A --expected-sha256 5f2922d73d3f8921600d082c92201975faea97cf3d078ab49e6ec51565661cbc --json-out testM_A_parity.json
python -m indetbench.replay /path/to/testM_B_risultati_completo.zip --kind M-B --expected-sha256 a78cf5a02566d22de80acf8fff6caff0fa0049c697abbbf27667b807648cea3a --json-out testM_B_parity.json
```

The replayer recomputes statistics from scores for individual pairs, rather than trusting the precomputed tables. [Exact scope and evidence](docs/REPRODUCIBILITY_STATUS.md). Test U/U2 replication and **HC4 annotation reliability** remain separate unfinished checks. The new Test M notebook A CLI is ready for validation against the full original ZIP.

## Test a new language model (experimental)

The first Hugging Face runner is now available as an **opt-in** feature. It loads an external causal LM under that model's own terms and scores user-authored B/C prompts without modifying the source model:

```bash
python -m pip install -e '.[hf]'
python -m indetbench.hf_runner --model-id Qwen/Qwen3-8B --revision YOUR_40_CHARACTER_COMMIT_SHA --model-key qwen --input examples/hf_pairs.jsonl --output my_scores.csv
python -m indetbench --scores my_scores.csv
```

Replace YOUR_40_CHARACTER_COMMIT_SHA with a commit hash from the model provider's official history. Only a fabricated demonstration pair is included. See [the input schema, first-token definition and limitations](docs/RUN_YOUR_MODEL.md). The runner's unit tests use a fake tokenizer. Beyond the first [CPU smoke test on SmolLM2-360M](docs/SMOLLM2_EXTERNAL_SMOKE.md), it has scored five more small models on CPU on the 240-pair set ([competence verdicts](docs/COMPETENCE_240_PAIRS.md)). Models of 7B and more are run from the Colab notebook in `notebooks/`; no result from that notebook is recorded in this repository yet. Semantic answer validation is still pending.

## External statistical evaluation — SmolLM2 (13 November 2026)

A preregistered 240-pair (480-inference) test on the external **SmolLM2-360M-Instruct** model found **no evidence** that its raw first-token `p(UNKNOWN)` reliably ranked underdetermined cases above determined cases: **W = 0.479** (95% bootstrap CI **0.417–0.546**), AUROC **0.501**. The exact two-sided sign-test p-value is **0.561**, independently recomputed after correcting a NumPy integer-overflow bug in the first archived report.

**Interpretation gate failed:** SmolLM2 answered only **92/240 answerable B cases correctly (38.3%)**, never generated `NO` on B or C, and abstained correctly in only 68/240 C cases. The software calculation is reproducible, but the model did not demonstrate the prerequisite task competence: the result is **not scientifically evaluable as an uncertainty-detector validation**, despite the descriptive W/AUROC values. Formatting and prompt-length effects are unresolved confounds, so this **cannot** be interpreted as epistemic detection, proof of generalization or a new model capability.

See [preregistered protocol](docs/SMOLLM2_STAT_STUDY_PREREG.md), [original model scores, statistical results and correction](docs/SMOLLM2_STAT_STUDY_RESULTS.md), and [closest 2018–2026 scientific precedents](docs/NOVELTY_AND_RELATED_WORK_2026.md). IndetBench is **not** the first or broadest benchmark on abstention and uncertainty.
