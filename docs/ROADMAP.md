# Roadmap and acceptance criteria

## Phase 1: CPU foundation

- Installable Python package.
- Minimal B/C pair scoring with ties as half a win.
- Block-weighted W(C>B); paired delta-W on *common complete pairs*, block-level bootstrap, AUROC helper.
- Strict CSV validation and six unit tests.
- **Not yet** a verified reproduction of archived Test M or C statistics.

## Version 0.1 acceptance (not yet reached)

1. Ingest original Test M notebook A/B and Test C score artifacts, preserving IDs and exclusions.
2. Reproduce **all** frozen W and delta-W point estimates on CPU; match the original confidence intervals within a documented tolerance after matching seed, resampling and preprocessing exactly.
3. Verify SHA-256 for frozen inputs; report dropped pairs, model/score conventions, versions and source lineage.
4. Provide optional first-token p(UNKNOWN) computation under exact pinned chat templates/tokenizers; GPU runs are optional and separate from CPU reproduction.
5. Allow outside researchers to test **their own models**, not just import scores, using documented optional runners/adapters.
6. Keep LM-Polygraph/SIRIN/Obeso external and optional; do not bundle their weights or source.
7. Produce method cards that distinguish **measured** from **self-reported** positive controls, family-level divergences, coverage, baseline ceiling, and limits.

## Scientific cautions

Four English-language mid-size open-weight models, mostly template-generated data; baseline ceiling; strong operator/format effects. HC4 within B cannot be evaluated with zero wrong B answers; within C is confounded by family and annotation uncertainty. Natural DUE sample human review was not fully documented. Exploratory subgroup findings require independent replication.
