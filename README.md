# IndetBench

**A reproducible benchmark and validation protocol for answer determinability in language models.**

> **Status: private development / pre-alpha.** The repository now includes CPU archive replay for **Test C** and **Test M notebooks A and B**, plus an experimental Hugging Face model runner. Full U/U2 replay, HC4 validation, method-card/release checks and broader model compatibility are still pending; a first external-model CPU inference smoke test has passed. This project does not certify hallucination detection.

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

**Important:** the generic CSV CLI uses its own deterministic bootstrap; do not equate its confidence intervals automatically with the historical reports. The separate [archived-results replayer](docs/REPRODUCIBILITY_STATUS.md) follows the original NumPy bootstrap and has matched 508 Test C and 176 Test M notebook B checks in local development. A separate Test M notebook A CPU check matched **400 independent scalar comparisons** from the archived raw scores; the integrated CLI needs its own archived-file execution check. See [Test your model](docs/RUN_YOUR_MODEL.md) for the Hugging Face runner, which has now passed one real CPU-model smoke test.

## Scientific, licensing and AI transparency

- [Development plan, acceptance and limits](docs/ROADMAP.md).
- [AI assistance disclosure](docs/AI_USAGE.md) — AI-assisted planning, coding, analysis and writing, with human oversight and documented limits.
- [References and attribution](docs/REFERENCES.md) — verified core paper citations in [BibTeX](docs/REFERENCES.bib); model revisions and remaining references require further checks.
- [Third-party terms](docs/THIRD_PARTY.md) — per-model, library and dataset licensing.
- [Root license](LICENSE) — **PolyForm Noncommercial 1.0.0**, original IndetBench code only. Commercial use needs a separate agreement; this is **source-available, not OSI open source**.

**No third-party model weights, training data, natural SQuAD passages, or proprietary probe files are distributed with this package.**

Copyright © 2026 Simona Vargiu.

## Historical research archive — source material preserved

The owner's **original Step 1 and Step 2** research material is archived in [`research_originals/`](research_originals/README.md), separate from new Hugging Face synthetic studies. It includes original summaries, protocols, written results, two Test C notebooks, **seven exact historical generator/selection/verification scripts**, and frozen synthetic datasets from Test M and Test C compressed without changing their bytes.

The provenance and original-input SHA-256 values are in [`research_originals/manifest_originals.json`](research_originals/manifest_originals.json). The M-A and M-B original frozen inputs were checked to be identical. **This is a substantial partial recovery, not yet the entire historical research archive:** complete natural SQuAD-derived rows, several original U/U2 and Step 1 files, model-output ZIPs, environment captures and weights remain excluded pending byte access or rights review. The original full ZIPs are retained separately in the owner's private ChatGPT Library.

**The 240-pair `data/smol_stat_v01_frozen.jsonl` dataset was created for a separate experiment on 13 November 2026; it is NOT original Step 1 or Step 2 data.** Repository remains private and the PR is still draft; no change to owner licensing is implied by archiving sources.

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

Replace YOUR_40_CHARACTER_COMMIT_SHA with a commit hash from the model provider's official history. Only a fabricated demonstration pair is included. See [the input schema, first-token definition and limitations](docs/RUN_YOUR_MODEL.md). The runner's unit tests use a fake tokenizer and **one real external-model CPU smoke test has now passed**. Further model-family coverage and semantic answer validation are still pending. See [the verified run and limitations](docs/SMOLLM2_EXTERNAL_SMOKE.md).

## External statistical evaluation — SmolLM2 (13 November 2026)

A preregistered 240-pair (480-inference) test on the external **SmolLM2-360M-Instruct** model found **no evidence** that its raw first-token `p(UNKNOWN)` reliably ranked underdetermined cases above determined cases: **W = 0.479** (95% bootstrap CI **0.417–0.546**), AUROC **0.501**. The exact two-sided sign-test p-value is **0.561**, independently recomputed after correcting a NumPy integer-overflow bug in the first archived report.

**Interpretation gate failed:** SmolLM2 answered only **92/240 answerable B cases correctly (38.3%)**, never generated `NO` on B or C, and abstained correctly in only 68/240 C cases. The software calculation is reproducible, but the model did not demonstrate the prerequisite task competence: the result is **not scientifically evaluable as an uncertainty-detector validation**, despite the descriptive W/AUROC values. Formatting and prompt-length effects are unresolved confounds, so this **cannot** be interpreted as epistemic detection, proof of generalization or a new model capability.

See [preregistered protocol](docs/SMOLLM2_STAT_STUDY_PREREG.md), [original model scores, statistical results and correction](docs/SMOLLM2_STAT_STUDY_RESULTS.md), and [closest 2018–2026 scientific precedents](docs/NOVELTY_AND_RELATED_WORK_2026.md). IndetBench is **not** the first or broadest benchmark on abstention and uncertainty.
