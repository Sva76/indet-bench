# Roadmap and acceptance criteria

## Phase 1: CPU foundation

- Installable Python package.
- Minimal B/C pair scoring with ties as half a win.
- Block-weighted W(C>B); paired delta-W on *common complete pairs*, block-level bootstrap, AUROC helper.
- Strict CSV validation and six unit tests.
- **Archived CPU comparisons:** 508 Test C metric checks, 176 Test M notebook B metric checks and 400 individually compared Test M notebook A scalar fields matched the original scores. The `--kind M-A` CLI still needs a full archived-file execution check; real-model smoke tests remain pending.

## Version 0.1 acceptance (not yet reached)

1. Ingest original Test M notebook A/B and Test C score artifacts, preserving IDs and exclusions.
2. Reproduce **all** frozen W and delta-W point estimates on CPU; match the original confidence intervals within a documented tolerance after matching seed, resampling and preprocessing exactly.
3. Verify SHA-256 for frozen inputs; report dropped pairs, model/score conventions, versions and source lineage.
4. Provide optional first-token p(UNKNOWN) computation under exact pinned chat templates/tokenizers; GPU runs are optional and separate from CPU reproduction.
5. Complete real-model GPU testing of the new optional Hugging Face runner, enabling outside researchers to test **their own models** rather than only import scores.
6. Keep LM-Polygraph/SIRIN/Obeso external and optional; do not bundle their weights or source.
7. Produce method cards that distinguish **measured** from **self-reported** positive controls, family-level divergences, coverage, baseline ceiling, and limits.

## Scientific cautions

Four English-language mid-size open-weight models, mostly template-generated data; baseline ceiling; strong operator/format effects. HC4 within B cannot be evaluated with zero wrong B answers; within C is confounded by family and annotation uncertainty. Natural DUE sample human review was not fully documented. Exploratory subgroup findings require independent replication.
