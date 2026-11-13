# IndetBench

**A benchmark and validation protocol for answer determinability in language models.**

> Private development repository. The scientific reports and experiments already exist; the reusable Python library is being assembled and has **not yet passed archived-results reproduction tests**.

IndetBench evaluates minimal B/C pairs: B is answer-determined by the given passage, while C is underdetermined. It compares uncertainty scores against the training-free reference `p(UNKNOWN)`.

The project is **a benchmark, not a newly validated hallucination detector**. Its results are limited to the evaluated models, tasks, and environments. A previously observed positive result for a LoRA probe in Test M did not replicate in Test C.

A proposed first implementation, with CPU metrics, unit tests, scientific references, third-party license documentation, and an AI-assistance disclosure, will be submitted as a reviewable pull request.

Copyright © 2026 Simona Vargiu. No third-party models or datasets are distributed here.
