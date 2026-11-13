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

**Important:** exact replay of the archived Test M and C pipelines is the next acceptance test. The current bootstrap uses its own deterministic Python implementation and must not yet be described as reproducing the original confidence intervals. Optional loading of new language models, including `p(UNKNOWN)` generation, is planned but **not implemented in this first change**.

## Scientific, licensing and AI transparency

- [Development plan, acceptance and limits](docs/ROADMAP.md).
- [AI assistance disclosure](docs/AI_USAGE.md) — AI-assisted planning, coding, analysis and writing, with human oversight and documented limits.
- [References and attribution](docs/REFERENCES.md) — bibliography requiring final verification before release.
- [Third-party terms](docs/THIRD_PARTY.md) — per-model, library and dataset licensing.
- [Root license](LICENSE) — **PolyForm Noncommercial 1.0.0**, original IndetBench code only. Commercial use needs a separate agreement; this is **source-available, not OSI open source**.

**No third-party model weights, training data, natural SQuAD passages, or proprietary probe files are distributed with this package.**

Copyright © 2026 Simona Vargiu.
