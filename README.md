# IndetBench

**A reproducible benchmark and validation protocol for answer determinability in language models.**

> **Status: private development / pre-alpha.** The first proposed release supplies CPU-only evaluation primitives. It does **not yet** reproduce the complete Test M/C reports, provide a model runner, or certify hallucination detection.

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

**Important:** exact replay of the archived Test M and C pipelines is the next acceptance test. The current bootstrap uses its own deterministic Python implementation and must not yet be described as reproducing the original confidence intervals. An **experimental** Hugging Face runner is included, but has not yet completed its own real-model GPU smoke test. See [Test your model](docs/RUN_YOUR_MODEL.md).

## Scientific, licensing and AI transparency

- [Development plan, acceptance and limits](docs/ROADMAP.md).
- [AI assistance disclosure](docs/AI_USAGE.md) — AI-assisted planning, coding, analysis and writing, with human oversight and documented limits.
- [References and attribution](docs/REFERENCES.md) — bibliography requiring final verification before release.
- [Third-party terms](docs/THIRD_PARTY.md) — per-model, library and dataset licensing.
- [Root license](LICENSE) — **PolyForm Noncommercial 1.0.0**, original IndetBench code only. Commercial use needs a separate agreement; this is **source-available, not OSI open source**.

**No third-party model weights, training data, natural SQuAD passages, or proprietary probe files are distributed with this package.**

Copyright © 2026 Simona Vargiu.

## Reproduce frozen experiments without GPU

Install the NumPy-only optional analysis dependencies: `python -m pip install -e '.[replay]'`.

Given the original complete-results archives (not redistributed here):

```bash
python -m indetbench.replay /path/to/completo-20261113T082301Z-1-001.zip --kind C --expected-sha256 da84d9bfb81df8ef15c39524b9e507ffa13eb1e563ce18715b432a1638b5bbed --json-out testC_parity.json
python -m indetbench.replay /path/to/testM_B_risultati_completo.zip --kind M-B --expected-sha256 a78cf5a02566d22de80acf8fff6caff0fa0049c697abbbf27667b807648cea3a --json-out testM_B_parity.json
```

The replayer recomputes statistics from scores for individual pairs, rather than trusting the precomputed tables. [Exact scope and evidence](docs/REPRODUCIBILITY_STATUS.md). The Test M **notebook A** archive, Test U/U2 replication and **HC4 annotation reliability** remain separate unfinished checks.

## Test a new language model (experimental)

The first Hugging Face runner is now available as an **opt-in** feature. It loads an external causal LM under that model's own terms and scores user-authored B/C prompts without modifying the source model:

```bash
python -m pip install -e '.[hf]'
python -m indetbench.hf_runner --model-id Qwen/Qwen3-8B --model-key qwen --input examples/hf_pairs.jsonl --output my_scores.csv
python -m indetbench --scores my_scores.csv
```

Only a fabricated demonstration pair is included. See [the input schema, first-token definition and limitations](docs/RUN_YOUR_MODEL.md). The runner's integration tests currently use a fake tokenizer; **a real GPU smoke test is still pending**.
