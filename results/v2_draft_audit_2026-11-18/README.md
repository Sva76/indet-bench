# v2 draft: shortcut audits (18 November 2026)

Audits of the **v2 generator text only**. No model was run. Reading of the results: [V2_GENERATOR_SPEC.md §5](../../docs/V2_GENERATOR_SPEC.md#5-shortcut-controls-binding-before-any-model-run).

| File | Seed | `--flip-location` | Role |
|---|---|---|---|
| `audit_dev_seed20261118_any.json` | 20261118 | any (default) | development: the seed used while correcting the generator |
| `audit_dev_seed20261118_intermediate.json` | 20261118 | intermediate | development |
| `audit_confirm_seed20261119_any.json` | 20261119 | any (default) | confirmation |
| `audit_confirm_seed20261119_intermediate.json` | 20261119 | intermediate | confirmation |

## What "confirmation" means here

- The prompt-generating code was committed in `b605ac2` before seed 20261119 was generated for the first time.
- After CodeRabbit's review of PR #25, story ids were made dataset-specific, metadata fields were added and the audit gained the single-rule readers and a location-scoped feasibility table. The **prompts and gold labels of seed 20261119 did not change**: they were compared row by row, both settings, B/C and D files.
- The audits above were then **re-run on both seeds with the revised audit code**. The single-rule readers were therefore first computed on the confirmation seed after the generator had been fixed, but the audit code itself was revised after the first confirmation run. Neither seed is the final data set.

## How to reproduce

```bash
python -m pip install -e .
indet-bench-v2 generate --seed 20261119 --flip-location any --output pairs.jsonl --controls controls.jsonl
indet-bench-v2 audit --input pairs.jsonl > audit.json
```

The generated files are not committed: they are rebuilt from the seed. Their SHA-256 (Python 3.13). `test_confirmation_files_checksum` in `tests/test_gen_v2.py` rebuilds the four seed-20261119 files and checks these values in the `cpu-tests` job of `.github/workflows/ci.yml` (Python 3.10 and 3.12; pushes to `main` and every pull request). The seed-20261118 files are not checked in CI.

| Seed | Flip location | `pairs.jsonl` | `controls.jsonl` |
|---|---|---|---|
| 20261118 | any | `9113e0b8f6facaef35c8d70aec08bad8f45f91e89cf1a957acef57ce25999149` | `96722e7668ddcb01b481b72acbc743663eaa08cf2b5710039f5107bad5e62712` |
| 20261118 | intermediate | `32be11b548fcd39fff753d565cf29552039f69aafd566b75a1d1e6792a4175a3` | `a55078f8517c0a8fe2ca84117a6ef5ea105ea14e51223d2c2ce02044389d77b7` |
| 20261119 | any | `bee7a517939e11efefbfac303cd1f0f92573b4cc61df0d726d7c641655d055d0` | `6aaf431cbbd7fc0069d9312e82cb855a89af1915454209a2170c06df3f94f2e8` |
| 20261119 | intermediate | `2e08ffb97a5a9175abd1bd4944504643fb1efa0d6470a6e2994fd5689ad5ae6c` | `36aa53122606f4ed60d92e77952e5cd5ba3794df47ed7dc9cf12d784ae65e5e2` |

Audit files (`sha256sum *.json`):

```
b52ffedbd45eafbd233fcbf366d1489ead75f866ee324997421d71e10d84fbf8  audit_confirm_seed20261119_any.json
c9106e51106dd636eeeb714a845a4430b2fc3a182e23a702a869929782cb0bcb  audit_confirm_seed20261119_intermediate.json
c70c5269c18042d343734300837366f6b673434c78b85d17d4228c0124ceb16c  audit_dev_seed20261118_any.json
1778be43bcd37cd8f07b6a44e85dad9fdc67d3fe4d661846419e8486a030e80e  audit_dev_seed20261118_intermediate.json
```

Original IndetBench material, © 2026 Simona Vargiu, PolyForm Noncommercial License 1.0.0.
